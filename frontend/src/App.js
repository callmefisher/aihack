import React, { useState } from 'react';
import './App.css';
import InputForm from './components/InputForm';
import TaskStatus from './components/TaskStatus';
import VideoPlayer from './components/VideoPlayer';
import ContentDisplay from './components/ContentDisplay';

function App() {
  const [taskId, setTaskId] = useState(null);
  const [taskCompleted, setTaskCompleted] = useState(false);
  const [videoUrl, setVideoUrl] = useState(null);
  const [paragraphs, setParagraphs] = useState(null);
  const [showContent, setShowContent] = useState(false);
  const [progress, setProgress] = useState({ completed: 0, total: 0 });
  const [audioCacheMap, setAudioCacheMap] = useState({});
  const [imageCacheMap, setImageCacheMap] = useState({});
  const [videoCacheMap, setVideoCacheMap] = useState({});
  const [autoPlayAudio, setAutoPlayAudio] = useState(null);
  const [audioQueueMap, setAudioQueueMap] = useState({});
  const [imageQueueMap, setImageQueueMap] = useState({});
  const [videoQueueMap, setVideoQueueMap] = useState({});

  const handleTaskCreated = (id, text) => {
    setTaskId(id);
    setTaskCompleted(false);
    setVideoUrl(null);
    setAudioCacheMap({});
    setImageCacheMap({});
    setVideoCacheMap({});
    setAudioQueueMap({});
    setImageQueueMap({});
    setVideoQueueMap({});
    
    try {
      localStorage.clear();
      sessionStorage.clear();
    } catch (e) {
      console.warn('清理缓存失败:', e);
    }
    
    const splitParagraphs = text.split(/\n+/).filter(p => p.trim().length > 0);
    setParagraphs(splitParagraphs);
    setShowContent(true);
  };

  const handleAudioCache = (paragraphNumber, audioUrl, autoPlay = false, sequenceNumber = 0) => {
    setAudioQueueMap(prev => {
      const queue = prev[paragraphNumber] || [];
      const newItem = { sequenceNumber, audioUrl, timestamp: Date.now() };
      const updatedQueue = [...queue, newItem].sort((a, b) => a.sequenceNumber - b.sequenceNumber);
      return {
        ...prev,
        [paragraphNumber]: updatedQueue
      };
    });
    
    setAudioCacheMap(prev => ({
      ...prev,
      [paragraphNumber]: audioUrl
    }));
    console.log(`缓存音频: 段落 ${paragraphNumber}, 序列号 ${sequenceNumber}, 自动播放=${autoPlay}`);
    if (autoPlay) {
      setAutoPlayAudio({ paragraphNumber, audioUrl, sequenceNumber, timestamp: Date.now() });
    }
  };

  const handleImageCache = (paragraphNumber, imageUrls, sequenceNumber = 0) => {
    setImageQueueMap(prev => {
      const queue = prev[paragraphNumber] || [];
      const newItem = { sequenceNumber, imageUrls, timestamp: Date.now() };
      const updatedQueue = [...queue, newItem].sort((a, b) => a.sequenceNumber - b.sequenceNumber);
      return {
        ...prev,
        [paragraphNumber]: updatedQueue
      };
    });
    
    setImageCacheMap(prev => ({
      ...prev,
      [paragraphNumber]: imageUrls
    }));
    console.log(`缓存图片: 段落 ${paragraphNumber}, 序列号 ${sequenceNumber}, 图片数量=${imageUrls.length}`);
  };

  const handleTaskComplete = (url) => {
    setTaskCompleted(true);
    setVideoUrl(url);
  };

  const handleReset = () => {
    setTaskId(null);
    setTaskCompleted(false);
    setVideoUrl(null);
    setParagraphs(null);
    setShowContent(false);
    
    Object.values(audioQueueMap).forEach(queue => {
      queue.forEach(item => {
        try {
          URL.revokeObjectURL(item.audioUrl);
        } catch (e) {
          console.error('清理URL失败:', e);
        }
      });
    });
    setAudioCacheMap({});
    setImageCacheMap({});
    setVideoCacheMap({});
    setAudioQueueMap({});
    setImageQueueMap({});
    setVideoQueueMap({});
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>听，见</h1>
        <p style={{ fontSize: '1.5rem', fontWeight: '500', letterSpacing: '0.1em', marginTop: '15px' }}>让文字变成画面，让故事触手可及</p>
        {showContent && (
          <button className="reset-button" onClick={handleReset}>
            🔄 重新开始
          </button>
        )}
      </header>

      <main className="App-main">
        <InputForm onTaskCreated={handleTaskCreated} onAudioCache={handleAudioCache} onImageCache={handleImageCache} />
        
        {showContent && progress && (
          <div className="progress-container">
            <div className="progress-info">
              <span>处理进度:</span>
              <span>{progress.completed}/{progress.total}</span>
            </div>
            <div className="progress-bar-wrapper">
              <div className="progress-bar-fill" style={{ width: `${progress.total > 0 ? (progress.completed / progress.total * 100) : 0}%` }}></div>
            </div>
          </div>
        )}
        
        <ContentDisplay taskId={taskId} paragraphs={paragraphs} onProgressUpdate={setProgress} audioCacheMap={audioCacheMap} imageCacheMap={imageCacheMap} autoPlayAudio={autoPlayAudio} audioQueueMap={audioQueueMap} imageQueueMap={imageQueueMap} />
        
        {taskCompleted && videoUrl && (
          <VideoPlayer 
            videoUrl={videoUrl} 
            onReset={handleReset}
          />
        )}
      </main>

      <footer className="App-footer">
        <p>© 2025 Novel to Anime Generator | Powered by AI</p>
      </footer>
    </div>
  );
}

export default App;
