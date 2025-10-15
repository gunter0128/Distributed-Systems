import axios from 'axios';

const api = axios.create({
  baseURL: 'http://35.221.140.146:5000'
});

export default api;