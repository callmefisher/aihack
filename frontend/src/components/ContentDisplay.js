import React, { useState, useEffect } from 'react';
import './ContentDisplay.css';
import { generateImage, generateVideo, getAudio } from '../services/api';

function ContentDisplay({ taskId, paragraphs, onProgressUpdate }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState({});
  const [audioPlaying, setAudioPlaying] = useState(null);
  const [zoomedImage, setZoomedImage] = useState(null);
  const [speechPlaying, setSpeechPlaying] = useState(null);

  useEffect(() => {
    if (paragraphs && paragraphs.length > 0) {
      const initialItems = paragraphs.map((text, index) => ({
        id: index + 1,
        text,
        image: null,
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

  const processTestMode = (itemsList) => {
    const updatedItems = itemsList.map((item, index) => ({
      ...item,
      image: '/test.jpeg',
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
          image: response.image_url,
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
    
    if (audioPlaying === index) {
      setAudioPlaying(null);
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
        const response = await getAudio(taskId, item.text, index + 1);
        
        setItems(prev => {
          const updated = [...prev];
          updated[index] = { ...updated[index], audioUrl: response.audio_url, loadingAudio: false };
          return updated;
        });

        playAudio(response.audio_url, index);
      } catch (error) {
        console.error(`Error getting audio for item ${index + 1}:`, error);
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

  const handleGenerateVideo = async (index) => {
    const item = items[index];

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

      const response = await generateVideo(taskId, item.text, index + 1, item.image);
      
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

    } catch (error) {
      console.error(`Error generating video for item ${index + 1}:`, error);
      setItems(prev => {
        const updated = [...prev];
        updated[index] = { ...updated[index], loadingVideo: false, progress: 0 };
        return updated;
      });
    }
  };

  const completedItems = items.filter(item => item.image).length;
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
                  ) : item.image ? (
                    <>
                      <img 
                        src={item.image} 
                        alt={`Scene ${item.id}`} 
                        onClick={() => handleImageClick(item.image)}
                        style={{ cursor: 'pointer' }}
                        title="点击放大图片"
                      />
                      <div className="image-actions">
                        <button
                          className={`action-button ${speechPlaying === index ? 'playing' : ''}`}
                          onClick={() => handlePlaySpeech(item.text, index)}
                        >
                          {speechPlaying === index ? '⏸️ 停止朗读' : '🔊 朗读段落'}
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
                    </>
                  ) : (
                    <div className="placeholder">等待生成...</div>
                  )}
                </div>
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
