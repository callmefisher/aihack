import React, { useState, useEffect, useCallback } from 'react';
import './ContentDisplay.css';
import { generateVideo } from '../services/api';
import wsService from '../services/websocket';

function ContentDisplay({ taskId, paragraphs, onProgressUpdate, audioCacheMap, imageCacheMap, autoPlayAudio, audioQueueMap, imageQueueMap }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState({});
  const [audioPlaying, setAudioPlaying] = useState(null);
  const [currentAudio, setCurrentAudio] = useState(null);
  const [currentPlayingParagraph, setCurrentPlayingParagraph] = useState(null);
  const [zoomedImage, setZoomedImage] = useState(null);
  const [speechPlaying, setSpeechPlaying] = useState(null);
  const [currentImageIndex, setCurrentImageIndex] = useState({});
  const [useWebSocket, setUseWebSocket] = useState(true);
  const [videoCacheMap, setVideoCacheMap] = useState({});
  const [audioQueueIndex, setAudioQueueIndex] = useState({});
  const [imageQueueIndex, setImageQueueIndex] = useState({});
  const processedAutoPlayRef = React.useRef(new Set());
  const [nextSequenceToPlay, setNextSequenceToPlay] = useState({});
  const [isParagraphBlocked, setIsParagraphBlocked] = useState(false);

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

  const handleImageResult = useCallback((payload) => {
    console.log('=== ContentDisplay收到图片结果 ===');
    console.log('完整payload:', JSON.stringify(payload, null, 2));
    
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
        console.log(`  段落 ${paragraph_number} 更新前的images:`, updated[index]?.images);
        
        if (index >= 0 && index < updated.length) {
          updated[index] = {
            ...updated[index],
            images: [...imageUrls],
            loadingImage: false,
            progress: 100
          };
          console.log(`✅ 段落 ${paragraph_number} 图片已更新，图片数量=${imageUrls.length}`);
          console.log(`  更新后的images:`, updated[index].images);
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
  }, []);

  useEffect(() => {
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
  }, [useWebSocket, handleImageResult]);

  useEffect(() => {
    if (imageCacheMap && Object.keys(imageCacheMap).length > 0) {
      console.log('=== 应用缓存的图片 ===');
      console.log('imageCacheMap:', imageCacheMap);
      
      setItems(prev => {
        const updated = [...prev];
        Object.entries(imageCacheMap).forEach(([paragraphNumber, imageUrls]) => {
          const index = parseInt(paragraphNumber) - 1;
          if (index >= 0 && index < updated.length) {
            console.log(`应用缓存图片到段落 ${paragraphNumber}，图片数量=${imageUrls.length}`);
            updated[index] = {
              ...updated[index],
              images: imageUrls,
              loadingImage: false,
              progress: 0
            };
          }
        });
        return updated;
      });
    }
  }, [imageCacheMap]);

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
      setCurrentPlayingParagraph(null);
      
      setNextSequenceToPlay(prev => ({
        ...prev,
        [paragraphNumber]: 0
      }));
      
      if (paragraphNumber === 1) {
        setIsParagraphBlocked(false);
      }
      
      console.log(`暂停播放段落 ${paragraphNumber}，已清理序列号状态，下次播放将从序列号 0 开始`);
      return;
    }

    if (paragraphNumber !== 1 && isParagraphBlocked) {
      console.log(`段落 ${paragraphNumber} 被阻止播放，因为段落 1 尚未完成`);
      alert('请先完成段落 1 的播放');
      return;
    }

    if (currentAudio) {
      currentAudio.pause();
      setCurrentAudio(null);
    }

    if (paragraphNumber === 1) {
      setIsParagraphBlocked(true);
    }

    setNextSequenceToPlay(prev => ({
      ...prev,
      [paragraphNumber]: 0
    }));

    if (audioQueueMap && audioQueueMap[paragraphNumber] && audioQueueMap[paragraphNumber].length > 0) {
      console.log(`播放整个段落的音频队列: 段落 ${paragraphNumber}, 队列长度 ${audioQueueMap[paragraphNumber].length}`);
      const queue = audioQueueMap[paragraphNumber];
      playAudioQueueSequential(queue, index, paragraphNumber);
      return;
    }

    if (audioCacheMap && audioCacheMap[paragraphNumber]) {
      console.log(`使用缓存的音频: 段落 ${paragraphNumber}`);
      playAudio(audioCacheMap[paragraphNumber], index, paragraphNumber);
      return;
    }

    if (item.audioUrl) {
      playAudio(item.audioUrl, index, paragraphNumber);
    }
  };

  const playAudio = (url, index, paragraphNumber) => {
    const audio = new Audio(url);
    audio.play();
    setAudioPlaying(index);
    setCurrentAudio(audio);
    setCurrentPlayingParagraph(paragraphNumber);
    
    audio.onended = () => {
      setAudioPlaying(null);
      setCurrentAudio(null);
      setCurrentPlayingParagraph(null);
    };
  };

  const playAudioQueueSequential = (queue, itemIndex, paragraphNumber) => {
    const nextSeq = nextSequenceToPlay[paragraphNumber] || 0;
    const nextItem = queue.find(item => item.sequenceNumber === nextSeq);
    
    if (!nextItem) {
      console.log(`等待序列号 ${nextSeq} 到达，段落 ${paragraphNumber}`);
      return;
    }
    
    console.log(`播放队列序列: 段落 ${paragraphNumber}, 序列号 ${nextItem.sequenceNumber}`);
    
    const audio = new Audio(nextItem.audioUrl);
    audio.play();
    setAudioPlaying(itemIndex);
    setCurrentAudio(audio);
    setCurrentPlayingParagraph(paragraphNumber);
    
    audio.onended = () => {
      console.log(`序列播放完成: 段落 ${paragraphNumber}, 序列号 ${nextItem.sequenceNumber}`);
      
      const nextSeqNum = nextSeq + 1;
      setNextSequenceToPlay(prev => ({
        ...prev,
        [paragraphNumber]: nextSeqNum
      }));
      
      const hasMoreInQueue = queue.some(item => item.sequenceNumber === nextSeqNum);
      
      if (hasMoreInQueue) {
        playAudioQueueSequential(queue, itemIndex, paragraphNumber);
      } else {
        console.log(`段落 ${paragraphNumber} 所有已接收序列播放完成，等待后续序列...`);
        setAudioPlaying(null);
        setCurrentAudio(null);
        setCurrentPlayingParagraph(null);
        
        if (paragraphNumber === 1) {
          setIsParagraphBlocked(false);
        }
      }
    };
    
    audio.onerror = (error) => {
      console.error(`播放错误: 段落 ${paragraphNumber}, 序列号 ${nextItem.sequenceNumber}`, error);
      const nextSeqNum = nextSeq + 1;
      setNextSequenceToPlay(prev => ({
        ...prev,
        [paragraphNumber]: nextSeqNum
      }));
      playAudioQueueSequential(queue, itemIndex, paragraphNumber);
    };
  };

  const playAudioQueue = (queue, queueIndex, itemIndex, paragraphNumber) => {
    if (queueIndex >= queue.length) {
      console.log(`队列播放完成: 段落 ${paragraphNumber}`);
      setAudioPlaying(null);
      setCurrentAudio(null);
      setCurrentPlayingParagraph(null);
      return;
    }

    const currentItem = queue[queueIndex];
    console.log(`播放队列序列: 段落 ${paragraphNumber}, 序列号 ${currentItem.sequenceNumber}, 队列位置 ${queueIndex + 1}/${queue.length}`);
    
    const audio = new Audio(currentItem.audioUrl);
    audio.play();
    setAudioPlaying(itemIndex);
    setCurrentAudio(audio);
    setCurrentPlayingParagraph(paragraphNumber);
    
    audio.onended = () => {
      console.log(`序列播放完成: 段落 ${paragraphNumber}, 序列号 ${currentItem.sequenceNumber}`);
      playAudioQueue(queue, queueIndex + 1, itemIndex, paragraphNumber);
    };
    
    audio.onerror = (error) => {
      console.error(`播放错误: 段落 ${paragraphNumber}, 序列号 ${currentItem.sequenceNumber}`, error);
      playAudioQueue(queue, queueIndex + 1, itemIndex, paragraphNumber);
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

    console.log(`=== 开始生成视频 ===`);
    console.log(`段落编号: ${paragraphNumber}`);
    console.log(`taskId: ${taskId}`);
    console.log(`WebSocket连接状态: ${wsService.isConnected()}`);
    console.log(`useWebSocket: ${useWebSocket}`);

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

    const currentImage = item.images && item.images.length > 0 ? item.images[0] : null;
    
    if (!currentImage) {
      console.error(`❌ 段落 ${paragraphNumber} 没有可用的图片，无法生成视频`);
      alert(`请先等待段落 ${paragraphNumber} 的图片生成完成后再生成视频`);
      return;
    }

    setItems(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], loadingVideo: true, progress: 0 };
      return updated;
    });

    try {
      let currentProgress = 0;
      const progressInterval = setInterval(() => {
        setItems(prev => {
          const updated = [...prev];
          if (updated[index] && currentProgress < 90) {
            const increment = Math.random() * 2 + 0.5;
            currentProgress = Math.min(90, currentProgress + increment);
            updated[index] = { ...updated[index], progress: Math.floor(currentProgress) };
          }
          return updated;
        });
      }, 300);

      let imageBase64 = '';
      if (currentImage.startsWith('data:image/')) {
        imageBase64 = currentImage.split(',')[1];
      } else {
        imageBase64 = currentImage;
      }
      
      console.log(`图片Base64长度: ${imageBase64.length}`);
      console.log(`文本内容: ${item.text.substring(0, 50)}...`);
      
      if (useWebSocket && wsService.isConnected()) {
        console.log(`✅ 使用WebSocket发送视频生成请求`);
        try {
          wsService.sendVideoRequest(taskId, item.text, paragraphNumber, imageBase64);
          console.log(`✅ WebSocket视频请求已发送`);
        } catch (error) {
          console.error(`❌ WebSocket发送失败:`, error);
          clearInterval(progressInterval);
          setItems(prev => {
            const updated = [...prev];
            updated[index] = { ...updated[index], loadingVideo: false, progress: 0 };
            return updated;
          });
          alert(`视频生成请求发送失败: ${error.message}`);
          return;
        }
        
        const handleVideoResult = (data) => {
          console.log(`收到视频结果:`, data);
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
        
        const handleVideoError = (data) => {
          console.error(`收到视频生成错误:`, data);
          if (data.paragraph_number === paragraphNumber) {
            clearInterval(progressInterval);
            setItems(prev => {
              const updated = [...prev];
              updated[index] = { ...updated[index], loadingVideo: false, progress: 0 };
              return updated;
            });
            alert(`视频生成失败: ${data.message}`);
            wsService.off('error', handleVideoError);
            wsService.off('video_result', handleVideoResult);
          }
        };
        
        wsService.on('video_result', handleVideoResult);
        wsService.on('error', handleVideoError);
      } else {
        console.error(`❌ WebSocket未连接，无法生成视频`);
        clearInterval(progressInterval);
        setItems(prev => {
          const updated = [...prev];
          updated[index] = { ...updated[index], loadingVideo: false, progress: 0 };
          return updated;
        });
        alert('请确保WebSocket已连接后再生成视频');
        return;
      }

    } catch (error) {
      console.error(`❌ 生成视频错误 (段落 ${paragraphNumber}):`, error);
      setItems(prev => {
        const updated = [...prev];
        updated[index] = { ...updated[index], loadingVideo: false, progress: 0 };
        return updated;
      });
      alert(`视频生成失败: ${error.message}`);
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

  useEffect(() => {
    if (autoPlayAudio && autoPlayAudio.paragraphNumber && autoPlayAudio.audioUrl) {
      const paragraphNumber = autoPlayAudio.paragraphNumber;
      const index = paragraphNumber - 1;
      const sequenceNumber = autoPlayAudio.sequenceNumber !== undefined ? autoPlayAudio.sequenceNumber : 0;
      const audioKey = `${paragraphNumber}-${sequenceNumber}-${autoPlayAudio.timestamp}`;
      
      if (processedAutoPlayRef.current.has(audioKey)) {
        return;
      }
      
      processedAutoPlayRef.current.add(audioKey);
      console.log(`收到自动播放音频请求: 段落 ${paragraphNumber}, 序列号 ${sequenceNumber}, 索引=${index}`);
      
      if (paragraphNumber !== 1 && isParagraphBlocked) {
        console.log(`⚠️  段落 ${paragraphNumber} 被阻止自动播放，因为段落 1 尚未完成`);
        return;
      }
      
      const expectedSequence = nextSequenceToPlay[paragraphNumber] || 0;
      if (sequenceNumber !== expectedSequence) {
        console.log(`⚠️  收到序列号 ${sequenceNumber}，但期望序列号 ${expectedSequence}。等待前序音频`);
        return;
      }
      
      if (currentAudio && !currentAudio.paused) {
        if (currentPlayingParagraph !== null && currentPlayingParagraph !== paragraphNumber) {
          console.log(`⚠️  当前正在播放段落 ${currentPlayingParagraph}，不打断。新段落 ${paragraphNumber} 的音频将等待`);
          return;
        }
        console.log(`⚠️  当前正在播放段落 ${paragraphNumber} 的音频，新序列 ${sequenceNumber} 加入队列等待`);
        return;
      }
      
      if (paragraphNumber === 1) {
        setIsParagraphBlocked(true);
      }
      
      const audio = new Audio(autoPlayAudio.audioUrl);
      audio.play().then(() => {
        console.log(`✅ 音频自动播放开始: 段落 ${paragraphNumber}, 序列号 ${sequenceNumber}`);
        setAudioPlaying(index);
        setCurrentAudio(audio);
        setCurrentPlayingParagraph(paragraphNumber);
        
        audio.onended = () => {
          console.log(`音频播放结束: 段落 ${paragraphNumber}, 序列号 ${sequenceNumber}`);
          
          setNextSequenceToPlay(prev => ({
            ...prev,
            [paragraphNumber]: sequenceNumber + 1
          }));
          
          if (audioQueueMap && audioQueueMap[paragraphNumber]) {
            const queue = audioQueueMap[paragraphNumber];
            const nextItem = queue.find(item => item.sequenceNumber === sequenceNumber + 1);
            
            if (nextItem) {
              console.log(`自动播放下一个序列: 段落 ${paragraphNumber}, 序列号 ${nextItem.sequenceNumber}`);
              playAudioQueueSequential(queue, index, paragraphNumber);
            } else {
              console.log(`段落 ${paragraphNumber} 等待下一个序列...`);
              setAudioPlaying(null);
              setCurrentAudio(null);
              setCurrentPlayingParagraph(null);
              
              if (paragraphNumber === 1) {
                setIsParagraphBlocked(false);
              }
            }
          } else {
            setAudioPlaying(null);
            setCurrentAudio(null);
            setCurrentPlayingParagraph(null);
            
            if (paragraphNumber === 1) {
              setIsParagraphBlocked(false);
            }
          }
        };
      }).catch(error => {
        console.error(`❌ 自动播放音频失败:`, error);
      });
    }
  }, [autoPlayAudio, audioQueueMap, currentPlayingParagraph, nextSequenceToPlay, isParagraphBlocked]);

  const playAudioQueueFromIndex = (queue, startIndex, itemIndex, paragraphNumber) => {
    if (startIndex >= queue.length) {
      console.log(`队列播放完成: 段落 ${paragraphNumber}`);
      setAudioPlaying(null);
      setCurrentAudio(null);
      setCurrentPlayingParagraph(null);
      return;
    }

    const currentItem = queue[startIndex];
    console.log(`播放队列序列: 段落 ${paragraphNumber}, 序列号 ${currentItem.sequenceNumber}, 队列位置 ${startIndex + 1}/${queue.length}`);
    
    const audio = new Audio(currentItem.audioUrl);
    audio.play().then(() => {
      console.log(`✅ 音频播放开始: 段落 ${paragraphNumber}, 序列号 ${currentItem.sequenceNumber}`);
      setAudioPlaying(itemIndex);
      setCurrentAudio(audio);
      setCurrentPlayingParagraph(paragraphNumber);
      
      audio.onended = () => {
        console.log(`序列播放完成: 段落 ${paragraphNumber}, 序列号 ${currentItem.sequenceNumber}`);
        playAudioQueueFromIndex(queue, startIndex + 1, itemIndex, paragraphNumber);
      };
      
      audio.onerror = (error) => {
        console.error(`播放错误: 段落 ${paragraphNumber}, 序列号 ${currentItem.sequenceNumber}`, error);
        playAudioQueueFromIndex(queue, startIndex + 1, itemIndex, paragraphNumber);
      };
    }).catch(error => {
      console.error(`❌ 播放音频失败: 段落 ${paragraphNumber}, 序列号 ${currentItem.sequenceNumber}`, error);
      playAudioQueueFromIndex(queue, startIndex + 1, itemIndex, paragraphNumber);
    });
  };

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
