import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
import { Text, TouchableOpacity } from "react-native";
import { ThemeProvider, useTheme } from "../../src/context/ThemeContext";

jest.mock("@react-native-async-storage/async-storage", () =>
  require("@react-native-async-storage/async-storage/jest/async-storage-mock"),
);

const ThemeConsumer = () => {
  const { theme, isDarkMode, toggleTheme } = useTheme();
  return (
    <>
      <Text testID="mode">{isDarkMode ? "dark" : "light"}</Text>
      <Text testID="primary">{theme.primary}</Text>
      <Text testID="surface">{theme.surface}</Text>
      <Text testID="textSecondary">{theme.textSecondary}</Text>
      <TouchableOpacity testID="toggle" onPress={toggleTheme} />
    </>
  );
};

describe("ThemeContext", () => {
  it("provides light theme by default", () => {
    const { getByTestId } = render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );

    expect(getByTestId("mode").children[0]).toBe("light");
  });

  it("includes required theme properties", () => {
    const { getByTestId } = render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );

    expect(getByTestId("primary").children[0]).toBe("#1aff92");
    expect(getByTestId("surface")).toBeTruthy();
    expect(getByTestId("textSecondary")).toBeTruthy();
  });

  it("toggles theme on toggleTheme call", () => {
    const { getByTestId } = render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );

    expect(getByTestId("mode").children[0]).toBe("light");
    fireEvent.press(getByTestId("toggle"));
    expect(getByTestId("mode").children[0]).toBe("dark");
    fireEvent.press(getByTestId("toggle"));
    expect(getByTestId("mode").children[0]).toBe("light");
  });
});
