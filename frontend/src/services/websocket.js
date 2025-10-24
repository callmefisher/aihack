/**
 * WebSocket服务
 * 用于前后端实时通信
 */

class WebSocketService {
  constructor() {
    this.ws = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;
    this.url = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/api/ws';
  }

  /**
   * 连接WebSocket
   */
  connect() {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('WebSocket已连接');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('解析WebSocket消息失败:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket错误:', error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket已断开');
          this.attemptReconnect();
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 尝试重新连接
   */
  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`尝试重新连接... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connect().catch(error => {
          console.error('重新连接失败:', error);
        });
      }, this.reconnectDelay);
    } else {
      console.error('达到最大重连次数，停止重连');
      this.emit('max_reconnect_failed', {});
    }
  }

  /**
   * 发送文本进行TTS处理
   * @param {string} text - 要处理的文本
   * @param {number} paragraphNumber - 段落编号
   */
  sendText(text, paragraphNumber = null) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        action: 'tts',
        text: text,
        paragraph_number: paragraphNumber
      };
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket未连接');
      throw new Error('WebSocket未连接');
    }
  }

  /**
   * 发送视频生成请求
   * @param {string} taskId - 任务ID
   * @param {string} text - 文本内容
   * @param {number} paragraphNumber - 段落编号
   * @param {string} imageUrl - 图片URL
   */
  sendVideoRequest(taskId, text, paragraphNumber, imageUrl) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        action: 'video',
        task_id: taskId,
        text: text,
        paragraph_number: paragraphNumber,
        image_url: imageUrl
      };
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket未连接');
      throw new Error('WebSocket未连接');
    }
  }

  /**
   * 处理接收到的消息
   * @param {object} data - 消息数据
   */
  handleMessage(data) {
    const { type, ...payload } = data;
    
    switch (type) {
      case 'status':
        this.emit('status', payload);
        break;
      case 'tts_result':
        this.emit('tts_result', payload);
        break;
      case 'image_result':
        this.emit('image_result', payload);
        break;
      case 'video_result':
        this.emit('video_result', payload);
        break;
      case 'error':
        this.emit('error', payload);
        break;
      case 'complete':
        this.emit('complete', payload);
        break;
      default:
        console.warn('未知消息类型:', type);
    }
  }

  /**
   * 注册事件监听器
   * @param {string} event - 事件名称
   * @param {function} callback - 回调函数
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  /**
   * 移除事件监听器
   * @param {string} event - 事件名称
   * @param {function} callback - 回调函数
   */
  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  /**
   * 触发事件
   * @param {string} event - 事件名称
   * @param {object} data - 事件数据
   */
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`事件处理器错误 (${event}):`, error);
        }
      });
    }
  }

  /**
   * 关闭WebSocket连接
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.listeners.clear();
  }

  /**
   * 检查连接状态
   */
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }
}

// 创建单例实例
const wsService = new WebSocketService();

export default wsService;
