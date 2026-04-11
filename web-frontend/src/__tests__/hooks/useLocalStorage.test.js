import { act, renderHook } from "@testing-library/react";
import { useLocalStorage } from "../../hooks/useLocalStorage";

describe("useLocalStorage", () => {
  beforeEach(() => {
    window.localStorage.clear();
    jest.spyOn(Storage.prototype, "setItem");
    jest.spyOn(Storage.prototype, "getItem");
    jest.spyOn(Storage.prototype, "removeItem");
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("returns the initial value when localStorage is empty", () => {
    const { result } = renderHook(() => useLocalStorage("testKey", "default"));
    expect(result.current[0]).toBe("default");
  });

  it("returns stored value when it exists in localStorage", () => {
    window.localStorage.setItem("testKey", JSON.stringify("storedValue"));
    const { result } = renderHook(() => useLocalStorage("testKey", "default"));
    expect(result.current[0]).toBe("storedValue");
  });

  it("stores a new value in localStorage", () => {
    const { result } = renderHook(() => useLocalStorage("testKey", "default"));

    act(() => {
      result.current[1]("newValue");
    });

    expect(result.current[0]).toBe("newValue");
    expect(window.localStorage.getItem("testKey")).toBe(
      JSON.stringify("newValue"),
    );
  });

  it("supports functional updates", () => {
    const { result } = renderHook(() => useLocalStorage("counter", 0));

    act(() => {
      result.current[1]((prev) => prev + 1);
    });

    expect(result.current[0]).toBe(1);
  });

  it("stores objects correctly", () => {
    const { result } = renderHook(() =>
      useLocalStorage("obj", { name: "test" }),
    );

    act(() => {
      result.current[1]({ name: "updated", count: 5 });
    });

    expect(result.current[0]).toEqual({ name: "updated", count: 5 });
  });

  it("removes the value from localStorage", () => {
    window.localStorage.setItem("testKey", JSON.stringify("storedValue"));
    const { result } = renderHook(() => useLocalStorage("testKey", "default"));

    act(() => {
      result.current[2](); // removeValue
    });

    expect(result.current[0]).toBe("default");
    expect(window.localStorage.getItem("testKey")).toBeNull();
  });

  it("handles invalid JSON in localStorage gracefully", () => {
    window.localStorage.setItem("testKey", "not-valid-json{{{");
    const { result } = renderHook(() => useLocalStorage("testKey", "fallback"));
    expect(result.current[0]).toBe("fallback");
  });

  it("handles localStorage.setItem errors gracefully", () => {
    Storage.prototype.setItem.mockImplementation(() => {
      throw new Error("QuotaExceededError");
    });
    const consoleSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});

    const { result } = renderHook(() => useLocalStorage("testKey", "default"));

    expect(() => {
      act(() => {
        result.current[1]("newValue");
      });
    }).not.toThrow();

    consoleSpy.mockRestore();
  });
});
