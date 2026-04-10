import React, { createContext, useState, useContext, useCallback } from "react";
import { useColorScheme } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";

const lightTheme = {
  primary: "#1aff92",
  secondary: "#0066cc",
  background: "#f8f9fa",
  card: "#ffffff",
  surface: "#ffffff",
  text: "#121212",
  textSecondary: "#666666",
  border: "#e1e1e1",
  notification: "#ff3b30",
  error: "#ff4d4d",
  success: "#34c759",
  warning: "#ffcc00",
  info: "#0066cc",
  shadow: "#000000",
  chartBackground: "#ffffff",
  chartBackgroundGradientFrom: "#ffffff",
  chartBackgroundGradientTo: "#f8f9fa",
};

const darkTheme = {
  primary: "#1aff92",
  secondary: "#0a84ff",
  background: "#121212",
  card: "#1e1e1e",
  surface: "#2a2a2a",
  text: "#ffffff",
  textSecondary: "#cccccc",
  border: "#2c2c2c",
  notification: "#ff453a",
  error: "#ff4d4d",
  success: "#32d74b",
  warning: "#ffd60a",
  info: "#0a84ff",
  shadow: "#000000",
  chartBackground: "#1e1e1e",
  chartBackgroundGradientFrom: "#1e1e1e",
  chartBackgroundGradientTo: "#1e1e1e",
};

const ThemeContext = createContext();

export const useTheme = () => useContext(ThemeContext);

export const ThemeProvider = ({ children }) => {
  const deviceTheme = useColorScheme();
  const [isDarkMode, setIsDarkMode] = useState(deviceTheme === "dark");

  const theme = isDarkMode ? darkTheme : lightTheme;

  const toggleTheme = useCallback(() => {
    setIsDarkMode((prev) => {
      const next = !prev;
      AsyncStorage.setItem("theme_preference", next ? "dark" : "light").catch(
        () => {},
      );
      return next;
    });
  }, []);

  const setTheme = useCallback(
    (preference) => {
      if (preference === "auto") {
        setIsDarkMode(deviceTheme === "dark");
      } else {
        setIsDarkMode(preference === "dark");
      }
      AsyncStorage.setItem("theme_preference", preference).catch(() => {});
    },
    [deviceTheme],
  );

  return (
    <ThemeContext.Provider
      value={{
        theme,
        isDarkMode,
        toggleTheme,
        setTheme,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};
