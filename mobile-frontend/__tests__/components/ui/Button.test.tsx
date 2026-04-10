import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
import Button from "../../../src/components/ui/Button";
import { ThemeProvider } from "../../../src/context/ThemeContext";

const Wrapper = ({ children }: { children: React.ReactNode }) => (
  <ThemeProvider>{children}</ThemeProvider>
);

describe("Button", () => {
  it("renders title text", () => {
    const { getByText } = render(
      <Button title="Test Button" onPress={jest.fn()} />,
      { wrapper: Wrapper },
    );
    expect(getByText("Test Button")).toBeTruthy();
  });

  it("calls onPress when tapped", () => {
    const onPress = jest.fn();
    const { getByText } = render(<Button title="Tap Me" onPress={onPress} />, {
      wrapper: Wrapper,
    });
    fireEvent.press(getByText("Tap Me"));
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it("does not call onPress when disabled", () => {
    const onPress = jest.fn();
    const { getByText } = render(
      <Button title="Disabled" onPress={onPress} disabled />,
      { wrapper: Wrapper },
    );
    fireEvent.press(getByText("Disabled"));
    expect(onPress).not.toHaveBeenCalled();
  });

  it("shows ActivityIndicator when loading", () => {
    const { queryByText, UNSAFE_getByType } = render(
      <Button title="Loading" onPress={jest.fn()} loading />,
      { wrapper: Wrapper },
    );
    expect(queryByText("Loading")).toBeNull();
  });

  it("renders all variants without crashing", () => {
    const variants = [
      "primary",
      "secondary",
      "outline",
      "ghost",
      "danger",
    ] as const;
    variants.forEach((variant) => {
      const { getByText } = render(
        <Button title={variant} onPress={jest.fn()} variant={variant} />,
        { wrapper: Wrapper },
      );
      expect(getByText(variant)).toBeTruthy();
    });
  });

  it("renders all sizes without crashing", () => {
    const sizes = ["small", "medium", "large"] as const;
    sizes.forEach((size) => {
      const { getByText } = render(
        <Button title={size} onPress={jest.fn()} size={size} />,
        { wrapper: Wrapper },
      );
      expect(getByText(size)).toBeTruthy();
    });
  });
});
