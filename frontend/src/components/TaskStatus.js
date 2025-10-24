import React, { useEffect, useState } from 'react';
import './TaskStatus.css';
import { getTaskStatus } from '../services/api';

function TaskStatus({ taskId, onComplete, onError }) {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const pollStatus = async () => {
      try {
        const data = await getTaskStatus(taskId);
        setStatus(data);

        if (data.status === 'completed') {
          const videoUrl = `http://localhost:8000${data.video_url || ''}`;
          setTimeout(() => onComplete(videoUrl), 1000);
        } else if (data.status === 'failed') {
          setError(data.error || '任务处理失败');
          setTimeout(() => onError(), 3000);
        }
      } catch (err) {
        setError('无法获取任务状态');
      }
    };

    pollStatus();
    const interval = setInterval(pollStatus, 2000);

    return () => clearInterval(interval);
  }, [taskId, onComplete, onError]);

  if (error) {
    return (
      <div className="task-status-container">
        <div className="task-status-card error">
          <h2>❌ 处理失败</h2>
          <p>{error}</p>
          <p>将在3秒后返回...</p>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="task-status-container">
        <div className="task-status-card">
          <div className="loading-spinner"></div>
          <p>正在获取任务状态...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="task-status-container">
      <div className="task-status-card">
        <h2>🎬 正在处理您的小说</h2>
        
        <div className="progress-section">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${status.progress}%` }}
            />
          </div>
          <div className="progress-text">{status.progress}%</div>
        </div>

        {status.current_step && (
          <div className="current-step">
            <p>当前步骤: {status.current_step}</p>
          </div>
        )}

        {status.total_scenes && (
          <div className="scene-info">
            <p>
              场景进度: {status.processed_scenes || 0} / {status.total_scenes}
            </p>
          </div>
        )}

        <div className="status-info">
          <div className="loading-spinner"></div>
          <p>请耐心等待，这可能需要几分钟...</p>
        </div>
      </div>
    </div>
  );
}

export default TaskStatus;
