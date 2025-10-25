import React, { useState, useEffect } from 'react';
import './ContentDisplay.css';
import { generateImage, generateVideo, getAudio } from '../services/api';
import wsService from '../services/websocket';

function ContentDisplay({ taskId, paragraphs, onProgressUpdate, audioCacheMap }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState({});
  const [audioPlaying, setAudioPlaying] = useState(null);
  const [currentAudio, setCurrentAudio] = useState(null);
  const [zoomedImage, setZoomedImage] = useState(null);
  const [speechPlaying, setSpeechPlaying] = useState(null);
  const [currentImageIndex, setCurrentImageIndex] = useState({});
  const [useWebSocket, setUseWebSocket] = useState(true);
  const [videoCacheMap, setVideoCacheMap] = useState({});

  useEffect(() => {
    if (paragraphs && paragraphs.length > 0) {
      const initialItems = paragraphs.map((text, index) => ({
        id: index + 1,
        text,
        images: [],
        video: null,
        audioUrl: null,
        loadingImage: false,
        loadingVideo: false,
        loadingAudio: false,
        progress: 0
      }));
      setItems(initialItems);
      
      if (taskId === 'test-mode') {
        processTestMode(initialItems);
      } else {
        processItemsSequentially(initialItems);
      }
    }
  }, [paragraphs, taskId]);

  useEffect(() => {
    const handleImageResult = (payload) => {
      console.log('=== ContentDisplay收到图片结果 ===');
      console.log('完整payload:', JSON.stringify(payload, null, 2));
      console.log('当前items数组长度:', items.length);
      
      const { data, paragraph_number } = payload;
      
      if (!data || !data.data || !Array.isArray(data.data)) {
        console.error('❌ 图片数据格式不正确:', {
          hasData: !!data,
          hasDataData: !!(data && data.data),
          isArray: !!(data && data.data && Array.isArray(data.data)),
          payload
        });
        return;
      }
      
      try {
        console.log(`✅ 开始处理 ${data.data.length} 张图片`);
        const imageUrls = data.data.map((img, idx) => {
          const base64Data = img.b64_json;
          const url = `data:image/${data.output_format || 'png'};base64,${base64Data}`;
          console.log(`  图片 ${idx + 1}: base64长度=${base64Data?.length || 0}, URL长度=${url.length}`);
          return url;
        });
        
        console.log(`准备更新段落 ${paragraph_number}, 索引=${paragraph_number - 1}`);
        setItems(prev => {
          const updated = [...prev];
          const index = paragraph_number - 1;
          console.log(`  当前items长度=${updated.length}, 目标索引=${index}`);
          
          if (index >= 0 && index < updated.length) {
            updated[index] = {
              ...updated[index],
              images: imageUrls,
              loadingImage: false,
              progress: 100
            };
            console.log(`✅ 段落 ${paragraph_number} 图片已更新，图片数量=${imageUrls.length}`);
          } else {
            console.error(`❌ 索引越界: index=${index}, items.length=${updated.length}`);
          }
          return updated;
        });
        
        setTimeout(() => {
          setItems(prev => {
            const updated = [...prev];
            const index = paragraph_number - 1;
            if (index >= 0 && index < updated.length) {
              updated[index] = { ...updated[index], progress: 0 };
            }
            return updated;
          });
        }, 1000);
      } catch (error) {
        console.error('❌ 处理图片数据失败:', error);
        console.error('错误堆栈:', error.stack);
      }
    };
    
    if (useWebSocket && wsService.isConnected()) {
      console.log('✅ 注册image_result事件监听器');
      wsService.on('image_result', handleImageResult);
      
      return () => {
        console.log('🔄 移除image_result事件监听器');
        wsService.off('image_result', handleImageResult);
      };
    } else {
      console.log('⚠️  WebSocket未连接，跳过事件监听器注册');
    }
  }, [useWebSocket, items.length]);

  const processTestMode = (itemsList) => {
    const updatedItems = itemsList.map((item, index) => ({
      ...item,
      images: ['/test.jpeg', '/test.jpeg', '/test.jpeg'],
      loadingImage: false,
      progress: 100
    }));
    setItems(updatedItems);
  };

  const processItemsSequentially = async (itemsList) => {
    if (useWebSocket && wsService.isConnected()) {
      setItems(prev => prev.map(item => ({
        ...item,
        loadingImage: true,
        progress: 10
      })));
    } else {
      for (let i = 0; i < itemsList.length; i++) {
        await generateImageForItem(i);
      }
    }
  };

  const generateImageForItem = async (index) => {
    setItems(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], loadingImage: true, progress: 0 };
      return updated;
    });

    try {
      const progressInterval = setInterval(() => {
        setItems(prev => {
          const updated = [...prev];
          if (updated[index] && updated[index].progress < 90) {
            updated[index] = { ...updated[index], progress: updated[index].progress + 10 };
          }
          return updated;
        });
      }, 500);

      const response = await generateImage(taskId, items[index].text, index + 1);
      
      clearInterval(progressInterval);

      setItems(prev => {
        const updated = [...prev];
        updated[index] = {
          ...updated[index],
          images: [response.image_url, response.image_url, response.image_url],
          audioUrl: response.audio_url,
          loadingImage: false,
          progress: 100
        };
        return updated;
      });

      setTimeout(() => {
        setItems(prev => {
          const updated = [...prev];
          updated[index] = { ...updated[index], progress: 0 };
          return updated;
        });
      }, 1000);

    } catch (error) {
      console.error(`Error generating image for item ${index + 1}:`, error);
      setItems(prev => {
        const updated = [...prev];
        updated[index] = { ...updated[index], loadingImage: false, progress: 0 };
        return updated;
      });
    }
  };

  const handlePlayAudio = async (index) => {
    const item = items[index];
    const paragraphNumber = index + 1;
    
    if (audioPlaying === index) {
      if (currentAudio) {
        currentAudio.pause();
        setCurrentAudio(null);
      }
      setAudioPlaying(null);
      return;
    }

    if (currentAudio) {
      currentAudio.pause();
      setCurrentAudio(null);
    }

    if (audioCacheMap && audioCacheMap[paragraphNumber]) {
      console.log(`使用缓存的音频: 段落 ${paragraphNumber}`);
      playAudio(audioCacheMap[paragraphNumber], index);
      return;
    }

    if (item.audioUrl) {
      playAudio(item.audioUrl, index);
    } else {
      setItems(prev => {
        const updated = [...prev];
        updated[index] = { ...updated[index], loadingAudio: true };
        return updated;
      });

      try {
        const response = await getAudio(taskId, item.text, paragraphNumber);
        
        setItems(prev => {
          const updated = [...prev];
          updated[index] = { ...updated[index], audioUrl: response.audio_url, loadingAudio: false };
          return updated;
        });

        playAudio(response.audio_url, index);
      } catch (error) {
        console.error(`Error getting audio for item ${paragraphNumber}:`, error);
        setItems(prev => {
          const updated = [...prev];
          updated[index] = { ...updated[index], loadingAudio: false };
          return updated;
        });
      }
    }
  };

  const playAudio = (url, index) => {
    const audio = new Audio(url);
    audio.play();
    setAudioPlaying(index);
    setCurrentAudio(audio);
    
    audio.onended = () => {
      setAudioPlaying(null);
      setCurrentAudio(null);
    };
  };

  const handleImageClick = (imageUrl) => {
    setZoomedImage(imageUrl);
  };

  const handleCloseZoom = () => {
    setZoomedImage(null);
  };

  const handlePlaySpeech = (text, index) => {
    if (speechPlaying === index) {
      window.speechSynthesis.cancel();
      setSpeechPlaying(null);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'zh-CN';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    
    utterance.onend = () => {
      setSpeechPlaying(null);
    };
    
    utterance.onerror = () => {
      setSpeechPlaying(null);
    };
    
    setSpeechPlaying(index);
    window.speechSynthesis.speak(utterance);
  };

  const handlePrevImage = (itemIndex) => {
    const item = items[itemIndex];
    if (!item.images || item.images.length === 0) return;
    
    setCurrentImageIndex(prev => {
      const current = prev[itemIndex] || 0;
      const newIndex = current === 0 ? item.images.length - 1 : current - 1;
      return { ...prev, [itemIndex]: newIndex };
    });
  };

  const handleNextImage = (itemIndex) => {
    const item = items[itemIndex];
    if (!item.images || item.images.length === 0) return;
    
    setCurrentImageIndex(prev => {
      const current = prev[itemIndex] || 0;
      const newIndex = (current + 1) % item.images.length;
      return { ...prev, [itemIndex]: newIndex };
    });
  };

  useEffect(() => {
    const intervals = {};
    
    items.forEach((item, index) => {
      if (item.images && item.images.length > 1) {
        intervals[index] = setInterval(() => {
          handleNextImage(index);
        }, 3000);
      }
    });

    return () => {
      Object.values(intervals).forEach(interval => clearInterval(interval));
    };
  }, [items]);

  const handleGenerateVideo = async (index) => {
    const item = items[index];
    const paragraphNumber = index + 1;

    if (videoCacheMap[paragraphNumber]) {
      console.log(`使用缓存的视频: 段落 ${paragraphNumber}`);
      setItems(prev => {
        const updated = [...prev];
        updated[index] = {
          ...updated[index],
          video: videoCacheMap[paragraphNumber]
        };
        return updated;
      });
      return;
    }

    setItems(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], loadingVideo: true, progress: 0 };
      return updated;
    });

    try {
      const progressInterval = setInterval(() => {
        setItems(prev => {
          const updated = [...prev];
          if (updated[index] && updated[index].progress < 90) {
            updated[index] = { ...updated[index], progress: updated[index].progress + 5 };
          }
          return updated;
        });
      }, 1000);

      const currentImage = item.images && item.images.length > 0 ? item.images[0] : null;
      
      if (!currentImage) {
        console.error('没有可用的图片用于视频生成');
        setItems(prev => {
          const updated = [...prev];
          updated[index] = { ...updated[index], loadingVideo: false, progress: 0 };
          return updated;
        });
        return;
      }
      
      let imageBase64 = '';
      if (currentImage.startsWith('data:image/')) {
        imageBase64 = currentImage.split(',')[1];
      } else {
        imageBase64 = currentImage;
      }
      
      if (useWebSocket && wsService.isConnected()) {
        wsService.sendVideoRequest(taskId, item.text, paragraphNumber, imageBase64);
        
        const handleVideoResult = (data) => {
          if (data.paragraph_number === paragraphNumber) {
            clearInterval(progressInterval);
            
            setVideoCacheMap(prev => ({
              ...prev,
              [paragraphNumber]: data.video_url
            }));
            
            setItems(prev => {
              const updated = [...prev];
              updated[index] = {
                ...updated[index],
                video: data.video_url,
                loadingVideo: false,
                progress: 100
              };
              return updated;
            });

            setTimeout(() => {
              setItems(prev => {
                const updated = [...prev];
                updated[index] = { ...updated[index], progress: 0 };
                return updated;
              });
            }, 1000);
            
            wsService.off('video_result', handleVideoResult);
          }
        };
        
        wsService.on('video_result', handleVideoResult);
      } else {
        const response = await generateVideo(taskId, item.text, paragraphNumber, currentImage);
        
        clearInterval(progressInterval);

        setVideoCacheMap(prev => ({
          ...prev,
          [paragraphNumber]: response.video_url
        }));

        setItems(prev => {
          const updated = [...prev];
          updated[index] = {
            ...updated[index],
            video: response.video_url,
            loadingVideo: false,
            progress: 100
          };
          return updated;
        });

        setTimeout(() => {
          setItems(prev => {
            const updated = [...prev];
            updated[index] = { ...updated[index], progress: 0 };
            return updated;
          });
        }, 1000);
      }

    } catch (error) {
      console.error(`Error generating video for item ${paragraphNumber}:`, error);
      setItems(prev => {
        const updated = [...prev];
        updated[index] = { ...updated[index], loadingVideo: false, progress: 0 };
        return updated;
      });
    }
  };

  const completedItems = items.filter(item => item.images && item.images.length > 0).length;
  const totalItems = items.length;
  const overallProgress = totalItems > 0 ? Math.round((completedItems / totalItems) * 100) : 0;
  
  useEffect(() => {
    if (onProgressUpdate) {
      onProgressUpdate({ completed: completedItems, total: totalItems });
    }
  }, [completedItems, totalItems, onProgressUpdate]);

  if (!paragraphs || paragraphs.length === 0) {
    return (
      <div className="content-display">
        <div className="sections-container">
          <div className="section image-section">
            <h2>📷 段落内容与图片</h2>
            <div className="empty-state">
              <p>等待输入内容后开始生成...</p>
            </div>
          </div>

          <div className="section video-section">
            <h2>🎥 生成视频</h2>
            <div className="empty-state">
              <p>等待输入内容后开始生成...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="content-display">
      <div className="sections-container">
        <div className="section image-section">
          <h2>📷 段落内容与图片</h2>
          <div className="items-grid">
            {items.map((item, index) => (
              <div key={item.id} className="image-item">
                <div className="item-header">
                  <div className="item-title">段落 {item.id}</div>
                  <div className="item-number">{item.id}</div>
                </div>
                <div className="paragraph-text">{item.text}</div>
                <div className="item-content">
                  {item.loadingImage ? (
                    <div className="loading-container">
                      <div className="loading-spinner"></div>
                      <div className="progress-bar">
                        <div className="progress-fill" style={{ width: `${item.progress}%` }}></div>
                      </div>
                      <p>生成中... {item.progress}%</p>
                    </div>
                  ) : item.images && item.images.length > 0 ? (
                    <div className="image-carousel">
                      {item.images.length > 1 && (
                        <button 
                          className="carousel-btn carousel-btn-prev" 
                          onClick={() => handlePrevImage(index)}
                          aria-label="上一张"
                        >
                          ‹
                        </button>
                      )}
                      <div className="carousel-images">
                        {item.images.map((imgUrl, imgIndex) => (
                          <img 
                            key={imgIndex}
                            src={imgUrl} 
                            alt={`Scene ${item.id}-${imgIndex + 1}`} 
                            onClick={() => handleImageClick(imgUrl)}
                            style={{ 
                              cursor: 'pointer',
                              display: (currentImageIndex[index] || 0) === imgIndex ? 'block' : 'none'
                            }}
                            title="点击放大图片"
                            className="carousel-image"
                          />
                        ))}
                      </div>
                      {item.images.length > 1 && (
                        <button 
                          className="carousel-btn carousel-btn-next" 
                          onClick={() => handleNextImage(index)}
                          aria-label="下一张"
                        >
                          ›
                        </button>
                      )}
                      {item.images.length > 1 && (
                        <div className="carousel-indicators">
                          {item.images.map((_, imgIndex) => (
                            <span 
                              key={imgIndex}
                              className={`indicator ${(currentImageIndex[index] || 0) === imgIndex ? 'active' : ''}`}
                              onClick={() => setCurrentImageIndex(prev => ({ ...prev, [index]: imgIndex }))}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="placeholder">等待生成...</div>
                  )}
                </div>
                <div className="image-actions">
                  <button
                    className={`action-button ${speechPlaying === index ? 'playing' : ''}`}
                    onClick={() => handlePlaySpeech(item.text, index)}
                  >
                    {speechPlaying === index ? '⏸️ 停止浏览器本地朗读' : '🔊 浏览器本地朗读'}
                  </button>
                  <button
                    className={`action-button ${audioPlaying === index ? 'playing' : ''}`}
                    onClick={() => handlePlayAudio(index)}
                    disabled={item.loadingAudio}
                  >
                    {item.loadingAudio ? '⏳' : audioPlaying === index ? '⏸️' : '🔊'} 
                    {item.loadingAudio ? ' 加载中' : audioPlaying === index ? ' 暂停播放' : ' 播放语音'}
                  </button>
                  <button
                    className="action-button"
                    onClick={() => handleGenerateVideo(index)}
                    disabled={item.loadingVideo}
                  >
                    {item.loadingVideo ? '⏳ 生成中...' : '🎬 生成视频'}
                  </button>
                </div>
                {item.loadingVideo && (
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${item.progress}%` }}></div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="section video-section">
          <h2>🎥 生成视频</h2>
          <div className="items-grid">
            {items.map((item) => (
              <div key={item.id} className="video-item">
                <div className="item-header">
                  <div className="item-title">段落 {item.id} 视频</div>
                  <div className="item-number">{item.id}</div>
                </div>
                <div className="paragraph-text">{item.text}</div>
                <div className="item-content">
                  {item.video ? (
                    <video controls>
                      <source src={item.video} type="video/mp4" />
                      您的浏览器不支持视频播放
                    </video>
                  ) : (
                    <div className="placeholder">
                      {item.loadingVideo ? '生成中...' : '生成的视频将在这里按段落顺序显示'}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      {zoomedImage && (
        <div className="image-modal" onClick={handleCloseZoom}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={handleCloseZoom}>✕</button>
            <img src={zoomedImage} alt="Zoomed" />
          </div>
        </div>
      )}
    </div>
  );
}

export default ContentDisplay;
