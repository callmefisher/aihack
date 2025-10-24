import React, { useState, useEffect } from 'react';
import './ContentDisplay.css';
import { generateImage, generateVideo, getAudio } from '../services/api';
import wsService from '../services/websocket';

function ContentDisplay({ taskId, paragraphs, onProgressUpdate, audioCacheMap }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState({});
  const [audioPlaying, setAudioPlaying] = useState(null);
  const [zoomedImage, setZoomedImage] = useState(null);
  const [speechPlaying, setSpeechPlaying] = useState(null);
  const [currentImageIndex, setCurrentImageIndex] = useState({});
  const [useWebSocket, setUseWebSocket] = useState(true);

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
    const handleImageResult = (data) => {
      console.log('ContentDisplay收到图片结果:', data);
      
      if (data.data && data.data.data && Array.isArray(data.data.data)) {
        try {
          const imageUrls = data.data.data.map((item, index) => {
            const base64Image = item.b64_json;
            const binaryString = atob(base64Image);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
              bytes[i] = binaryString.charCodeAt(i);
            }
            
            const blob = new Blob([bytes], { type: 'image/png' });
            const imageUrl = URL.createObjectURL(blob);
            
            console.log(`图片 ${index + 1} URL生成:`, imageUrl);
            return imageUrl;
          });
          
          const paragraphNumber = data.paragraph_number;
          if (paragraphNumber !== undefined) {
            const itemIndex = paragraphNumber - 1;
            
            setItems(prev => {
              const updated = [...prev];
              if (updated[itemIndex]) {
                updated[itemIndex] = {
                  ...updated[itemIndex],
                  images: imageUrls,
                  loadingImage: false,
                  progress: 100
                };
              }
              return updated;
            });
            
            console.log(`段落 ${paragraphNumber} 的图片已更新到UI`);
          }
        } catch (error) {
          console.error('解码图片失败:', error);
        }
      }
    };
    
    if (useWebSocket && wsService.isConnected()) {
      wsService.on('image_result', handleImageResult);
      
      return () => {
        wsService.off('image_result', handleImageResult);
      };
    }
  }, [useWebSocket]);

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
    for (let i = 0; i < itemsList.length; i++) {
      await generateImageForItem(i);
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
      setAudioPlaying(null);
      return;
    }

    // 先检查缓存
    if (audioCacheMap && audioCacheMap[paragraphNumber]) {
      console.log(`使用缓存的音频: 段落 ${paragraphNumber}`);
      playAudio(audioCacheMap[paragraphNumber], index);
      return;
    }

    // 如果有audioUrl，使用它
    if (item.audioUrl) {
      playAudio(item.audioUrl, index);
    } else {
      // 否则请求音频（仅HTTP模式）
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
    
    audio.onended = () => {
      setAudioPlaying(null);
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
      
      // 如果启用WebSocket且已连接，使用WebSocket
      if (useWebSocket && wsService.isConnected()) {
        // 使用WebSocket生成视频
        wsService.sendVideoRequest(taskId, item.text, paragraphNumber, currentImage);
        
        // 注册一次性的视频结果监听器
        const handleVideoResult = (data) => {
          if (data.paragraph_number === paragraphNumber) {
            clearInterval(progressInterval);
            
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
            
            // 移除监听器
            wsService.off('video_result', handleVideoResult);
          }
        };
        
        wsService.on('video_result', handleVideoResult);
      } else {
        // 使用HTTP API
        const response = await generateVideo(taskId, item.text, paragraphNumber, currentImage);
        
        clearInterval(progressInterval);

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
                    {item.loadingAudio ? ' 加载中' : audioPlaying === index ? ' 暂停' : ' 播放声音'}
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
