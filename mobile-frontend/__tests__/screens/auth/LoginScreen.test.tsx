import React from "react";
import { render, fireEvent, waitFor } from "@testing-library/react-native";
import LoginScreen from "../../../src/screens/auth/LoginScreen";
import { ThemeProvider } from "../../../src/context/ThemeContext";
import { AuthProvider } from "../../../src/context/AuthContext";

jest.mock("@react-native-async-storage/async-storage", () =>
  require("@react-native-async-storage/async-storage/jest/async-storage-mock"),
);

jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({
    navigate: jest.fn(),
    goBack: jest.fn(),
  }),
}));

const Wrapper = ({ children }: { children: React.ReactNode }) => (
  <ThemeProvider>
    <AuthProvider>{children}</AuthProvider>
  </ThemeProvider>
);

describe("LoginScreen", () => {
  it("renders email and password inputs", () => {
    const { getByPlaceholderText } = render(<LoginScreen />, {
      wrapper: Wrapper,
    });

    expect(getByPlaceholderText("you@example.com")).toBeTruthy();
    expect(getByPlaceholderText("••••••••")).toBeTruthy();
  });

  it("renders Sign in button", () => {
    const { getByText } = render(<LoginScreen />, { wrapper: Wrapper });
    expect(getByText("Sign in")).toBeTruthy();
  });

  it("shows error when email is empty", async () => {
    const { getByText } = render(<LoginScreen />, {
      wrapper: Wrapper,
    });

    fireEvent.press(getByText("Sign in"));

    await waitFor(() => {
      expect(getByText("Email and password are required")).toBeTruthy();
    });
  });

  it("shows error when password is empty", async () => {
    const { getByPlaceholderText, getByText } = render(<LoginScreen />, {
      wrapper: Wrapper,
    });

    fireEvent.changeText(
      getByPlaceholderText("you@example.com"),
      "user@example.com",
    );
    fireEvent.press(getByText("Sign in"));

    await waitFor(() => {
      expect(getByText("Email and password are required")).toBeTruthy();
    });
  });

  it("navigates to Register screen", () => {
    const navigate = jest.fn();
    jest
      .spyOn(require("@react-navigation/native"), "useNavigation")
      .mockReturnValue({ navigate });

    const { getByText } = render(<LoginScreen />, { wrapper: Wrapper });

    fireEvent.press(getByText("Create an account"));
    expect(navigate).toHaveBeenCalledWith("Register");
  });

  it("navigates to ForgotPassword screen", () => {
    const navigate = jest.fn();
    jest
      .spyOn(require("@react-navigation/native"), "useNavigation")
      .mockReturnValue({ navigate });

    const { getByText } = render(<LoginScreen />, { wrapper: Wrapper });

    fireEvent.press(getByText("Forgot password?"));
    expect(navigate).toHaveBeenCalledWith("ForgotPassword");
  });
});
