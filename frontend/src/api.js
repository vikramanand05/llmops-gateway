import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
  timeout: 15000
});

export function setAdminToken(token) {
  api.defaults.headers.common["X-Admin-Token"] = token;
}

export default api;