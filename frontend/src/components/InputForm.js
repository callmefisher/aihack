import React, { useState, useEffect } from 'react';
import './InputForm.css';
import { createTextTask, createURLTask } from '../services/api';
import wsService from '../services/websocket';

function InputForm({ onTaskCreated, onAudioCache }) {
  const [inputType, setInputType] = useState('text');
  const [textInput, setTextInput] = useState('');
  const [urlInput, setUrlInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(0);
  const [wsConnected, setWsConnected] = useState(false);
  const [streamingMessages, setStreamingMessages] = useState([]);
  const [useWebSocket, setUseWebSocket] = useState(true);

  // WebSocket连接管理
  useEffect(() => {
    if (useWebSocket) {
      // 连接WebSocket
      wsService.connect()
        .then(() => {
          setWsConnected(true);
          console.log('WebSocket连接成功');
        })
        .catch(error => {
          console.error('WebSocket连接失败:', error);
          setWsConnected(false);
        });

      // 注册事件监听
      const handleStatus = (data) => {
        setStreamingMessages(prev => [...prev, { type: 'status', ...data }]);
      };

      const handleTTSResult = (data) => {
        setStreamingMessages(prev => [...prev, { type: 'tts_result', ...data }]);
        console.log('TTS结果:', data);
        
        // 处理七牛云TTS返回的base64音频数据
        if (data.data && data.data.data) {
          try {
            // 解码base64音频数据
            const base64Audio = data.data.data;
            const binaryString = atob(base64Audio);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
              bytes[i] = binaryString.charCodeAt(i);
            }
            
            // 创建Blob对象
            const blob = new Blob([bytes], { type: 'audio/mpeg' });
            const audioUrl = URL.createObjectURL(blob);
            
            // 从数据中提取段落编号，如果没有则使用文本匹配
            const paragraphNumber = data.paragraph_number;
            
            // 缓存音频URL到父组件
            if (onAudioCache && paragraphNumber !== undefined) {
              onAudioCache(paragraphNumber, audioUrl);
            }
            
            // 创建并播放音频
            const audio = new Audio(audioUrl);
            audio.play().then(() => {
              console.log('音频播放成功');
            }).catch(error => {
              console.error('音频播放失败:', error);
              setError('音频播放失败: ' + error.message);
            });
            
            // 注意：不再在音频结束后立即清理URL，因为需要缓存
            // URL清理将由父组件管理
          } catch (error) {
            console.error('解码base64音频失败:', error);
            setError('解码音频失败: ' + error.message);
          }
        }
      };

      const handleError = (data) => {
        setError(data.message);
        setStreamingMessages(prev => [...prev, { type: 'error', ...data }]);
      };

      const handleComplete = (data) => {
        setLoading(false);
        setStreamingMessages(prev => [...prev, { type: 'complete', ...data }]);
      };

      wsService.on('status', handleStatus);
      wsService.on('tts_result', handleTTSResult);
      wsService.on('error', handleError);
      wsService.on('complete', handleComplete);

      // 清理函数
      return () => {
        wsService.off('status', handleStatus);
        wsService.off('tts_result', handleTTSResult);
        wsService.off('error', handleError);
        wsService.off('complete', handleComplete);
      };
    }
  }, [useWebSocket]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    setProgress(0);
    setStreamingMessages([]);

    try {
      let response;
      let text;
      
      if (inputType === 'text') {
        if (!textInput.trim()) {
          throw new Error('请输入小说文本');
        }
        text = textInput;
        
        if (textInput.trim() === 'test') {
          setProgress(50);
          response = { task_id: 'test-mode', status: 'test' };
          setProgress(100);
          onTaskCreated(response.task_id, text);
        } else if (useWebSocket && wsConnected) {
          // WebSocket模式 - 不调用HTTP API
          setProgress(50);
          wsService.sendText(textInput);
          // WebSocket会通过事件回调处理响应
          response = { task_id: `ws-${Date.now()}`, status: 'processing' };
          onTaskCreated(response.task_id, text, true);
        } else {
          // HTTP模式（仅在WebSocket未启用或未连接时使用）
          setProgress(30);
          response = await createTextTask(textInput);
          setProgress(100);
          onTaskCreated(response.task_id, text, false);
        }
      } else {
        if (!urlInput.trim()) {
          throw new Error('请输入小说URL');
        }
        setProgress(30);
        response = await createURLTask(urlInput);
        text = response.text || urlInput;
        setProgress(100);
        onTaskCreated(response.task_id, text);
      }

    } catch (err) {
      setError(err.response?.data?.detail || err.message || '提交失败，请重试');
      setProgress(0);
      setLoading(false);
    } finally {
      if (!useWebSocket || !wsConnected) {
        setLoading(false);
        setTimeout(() => setProgress(0), 1000);
      }
    }
  };

  return (
    <div className="input-form-container">
      <div className="input-form-card">
        <h2>📝 输入小说内容</h2>
        
        {/* WebSocket连接状态 */}
        <div className="ws-status">
          <label>
            <input
              type="checkbox"
              checked={useWebSocket}
              onChange={(e) => setUseWebSocket(e.target.checked)}
            />
            使用WebSocket模式
          </label>
          {useWebSocket && (
            <span className={`status-indicator ${wsConnected ? 'connected' : 'disconnected'}`}>
              {wsConnected ? '● 已连接' : '○ 未连接'}
            </span>
          )}
        </div>

        {/* 流式消息显示 */}
        {streamingMessages.length > 0 && (
          <div className="streaming-messages">
            <h3>实时消息:</h3>
            {streamingMessages.map((msg, index) => (
              <div key={index} className={`message message-${msg.type}`}>
                <strong>{msg.type}:</strong> {msg.message || JSON.stringify(msg.data)}
              </div>
            ))}
          </div>
        )}
        
        <div className="input-type-selector">
          <button
            className={inputType === 'text' ? 'active' : ''}
            onClick={() => setInputType('text')}
          >
            文本输入
          </button>
          <button
            className={inputType === 'url' ? 'active' : ''}
            onClick={() => setInputType('url')}
          >
            URL 输入
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {inputType === 'text' ? (
            <div className="form-group">
              <label>小说文本</label>
              <textarea
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="在此输入或粘贴小说文本内容..."
                rows="15"
                disabled={loading}
              />
            </div>
          ) : (
            <div className="form-group">
              <label>小说 URL</label>
              <input
                type="url"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                placeholder="https://example.com/novel.txt"
                disabled={loading}
              />
              <small>支持包含文本内容的网页链接</small>
            </div>
          )}

          {error && <div className="error-message">{error}</div>}

          <button 
            type="submit" 
            className="submit-button"
            disabled={loading}
          >
            {loading ? '⏳ 提交中...' : '🚀 开始生成'}
          </button>
          
          {loading && progress > 0 && (
            <div className="progress-bar-container">
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${progress}%` }}></div>
              </div>
              <div className="progress-text">{progress}%</div>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}

export default InputForm;
