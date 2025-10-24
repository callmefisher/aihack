import React, { useState } from 'react';
import './App.css';
import InputForm from './components/InputForm';
import TaskStatus from './components/TaskStatus';
import VideoPlayer from './components/VideoPlayer';

function App() {
  const [taskId, setTaskId] = useState(null);
  const [taskCompleted, setTaskCompleted] = useState(false);
  const [videoUrl, setVideoUrl] = useState(null);

  const handleTaskCreated = (id) => {
    setTaskId(id);
    setTaskCompleted(false);
    setVideoUrl(null);
  };

  const handleTaskComplete = (url) => {
    setTaskCompleted(true);
    setVideoUrl(url);
  };

  const handleReset = () => {
    setTaskId(null);
    setTaskCompleted(false);
    setVideoUrl(null);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>📚 小说转动漫生成器</h1>
        <p>将您的小说文本转换为动漫风格的视频</p>
      </header>

      <main className="App-main">
        {!taskId && <InputForm onTaskCreated={handleTaskCreated} />}
        
        {taskId && !taskCompleted && (
          <TaskStatus 
            taskId={taskId} 
            onComplete={handleTaskComplete}
            onError={handleReset}
          />
        )}
        
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
