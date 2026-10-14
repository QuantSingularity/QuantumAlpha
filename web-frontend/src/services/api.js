import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

/**
 * The backend wraps every successful response in an envelope:
 *   { success: true, data: <payload>, timestamp: "..." }
 *
 * The UI wants the raw payload. Unwrapping the envelope here, in one place, is
 * what keeps every page from receiving an object where it expects an array (the
 * bug that crashed the dashboard to a blank screen). `unwrap` is applied as the
 * default `transformResponse` for all queries and mutations below.
 */
const unwrap = (response) => {
  if (
    response &&
    typeof response === "object" &&
    "data" in response &&
    "success" in response
  ) {
    return response.data;
  }
  return response;
};

const rawBaseQuery = fetchBaseQuery({
  baseUrl: import.meta.env.VITE_API_URL || "http://localhost:8080/api",
  prepareHeaders: (headers, { getState }) => {
    const token = getState().auth.token || localStorage.getItem("qa_token");
    if (token) headers.set("authorization", `Bearer ${token}`);
    return headers;
  },
});

export const api = createApi({
  reducerPath: "api",
  baseQuery: rawBaseQuery,
  tagTypes: [
    "Portfolio",
    "Strategy",
    "Trade",
    "User",
    "Watchlist",
    "News",
    "AiModel",
  ],
  endpoints: (builder) => ({
    // ── Auth ────────────────────────────────────────────────────────────
    login: builder.mutation({
      query: (credentials) => ({
        url: "/auth/login",
        method: "POST",
        body: credentials,
      }),
      transformResponse: unwrap,
    }),
    register: builder.mutation({
      query: (userData) => ({
        url: "/auth/register",
        method: "POST",
        body: userData,
      }),
      transformResponse: unwrap,
    }),
    getUser: builder.query({
      query: () => "/auth/user",
      transformResponse: unwrap,
      providesTags: ["User"],
    }),

    // ── Portfolio ───────────────────────────────────────────────────────
    getPortfolio: builder.query({
      query: () => "/portfolio",
      transformResponse: unwrap,
      providesTags: ["Portfolio"],
    }),
    getPortfolioHistory: builder.query({
      query: (timeframe = "1M") => `/portfolio/history?timeframe=${timeframe}`,
      transformResponse: unwrap,
      providesTags: ["Portfolio"],
    }),

    // ── Strategies ──────────────────────────────────────────────────────
    getStrategies: builder.query({
      query: () => "/strategies",
      transformResponse: unwrap,
      providesTags: ["Strategy"],
    }),
    getStrategy: builder.query({
      query: (id) => `/strategies/${id}`,
      transformResponse: unwrap,
      providesTags: (_r, _e, id) => [{ type: "Strategy", id }],
    }),
    createStrategy: builder.mutation({
      query: (strategy) => ({
        url: "/strategies",
        method: "POST",
        body: strategy,
      }),
      transformResponse: unwrap,
      invalidatesTags: ["Strategy"],
    }),
    updateStrategy: builder.mutation({
      query: ({ id, ...patch }) => ({
        url: `/strategies/${id}`,
        method: "PATCH",
        body: patch,
      }),
      transformResponse: unwrap,
      invalidatesTags: (_r, _e, { id }) => [{ type: "Strategy", id }],
    }),
    deleteStrategy: builder.mutation({
      query: (id) => ({ url: `/strategies/${id}`, method: "DELETE" }),
      transformResponse: unwrap,
      invalidatesTags: ["Strategy"],
    }),

    // ── Trades ──────────────────────────────────────────────────────────
    // Canonical backend route is /trades (not /trade/orders).
    getTrades: builder.query({
      query: (params) => ({ url: "/trades", params }),
      transformResponse: unwrap,
      providesTags: ["Trade"],
    }),
    placeOrder: builder.mutation({
      query: (order) => ({ url: "/trade/order", method: "POST", body: order }),
      transformResponse: unwrap,
      invalidatesTags: ["Trade", "Portfolio"],
    }),

    // ── Market data ─────────────────────────────────────────────────────
    getMarketData: builder.query({
      query: (symbol) => `/market-data/${symbol}`,
      transformResponse: unwrap,
    }),
    getAllMarketData: builder.query({
      query: () => "/market-data",
      transformResponse: unwrap,
    }),

    // ── Watchlist / News / Analytics / Risk ─────────────────────────────
    getWatchlist: builder.query({
      query: () => "/watchlist",
      transformResponse: unwrap,
      providesTags: ["Watchlist"],
    }),
    getNews: builder.query({
      query: () => "/news",
      transformResponse: unwrap,
      providesTags: ["News"],
    }),
    getPerformanceAnalytics: builder.query({
      query: () => "/analytics/performance",
      transformResponse: unwrap,
    }),
    getRiskMetrics: builder.query({
      query: (strategyId) =>
        strategyId ? `/risk/metrics/${strategyId}` : "/risk/metrics",
      transformResponse: unwrap,
    }),
    getAiModels: builder.query({
      query: (params) => ({ url: "/ai/models", params }),
      transformResponse: unwrap,
      providesTags: ["AiModel"],
    }),
    getAiModelHealth: builder.query({
      query: ({ modelId, symbol }) => ({
        url: `/ai/models/${modelId}/health`,
        params: symbol ? { symbol } : undefined,
      }),
      transformResponse: unwrap,
    }),
    getAiPrediction: builder.mutation({
      query: (body) => ({ url: "/ai/predict", method: "POST", body }),
      transformResponse: unwrap,
    }),
    generateAiSignals: builder.mutation({
      query: (body) => ({ url: "/ai/signals/generate", method: "POST", body }),
      transformResponse: unwrap,
    }),
    getAiRecommendation: builder.mutation({
      query: (body) => ({ url: "/ai/rl/act", method: "POST", body }),
      transformResponse: unwrap,
    }),
  }),
});

export const {
  useLoginMutation,
  useRegisterMutation,
  useGetUserQuery,
  useGetPortfolioQuery,
  useGetPortfolioHistoryQuery,
  useGetStrategiesQuery,
  useGetStrategyQuery,
  useCreateStrategyMutation,
  useUpdateStrategyMutation,
  useDeleteStrategyMutation,
  useGetTradesQuery,
  usePlaceOrderMutation,
  useGetMarketDataQuery,
  useGetAllMarketDataQuery,
  useGetWatchlistQuery,
  useGetNewsQuery,
  useGetPerformanceAnalyticsQuery,
  useGetRiskMetricsQuery,
  useGetAiModelsQuery,
  useGetAiModelHealthQuery,
  useGetAiPredictionMutation,
  useGenerateAiSignalsMutation,
  useGetAiRecommendationMutation,
} = api;
