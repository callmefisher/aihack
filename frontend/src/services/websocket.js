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
    this.connectionStatus = 'disconnected';
    this.heartbeatInterval = null;
    this.heartbeatTimeout = null;
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
          this.connectionStatus = 'connected';
          this.emit('connection_status', { status: 'connected' });
          this.startHeartbeat();
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
          this.connectionStatus = 'error';
          this.emit('connection_status', { status: 'error', error });
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket已断开');
          this.connectionStatus = 'disconnected';
          this.emit('connection_status', { status: 'disconnected' });
          this.stopHeartbeat();
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
      this.connectionStatus = 'reconnecting';
      this.emit('connection_status', { status: 'reconnecting', attempt: this.reconnectAttempts, max: this.maxReconnectAttempts });
      console.log(`尝试重新连接... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connect().catch(error => {
          console.error('重新连接失败:', error);
        });
      }, this.reconnectDelay);
    } else {
      console.error('达到最大重连次数，停止重连');
      this.connectionStatus = 'failed';
      this.emit('connection_status', { status: 'failed' });
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
   * @param {string} imageBase64 - base64编码的图片数据
   */
  sendVideoRequest(taskId, text, paragraphNumber, imageBase64) {
    console.log(`=== WebSocket sendVideoRequest ===`);
    console.log(`WebSocket状态: ${this.ws ? this.ws.readyState : 'null'} (OPEN=${WebSocket.OPEN})`);
    
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        action: 'video',
        task_id: taskId,
        text: text,
        paragraph_number: paragraphNumber,
        image_base64: imageBase64
      };
      console.log(`发送视频请求消息:`, {
        action: message.action,
        task_id: message.task_id,
        paragraph_number: message.paragraph_number,
        text_length: message.text.length,
        image_base64_length: message.image_base64.length
      });
      this.ws.send(JSON.stringify(message));
      console.log(`✅ 视频请求消息已发送到WebSocket`);
    } else {
      console.error('❌ WebSocket未连接，无法发送视频请求');
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
  startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ action: 'ping' }));
        this.heartbeatTimeout = setTimeout(() => {
          console.warn('心跳超时，连接可能已断开');
          this.ws.close();
        }, 5000);
      }
    }, 30000);
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout);
      this.heartbeatTimeout = null;
    }
  }

  disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.connectionStatus = 'disconnected';
    this.listeners.clear();
  }

  /**
   * 检查连接状态
   */
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  getConnectionStatus() {
    return this.connectionStatus;
  }
}

// 创建单例实例
const wsService = new WebSocketService();

export default wsService;
