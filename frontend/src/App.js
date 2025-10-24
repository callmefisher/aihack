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

  const handleTaskCreated = (id, text) => {
    setTaskId(id);
    setTaskCompleted(false);
    setVideoUrl(null);
    setAudioCacheMap({});
    
    const splitParagraphs = text.split(/\n\n+/).filter(p => p.trim().length > 0);
    setParagraphs(splitParagraphs);
    setShowContent(true);
  };

  const handleAudioCache = (paragraphNumber, audioUrl) => {
    setAudioCacheMap(prev => ({
      ...prev,
      [paragraphNumber]: audioUrl
    }));
    console.log(`缓存音频: 段落 ${paragraphNumber}`);
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
    
    // 清理缓存的音频URL
    Object.values(audioCacheMap).forEach(url => {
      try {
        URL.revokeObjectURL(url);
      } catch (e) {
        console.error('清理URL失败:', e);
      }
    });
    setAudioCacheMap({});
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>📚 小说转动漫生成器</h1>
        <p>将您的小说文本转换为动漫风格的视频</p>
        {showContent && (
          <button className="reset-button" onClick={handleReset}>
            🔄 重新开始
          </button>
        )}
      </header>

      <main className="App-main">
        <InputForm onTaskCreated={handleTaskCreated} onAudioCache={handleAudioCache} />
        
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
        
        <ContentDisplay taskId={taskId} paragraphs={paragraphs} onProgressUpdate={setProgress} audioCacheMap={audioCacheMap} />
        
        {taskCompleted && videoUrl && (
          <VideoPlayer 
            videoUrl={videoUrl} 
            onReset={handleReset}
          />
        )}
      </main>

      <footer className="App-footer">
        <p>© 2024 Novel to Anime Generator | Powered by AI</p>
      </footer>
    </div>
  );
}

export default App;
