import axios from "axios";
import { getToken, logout } from "./auth";

const http = axios.create({
  baseURL: import.meta.env.VITE_REST_API_URL,
});

// JWT TOKEN AUTOMATIKUS HOZZÁADÁS
http.interceptors.request.use((config) => {
  const token = getToken();

  if (token) {
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
      window.location.href = "/login";      
    }
    return Promise.reject(err);
  }
);

export default http;
