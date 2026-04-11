import { fireEvent, render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import NotificationPanel from "../../components/common/NotificationPanel";
import uiReducer, { addNotification } from "../../store/slices/uiSlice";

const makeStore = (preloadedState = {}) =>
  configureStore({
    reducer: { ui: uiReducer },
    preloadedState,
  });

const renderWithStore = (store) =>
  render(
    <Provider store={store}>
      <NotificationPanel />
    </Provider>,
  );

describe("NotificationPanel", () => {
  it("renders nothing when there are no notifications", () => {
    const store = makeStore({ ui: { notifications: [] } });
    const { container } = renderWithStore(store);
    // No Snackbar elements present
    expect(container.querySelectorAll('[role="alert"]')).toHaveLength(0);
  });

  it("renders a notification when one is added", () => {
    const store = makeStore({
      ui: {
        notifications: [
          { id: 1, message: "Trade executed successfully", type: "success" },
        ],
      },
    });
    renderWithStore(store);
    expect(screen.getByText("Trade executed successfully")).toBeInTheDocument();
  });

  it("renders multiple notifications", () => {
    const store = makeStore({
      ui: {
        notifications: [
          { id: 1, message: "First notification", type: "info" },
          { id: 2, message: "Second notification", type: "warning" },
        ],
      },
    });
    renderWithStore(store);
    expect(screen.getByText("First notification")).toBeInTheDocument();
    expect(screen.getByText("Second notification")).toBeInTheDocument();
  });

  it("removes a notification when close is clicked", () => {
    const store = makeStore({
      ui: {
        notifications: [
          { id: 1, message: "Dismissible notification", type: "info" },
        ],
      },
    });
    renderWithStore(store);

    const closeButton = screen.getByTitle("Close");
    fireEvent.click(closeButton);

    // After dispatch, notification should be removed from store
    const state = store.getState();
    expect(state.ui.notifications).toHaveLength(0);
  });

  it("dispatches addNotification correctly via store", () => {
    const store = makeStore({ ui: { notifications: [] } });
    store.dispatch(addNotification({ message: "New alert", type: "error" }));
    const state = store.getState();
    expect(state.ui.notifications).toHaveLength(1);
    expect(state.ui.notifications[0].message).toBe("New alert");
    expect(state.ui.notifications[0].type).toBe("error");
    expect(state.ui.notifications[0].id).toBeDefined();
  });
});
