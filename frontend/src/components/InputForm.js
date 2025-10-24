import React, { useState } from 'react';
import './InputForm.css';
import { createTextTask, createURLTask } from '../services/api';

function InputForm({ onTaskCreated }) {
  const [inputType, setInputType] = useState('text');
  const [textInput, setTextInput] = useState('');
  const [urlInput, setUrlInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    setProgress(0);

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
        } else {
          setProgress(30);
          response = await createTextTask(textInput);
          setProgress(100);
        }
      } else {
        if (!urlInput.trim()) {
          throw new Error('请输入小说URL');
        }
        setProgress(30);
        response = await createURLTask(urlInput);
        text = response.text || urlInput;
        setProgress(100);
      }

      onTaskCreated(response.task_id, text);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '提交失败，请重试');
      setProgress(0);
    } finally {
      setLoading(false);
      setTimeout(() => setProgress(0), 1000);
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
