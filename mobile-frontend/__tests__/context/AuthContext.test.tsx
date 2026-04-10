import React from "react";
import { render, act, waitFor } from "@testing-library/react-native";
import { Text } from "react-native";
import { AuthProvider, useAuth } from "../../src/context/AuthContext";

jest.mock("@react-native-async-storage/async-storage", () =>
  require("@react-native-async-storage/async-storage/jest/async-storage-mock"),
);

const TestConsumer = () => {
  const { isAuthenticated, loading, user } = useAuth();
  return (
    <>
      <Text testID="loading">{loading ? "loading" : "ready"}</Text>
      <Text testID="auth">{isAuthenticated ? "authenticated" : "guest"}</Text>
      <Text testID="user">{user ? user.email : "no-user"}</Text>
    </>
  );
};

describe("AuthContext", () => {
  it("starts in loading state", () => {
    const { getByTestId } = render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );
    expect(getByTestId("loading").children[0]).toBe("loading");
  });

  it("resolves to guest state when no stored credentials", async () => {
    const { getByTestId } = render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(getByTestId("loading").children[0]).toBe("ready");
    });

    expect(getByTestId("auth").children[0]).toBe("guest");
    expect(getByTestId("user").children[0]).toBe("no-user");
  });

  it("provides login, logout, and register methods", () => {
    const TestMethods = () => {
      const ctx = useAuth();
      return (
        <>
          <Text testID="has-login">{typeof ctx.login}</Text>
          <Text testID="has-logout">{typeof ctx.logout}</Text>
          <Text testID="has-register">{typeof ctx.register}</Text>
        </>
      );
    };

    const { getByTestId } = render(
      <AuthProvider>
        <TestMethods />
      </AuthProvider>,
    );

    expect(getByTestId("has-login").children[0]).toBe("function");
    expect(getByTestId("has-logout").children[0]).toBe("function");
    expect(getByTestId("has-register").children[0]).toBe("function");
  });
});
