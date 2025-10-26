import React, { useState, useEffect } from 'react';
import './InputForm.css';
import wsService from '../services/websocket';

function InputForm({ onTaskCreated, onAudioCache, onImageCache }) {
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
      // 检查是否已经连接，避免重复连接
      if (wsService.isConnected()) {
        setWsConnected(true);
        console.log('WebSocket已连接，复用现有连接');
      } else {
        // 仅在未连接时才建立新连接
        wsService.connect()
          .then(() => {
            setWsConnected(true);
            console.log('WebSocket连接成功');
          })
          .catch(error => {
            console.error('WebSocket连接失败:', error);
            setWsConnected(false);
          });
      }

      // 注册事件监听
      const handleStatus = (data) => {
        setStreamingMessages(prev => [...prev, { type: 'status', ...data }]);
      };

      const handleTTSResult = (data) => {
        setStreamingMessages(prev => [...prev, { type: 'tts_result', ...data }]);
        console.log('TTS结果:', data);
        
        if (data.data && data.data.data) {
          try {
            const base64Audio = data.data.data;
            const binaryString = atob(base64Audio);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
              bytes[i] = binaryString.charCodeAt(i);
            }
            
            const blob = new Blob([bytes], { type: 'audio/mpeg' });
            const audioUrl = URL.createObjectURL(blob);
            
            const paragraphNumber = data.paragraph_number;
            const sequenceNumber = data.sequence_number !== undefined ? data.sequence_number : 0;
            
            if (onAudioCache && paragraphNumber !== undefined) {
              onAudioCache(paragraphNumber, audioUrl, true, sequenceNumber);
              console.log(`音频已缓存且将自动播放，段落 ${paragraphNumber}, 序列号 ${sequenceNumber}`);
            }
          } catch (error) {
            console.error('解码base64音频失败:', error);
            setError('解码音频失败: ' + error.message);
          }
        }
      };

      const handleImageResult = (data) => {
        setStreamingMessages(prev => [...prev, { type: 'image_result', ...data }]);
        console.log('图片生成结果:', data);
        
        if (data.data && data.data.data && Array.isArray(data.data.data)) {
          try {
            const imageUrls = data.data.data.map(img => {
              const base64Data = img.b64_json;
              const format = data.data.output_format || 'png';
              return `data:image/${format};base64,${base64Data}`;
            });
            
            const paragraphNumber = data.paragraph_number;
            const sequenceNumber = data.sequence_number !== undefined ? data.sequence_number : 0;
            
            if (onImageCache && paragraphNumber !== undefined) {
              onImageCache(paragraphNumber, imageUrls, sequenceNumber);
              console.log(`图片已缓存，段落 ${paragraphNumber}, 序列号 ${sequenceNumber}，图片数量 ${imageUrls.length}`);
            }
          } catch (error) {
            console.error('处理图片数据失败:', error);
            setError('处理图片失败: ' + error.message);
          }
        }
      };

      const handleVideoProgress = (data) => {
        setStreamingMessages(prev => [...prev, { type: 'video_progress', ...data }]);
        console.log('视频生成进度:', data);
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
      wsService.on('image_result', handleImageResult);
      wsService.on('video_progress', handleVideoProgress);
      wsService.on('error', handleError);
      wsService.on('complete', handleComplete);

      // 清理函数 - 只移除事件监听器，不断开连接
      return () => {
        wsService.off('status', handleStatus);
        wsService.off('tts_result', handleTTSResult);
        wsService.off('image_result', handleImageResult);
        wsService.off('video_progress', handleVideoProgress);
        wsService.off('error', handleError);
        wsService.off('complete', handleComplete);
        // 注意：不调用 wsService.disconnect()，保持连接活跃
      };
    }
  }, [useWebSocket, onAudioCache, onImageCache]);

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
          // WebSocket模式 - 分段发送TTS请求
          setProgress(30);
          
          // 分割段落（使用单个换行符）
          const paragraphs = textInput.split(/\n+/).filter(p => p.trim().length > 0);
          
          // 为每个段落发送TTS请求
          for (let i = 0; i < paragraphs.length; i++) {
            wsService.sendText(paragraphs[i], i + 1);
          }
          
          setProgress(50);
          // WebSocket会通过事件回调处理响应
          response = { task_id: `ws-${Date.now()}`, status: 'processing' };
          onTaskCreated(response.task_id, text);
        } else {
          throw new Error('WebSocket未连接，请等待连接成功后再试');
        }
      } else {
        if (!urlInput.trim()) {
          throw new Error('请输入URL');
        }
        
        if (!wsConnected) {
          throw new Error('WebSocket未连接，请等待连接成功后再试');
        }
        
        setProgress(10);
        
        try {
          const fetchResponse = await fetch(urlInput);
          if (!fetchResponse.ok) {
            throw new Error(`无法获取URL内容: ${fetchResponse.status}`);
          }
          
          let urlText;
          const contentType = fetchResponse.headers.get('content-type');
          const charset = contentType?.match(/charset=([^;]+)/)?.[1]?.toLowerCase();
          
          if (charset && (charset === 'gbk' || charset === 'gb2312' || charset === 'gb18030')) {
            const arrayBuffer = await fetchResponse.arrayBuffer();
            const decoder = new TextDecoder(charset);
            urlText = decoder.decode(arrayBuffer);
          } else if (!charset || charset === 'utf-8' || charset === 'utf8') {
            urlText = await fetchResponse.text();
          } else {
            const arrayBuffer = await fetchResponse.arrayBuffer();
            try {
              const decoder = new TextDecoder(charset);
              urlText = decoder.decode(arrayBuffer);
            } catch (e) {
              console.warn(`不支持的编码格式 ${charset}，尝试使用UTF-8`);
              const utf8Decoder = new TextDecoder('utf-8');
              urlText = utf8Decoder.decode(arrayBuffer);
            }
          }
          
          setProgress(30);
          
          setTextInput(urlText);
          setInputType('text');
          
          const paragraphs = urlText.split(/\n+/).filter(p => p.trim().length > 0);
          
          for (let i = 0; i < paragraphs.length; i++) {
            wsService.sendText(paragraphs[i], i + 1);
          }
          
          setProgress(50);
          response = { task_id: `ws-url-${Date.now()}`, status: 'processing' };
          onTaskCreated(response.task_id, urlText);
        } catch (fetchError) {
          throw new Error(`URL解析失败: ${fetchError.message}`);
        }
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
