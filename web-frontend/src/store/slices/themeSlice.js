import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  darkMode: true,
  theme: "dark", // 'light', 'dark', 'auto'
  primaryColor: "#00d4ff",
  accentColor: "#0099cc",
  fontSize: "medium", // 'small', 'medium', 'large'
  animations: true,
  compactMode: false,
  highContrast: false,
};

const themeSlice = createSlice({
  name: "theme",
  initialState,
  reducers: {
    toggleDarkMode: (state) => {
      state.darkMode = !state.darkMode;
      state.theme = state.darkMode ? "dark" : "light";
    },
    setTheme: (state, action) => {
      state.theme = action.payload;
      state.darkMode = action.payload === "dark";
    },
    setPrimaryColor: (state, action) => {
      state.primaryColor = action.payload;
    },
    setAccentColor: (state, action) => {
      state.accentColor = action.payload;
    },
    setFontSize: (state, action) => {
      state.fontSize = action.payload;
    },
    toggleAnimations: (state) => {
      state.animations = !state.animations;
    },
    toggleCompactMode: (state) => {
      state.compactMode = !state.compactMode;
    },
    toggleHighContrast: (state) => {
      state.highContrast = !state.highContrast;
    },
    resetTheme: (_state) => {
      return initialState;
    },
  },
});

export const {
  toggleDarkMode,
  setTheme,
  setPrimaryColor,
  setAccentColor,
  setFontSize,
  toggleAnimations,
  toggleCompactMode,
  toggleHighContrast,
  resetTheme,
} = themeSlice.actions;

export default themeSlice.reducer;
