import React from 'react';
import './VideoPlayer.css';

function VideoPlayer({ videoUrl, onReset }) {
  return (
    <div className="video-player-container">
      <div className="video-player-card">
        <h2>🎉 视频生成成功!</h2>
        
        <div className="video-wrapper">
          <video controls>
            <source src={videoUrl} type="video/mp4" />
            您的浏览器不支持视频播放
          </video>
        </div>

        <div className="action-buttons">
          <a 
            href={videoUrl} 
            download 
            className="download-button"
          >
            📥 下载视频
          </a>
          
          <button 
            onClick={onReset}
            className="reset-button"
          >
            🔄 生成新视频
          </button>
        </div>
      </div>
    </div>
  );
}

export default VideoPlayer;
