import { alertService } from "../../src/services/alertService";

describe("alertService", () => {
  describe("getRecentAlerts", () => {
    it("returns array of alerts", async () => {
      const result = await alertService.getRecentAlerts(5);
      expect(Array.isArray(result)).toBe(true);
    });

    it("respects limit parameter", async () => {
      const result = await alertService.getRecentAlerts(3);
      expect(result.length).toBeLessThanOrEqual(3);
    });

    it("each alert has required fields", async () => {
      const result = await alertService.getRecentAlerts(5);
      result.forEach((alert: any) => {
        expect(typeof alert.id).toBe("string");
        expect(typeof alert.title).toBe("string");
        expect(typeof alert.message).toBe("string");
        expect(typeof alert.type).toBe("string");
        expect(typeof alert.priority).toBe("string");
        expect(typeof alert.timestamp).toBe("string");
      });
    });
  });

  describe("getAllAlerts", () => {
    it("returns paginated result", async () => {
      const result = await alertService.getAllAlerts(1, 10);
      expect(Array.isArray(result.alerts)).toBe(true);
      expect(result.pagination).toBeDefined();
      expect(result.pagination.page).toBe(1);
    });
  });

  describe("markAsRead", () => {
    it("returns success response", async () => {
      const result = await alertService.markAsRead("alert1");
      expect(result.success).toBe(true);
    });
  });

  describe("markAllAsRead", () => {
    it("returns success response", async () => {
      const result = await alertService.markAllAsRead();
      expect(result.success).toBe(true);
    });
  });

  describe("deleteAlert", () => {
    it("returns success response", async () => {
      const result = await alertService.deleteAlert("alert1");
      expect(result.success).toBe(true);
    });
  });

  describe("subscribeToAlerts", () => {
    it("returns object with unsubscribe method", () => {
      const subscription = alertService.subscribeToAlerts(jest.fn());
      expect(typeof subscription.unsubscribe).toBe("function");
      subscription.unsubscribe();
    });

    it("calls subscriber when alert is triggered", () => {
      const callback = jest.fn();
      alertService.subscribeToAlerts(callback);
      alertService.simulateNewAlert();
      expect(callback).toHaveBeenCalledTimes(1);
      const alert = callback.mock.calls[0][0];
      expect(typeof alert.id).toBe("string");
      expect(typeof alert.title).toBe("string");
    });

    it("unsubscribe removes the callback", () => {
      const callback = jest.fn();
      const sub = alertService.subscribeToAlerts(callback);
      sub.unsubscribe();
      alertService.simulateNewAlert();
      expect(callback).not.toHaveBeenCalled();
    });
  });
});
