import axios from "axios";
import AsyncStorage from "@react-native-async-storage/async-storage";

// API Base URL configuration
// For iOS Simulator: Use http://localhost:8080/api
// For Android Emulator: Use http://10.0.2.2:8080/api
// For Physical Device: Use http://YOUR_COMPUTER_IP:8080/api
const API_BASE_URL = process.env.API_BASE_URL || "http://localhost:8080/api";

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for adding token
api.interceptors.request.use(
  async (config) => {
    try {
      const token = await AsyncStorage.getItem("token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.error("Error reading token from storage:", error);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Handle token expiration
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = await AsyncStorage.getItem("refreshToken");
        if (!refreshToken) {
          // Force logout if no refresh token
          await AsyncStorage.removeItem("token");
          await AsyncStorage.removeItem("user");
          return Promise.reject(error);
        }

        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refreshToken,
        });

        const { token } = response.data;
        await AsyncStorage.setItem("token", token);

        // Update the authorization header
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Force logout on refresh failure
        await AsyncStorage.removeItem("token");
        await AsyncStorage.removeItem("refreshToken");
        await AsyncStorage.removeItem("user");
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);

// Auth API
export const authAPI = {
  login: (email, password) => api.post("/auth/login", { email, password }),
  register: (userData) => api.post("/auth/register", userData),
  getUser: () => api.get("/auth/user"),
  logout: () => api.post("/auth/logout"),
};

// Portfolio API
export const portfolioAPI = {
  getPortfolio: () => api.get("/portfolio"),
  getPositions: () => api.get("/portfolio/positions"),
  getHistory: (timeframe) =>
    api.get(`/portfolio/history?timeframe=${timeframe}`),
};

// Market Data API
export const marketDataAPI = {
  getMarketData: (symbol) => api.get(`/market-data/${symbol}`),
  getAllMarketData: () => api.get("/market-data"),
};

// Strategy API
export const strategyAPI = {
  getStrategies: () => api.get("/strategies"),
  getStrategy: (id) => api.get(`/strategies/${id}`),
  createStrategy: (data) => api.post("/strategies", data),
  updateStrategy: (id, data) => api.patch(`/strategies/${id}`, data),
  deleteStrategy: (id) => api.delete(`/strategies/${id}`),
};

// Trade API
export const tradeAPI = {
  getTrades: (params) => api.get("/trades", { params }),
  placeOrder: (data) => api.post("/trade/order", data),
};

// Risk API
export const riskAPI = {
  getRiskMetrics: (strategyId) => api.get(`/risk/metrics/${strategyId}`),
  getPortfolioRiskMetrics: () => api.get("/risk/metrics"),
};

// Watchlist API
export const watchlistAPI = {
  getWatchlist: () => api.get("/watchlist"),
};

// News API
export const newsAPI = {
  getNews: () => api.get("/news"),
};

// Analytics API
export const analyticsAPI = {
  getPerformance: () => api.get("/analytics/performance"),
};

export default api;
