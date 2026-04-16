import axios from "axios";
import type { InternalAxiosRequestConfig  } from 'axios';
import { getToken, logout } from "./auth";

const http = axios.create({
  baseURL: import.meta.env.VITE_REST_API_URL as string,
});

// JWT TOKEN AUTOMATIKUS HOZZÁADÁS
http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getToken();

  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});


// 401 HANDLING 
http.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      console.log("Unauthorized");
      logout();
    }
    return Promise.reject(err);
  }
);

export default http;
