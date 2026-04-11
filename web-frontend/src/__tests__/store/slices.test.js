import authReducer, {
  loginFailure,
  loginStart,
  loginSuccess,
  logout,
  updateUser,
} from "../../store/slices/authSlice";
import portfolioReducer, {
  addHistoricalDataPoint,
  fetchPortfolioFailure,
  fetchPortfolioStart,
  fetchPortfolioSuccess,
  updatePortfolioValue,
} from "../../store/slices/portfolioSlice";
import uiReducer, {
  addNotification,
  clearErrors,
  clearNotifications,
  removeNotification,
  setDrawerOpen,
  toggleDrawer,
  toggleModal,
} from "../../store/slices/uiSlice";

// ─── Auth Slice ───────────────────────────────────────────────────────────────
describe("authSlice", () => {
  const initialState = {
    isAuthenticated: false,
    user: null,
    token: null,
    loading: false,
    error: null,
  };

  it("returns the initial state", () => {
    expect(authReducer(undefined, { type: "@@INIT" })).toEqual(initialState);
  });

  it("handles loginStart", () => {
    const state = authReducer(initialState, loginStart());
    expect(state.loading).toBe(true);
    expect(state.error).toBeNull();
  });

  it("handles loginSuccess", () => {
    const payload = { user: { email: "test@example.com" }, token: "abc123" };
    const state = authReducer(initialState, loginSuccess(payload));
    expect(state.isAuthenticated).toBe(true);
    expect(state.user).toEqual(payload.user);
    expect(state.token).toBe("abc123");
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
  });

  it("handles loginFailure", () => {
    const startState = authReducer(initialState, loginStart());
    const state = authReducer(startState, loginFailure("Invalid credentials"));
    expect(state.loading).toBe(false);
    expect(state.error).toBe("Invalid credentials");
    expect(state.isAuthenticated).toBe(false);
  });

  it("handles logout", () => {
    const loggedIn = {
      isAuthenticated: true,
      user: { email: "test@example.com" },
      token: "abc123",
      loading: false,
      error: null,
    };
    const state = authReducer(loggedIn, logout());
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
  });

  it("handles updateUser", () => {
    const loggedIn = {
      isAuthenticated: true,
      user: { email: "test@example.com", firstName: "John" },
      token: "abc123",
      loading: false,
      error: null,
    };
    const state = authReducer(loggedIn, updateUser({ firstName: "Jane" }));
    expect(state.user.firstName).toBe("Jane");
    expect(state.user.email).toBe("test@example.com");
  });
});

// ─── UI Slice ─────────────────────────────────────────────────────────────────
describe("uiSlice", () => {
  const initialState = {
    drawerOpen: false,
    darkMode: true,
    notifications: [],
    currentView: "dashboard",
    loading: {
      global: false,
      portfolio: false,
      strategies: false,
      trades: false,
    },
    errors: { global: null, portfolio: null, strategies: null, trades: null },
    modals: {
      settings: false,
      createStrategy: false,
      strategyDetails: false,
      deposit: false,
      withdraw: false,
    },
  };

  it("returns the initial state", () => {
    const state = uiReducer(undefined, { type: "@@INIT" });
    expect(state.drawerOpen).toBe(false);
    expect(state.notifications).toEqual([]);
  });

  it("handles toggleDrawer", () => {
    let state = uiReducer(initialState, toggleDrawer());
    expect(state.drawerOpen).toBe(true);
    state = uiReducer(state, toggleDrawer());
    expect(state.drawerOpen).toBe(false);
  });

  it("handles setDrawerOpen", () => {
    const state = uiReducer(initialState, setDrawerOpen(true));
    expect(state.drawerOpen).toBe(true);
  });

  it("handles addNotification", () => {
    const state = uiReducer(
      initialState,
      addNotification({ message: "Trade executed", type: "success" }),
    );
    expect(state.notifications).toHaveLength(1);
    expect(state.notifications[0].message).toBe("Trade executed");
    expect(state.notifications[0].type).toBe("success");
    expect(state.notifications[0].id).toBeDefined();
  });

  it("handles removeNotification", () => {
    let state = uiReducer(
      initialState,
      addNotification({ message: "Test", type: "info" }),
    );
    const id = state.notifications[0].id;
    state = uiReducer(state, removeNotification(id));
    expect(state.notifications).toHaveLength(0);
  });

  it("handles clearNotifications", () => {
    let state = uiReducer(
      initialState,
      addNotification({ message: "First", type: "info" }),
    );
    state = uiReducer(
      state,
      addNotification({ message: "Second", type: "info" }),
    );
    state = uiReducer(state, clearNotifications());
    expect(state.notifications).toHaveLength(0);
  });

  it("handles toggleModal with explicit value", () => {
    const state = uiReducer(
      initialState,
      toggleModal({ modal: "deposit", value: true }),
    );
    expect(state.modals.deposit).toBe(true);
  });

  it("handles toggleModal without value (toggles)", () => {
    let state = uiReducer(
      initialState,
      toggleModal({ modal: "createStrategy" }),
    );
    expect(state.modals.createStrategy).toBe(true);
    state = uiReducer(state, toggleModal({ modal: "createStrategy" }));
    expect(state.modals.createStrategy).toBe(false);
  });

  it("handles clearErrors", () => {
    const withErrors = {
      ...initialState,
      errors: {
        global: "error",
        portfolio: "err2",
        strategies: null,
        trades: null,
      },
    };
    const state = uiReducer(withErrors, clearErrors());
    expect(Object.values(state.errors).every((v) => v === null)).toBe(true);
  });
});

// ─── Portfolio Slice ──────────────────────────────────────────────────────────
describe("portfolioSlice", () => {
  it("handles fetchPortfolioStart", () => {
    const state = portfolioReducer(undefined, fetchPortfolioStart());
    expect(state.loading).toBe(true);
    expect(state.error).toBeNull();
  });

  it("handles fetchPortfolioSuccess", () => {
    const payload = {
      portfolioValue: 150000,
      dailyChange: 5000,
      percentChange: 3.45,
      historicalData: [{ name: "Jan", value: 100000 }],
      assets: [],
    };
    const state = portfolioReducer(undefined, fetchPortfolioSuccess(payload));
    expect(state.portfolioValue).toBe(150000);
    expect(state.loading).toBe(false);
  });

  it("handles fetchPortfolioFailure", () => {
    const state = portfolioReducer(
      undefined,
      fetchPortfolioFailure("Network error"),
    );
    expect(state.loading).toBe(false);
    expect(state.error).toBe("Network error");
  });

  it("handles updatePortfolioValue", () => {
    const state = portfolioReducer(
      undefined,
      updatePortfolioValue({
        value: 120000,
        dailyChange: 1000,
        percentChange: 0.84,
      }),
    );
    expect(state.portfolioValue).toBe(120000);
    expect(state.dailyChange).toBe(1000);
  });

  it("handles addHistoricalDataPoint", () => {
    const initial = portfolioReducer(undefined, { type: "@@INIT" });
    const initialLength = initial.historicalData.length;
    const state = portfolioReducer(
      initial,
      addHistoricalDataPoint({ name: "Aug", value: 12000 }),
    );
    expect(state.historicalData).toHaveLength(initialLength + 1);
    expect(state.historicalData[state.historicalData.length - 1]).toEqual({
      name: "Aug",
      value: 12000,
    });
  });
});
