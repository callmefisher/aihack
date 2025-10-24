import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

export const createTextTask = async (text, config = null) => {
  const response = await axios.post(`${API_BASE_URL}/tasks/text`, {
    text,
    config
  });
  return response.data;
};

export const createURLTask = async (url, config = null) => {
  const response = await axios.post(`${API_BASE_URL}/tasks/url`, {
    url,
    config
  });
  return response.data;
};

export const getTaskStatus = async (taskId) => {
  const response = await axios.get(`${API_BASE_URL}/tasks/${taskId}/status`);
  return response.data;
};

export const getTaskResult = async (taskId) => {
  const response = await axios.get(`${API_BASE_URL}/tasks/${taskId}/result`);
  return response.data;
};
