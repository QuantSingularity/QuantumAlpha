import { act, renderHook } from "@testing-library/react";
import { useDebounce } from "../../hooks/useDebounce";

describe("useDebounce", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("returns the initial value immediately", () => {
    const { result } = renderHook(() => useDebounce("hello", 500));
    expect(result.current).toBe("hello");
  });

  it("does not update the value before the delay", () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: "hello", delay: 500 } },
    );

    rerender({ value: "world", delay: 500 });
    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current).toBe("hello");
  });

  it("updates the value after the delay has passed", () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: "hello", delay: 500 } },
    );

    rerender({ value: "world", delay: 500 });
    act(() => {
      jest.advanceTimersByTime(500);
    });

    expect(result.current).toBe("world");
  });

  it("resets the timer when value changes before delay elapses", () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: "hello", delay: 500 } },
    );

    rerender({ value: "world", delay: 500 });
    act(() => {
      jest.advanceTimersByTime(300);
    });

    rerender({ value: "final", delay: 500 });
    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current).toBe("hello");

    act(() => {
      jest.advanceTimersByTime(200);
    });
    expect(result.current).toBe("final");
  });

  it("uses default delay of 500ms when none provided", () => {
    const { result, rerender } = renderHook(({ value }) => useDebounce(value), {
      initialProps: { value: "initial" },
    });

    rerender({ value: "updated" });
    act(() => {
      jest.advanceTimersByTime(499);
    });
    expect(result.current).toBe("initial");

    act(() => {
      jest.advanceTimersByTime(1);
    });
    expect(result.current).toBe("updated");
  });

  it("handles numeric values", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 0 } },
    );

    rerender({ value: 42 });
    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current).toBe(42);
  });

  it("handles object values", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: { count: 0 } } },
    );

    rerender({ value: { count: 1 } });
    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current).toEqual({ count: 1 });
  });

  it("cleans up timer on unmount", () => {
    const clearTimeoutSpy = jest.spyOn(global, "clearTimeout");
    const { unmount, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: "hello" } },
    );

    rerender({ value: "world" });
    unmount();

    expect(clearTimeoutSpy).toHaveBeenCalled();
    clearTimeoutSpy.mockRestore();
  });
});
