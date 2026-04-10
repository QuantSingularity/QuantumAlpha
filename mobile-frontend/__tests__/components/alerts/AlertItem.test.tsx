import React from "react";
import { render, fireEvent, waitFor } from "@testing-library/react-native";
import AlertItem from "../../../src/components/alerts/AlertItem";
import { ThemeProvider } from "../../../src/context/ThemeContext";

const mockAlert = {
  id: "1",
  type: "TRADE_SIGNAL",
  priority: "high",
  title: "Price Alert",
  message: "BTC reached $50,000",
  timestamp: new Date().toISOString(),
  read: false,
};

const Wrapper = ({ children }: { children: React.ReactNode }) => (
  <ThemeProvider>{children}</ThemeProvider>
);

describe("AlertItem", () => {
  it("renders title and message correctly", () => {
    const { getByText } = render(<AlertItem alert={mockAlert} />, {
      wrapper: Wrapper,
    });

    expect(getByText("Price Alert")).toBeTruthy();
    expect(getByText("BTC reached $50,000")).toBeTruthy();
  });

  it("calls onPress when the item is pressed", () => {
    const onPress = jest.fn();
    const { getByText } = render(
      <AlertItem alert={mockAlert} onPress={onPress} />,
      { wrapper: Wrapper },
    );

    fireEvent.press(getByText("Price Alert"));
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it("shows dismiss button when onDismiss is provided", () => {
    const onDismiss = jest.fn();
    const { getByTestId } = render(
      <AlertItem alert={mockAlert} onDismiss={onDismiss} />,
      { wrapper: Wrapper },
    );

    expect(getByTestId("dismiss-button")).toBeTruthy();
  });

  it("does not show dismiss button when onDismiss is not provided", () => {
    const { queryByTestId } = render(<AlertItem alert={mockAlert} />, {
      wrapper: Wrapper,
    });

    expect(queryByTestId("dismiss-button")).toBeNull();
  });

  it("renders correctly with isRead field (type alias)", () => {
    const readAlert = { ...mockAlert, isRead: true, read: undefined };
    const { getByText } = render(<AlertItem alert={readAlert} />, {
      wrapper: Wrapper,
    });
    expect(getByText("Price Alert")).toBeTruthy();
  });

  it("renders correctly with createdAt field (type alias)", () => {
    const { createdAt: _removed, ...base } = {
      ...mockAlert,
      timestamp: undefined,
    };
    const alert = { ...base, createdAt: new Date().toISOString() };
    const { getByText } = render(<AlertItem alert={alert} />, {
      wrapper: Wrapper,
    });
    expect(getByText("Price Alert")).toBeTruthy();
  });

  it("renders all priority levels without crashing", () => {
    const priorities = ["low", "medium", "high", "critical", undefined];
    priorities.forEach((priority) => {
      const { getByText } = render(
        <AlertItem alert={{ ...mockAlert, priority }} />,
        { wrapper: Wrapper },
      );
      expect(getByText("Price Alert")).toBeTruthy();
    });
  });
});
