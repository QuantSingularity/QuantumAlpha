// This file would contain the Redux Toolkit store setup.
// Example: configureStore from @reduxjs/toolkit

import { configureStore } from "@reduxjs/toolkit";
import { api } from "../services/api";
import authReducer from "./slices/authSlice";
import portfolioReducer from "./slices/portfolioSlice";
import strategyReducer from "./slices/strategySlice";
import themeReducer from "./slices/themeSlice";
import uiReducer from "./slices/uiSlice";

const store = configureStore({
  reducer: {
    [api.reducerPath]: api.reducer,
    auth: authReducer,
    portfolio: portfolioReducer,
    strategy: strategyReducer,
    theme: themeReducer,
    ui: uiReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(api.middleware),
});

export { store };
export default store;
