import { portfolioService } from "../../src/services/portfolioService";

describe("portfolioService", () => {
  describe("getPortfolioSummary", () => {
    it("returns portfolio summary with required fields", async () => {
      const result = await portfolioService.getPortfolioSummary();

      expect(result).toBeDefined();
      expect(typeof result.totalValue).toBe("number");
      expect(typeof result.dailyChange).toBe("number");
      expect(typeof result.percentChange).toBe("number");
      expect(Array.isArray(result.assets)).toBe(true);
    });

    it("returns positive total value", async () => {
      const result = await portfolioService.getPortfolioSummary();
      expect(result.totalValue).toBeGreaterThan(0);
    });
  });

  describe("getPerformanceHistory", () => {
    const periods = ["1D", "1W", "1M", "3M", "1Y", "ALL"];

    periods.forEach((period) => {
      it(`returns data for period ${period}`, async () => {
        const result = await portfolioService.getPerformanceHistory(period);

        expect(result).toBeDefined();
        expect(Array.isArray(result.labels)).toBe(true);
        expect(Array.isArray(result.values)).toBe(true);
        expect(result.labels.length).toBeGreaterThan(0);
        expect(result.values.length).toBe(result.labels.length);
        expect(result.period).toBe(period);
      });
    });

    it("falls back to 1M data for unknown period", async () => {
      const result = await portfolioService.getPerformanceHistory("UNKNOWN");
      expect(Array.isArray(result.labels)).toBe(true);
      expect(result.labels.length).toBeGreaterThan(0);
    });
  });

  describe("getAssetAllocation", () => {
    it("returns array with percentage and value fields", async () => {
      const result = await portfolioService.getAssetAllocation();

      expect(Array.isArray(result)).toBe(true);
      expect(result.length).toBeGreaterThan(0);

      result.forEach((item: any) => {
        expect(typeof item.name).toBe("string");
        expect(typeof item.percentage).toBe("number");
        expect(typeof item.value).toBe("number");
      });
    });

    it("percentages sum to approximately 100", async () => {
      const result = await portfolioService.getAssetAllocation();
      const total = result.reduce(
        (sum: number, item: any) => sum + item.percentage,
        0,
      );
      expect(Math.round(total)).toBe(100);
    });
  });

  describe("getHoldings", () => {
    it("returns array of holdings with required fields", async () => {
      const result = await portfolioService.getHoldings();

      expect(Array.isArray(result)).toBe(true);
      expect(result.length).toBeGreaterThan(0);

      result.forEach((item: any) => {
        expect(typeof item.symbol).toBe("string");
        expect(typeof item.name).toBe("string");
        expect(typeof item.quantity).toBe("number");
        expect(typeof item.price).toBe("number");
        expect(typeof item.value).toBe("number");
        expect(typeof item.change).toBe("number");
      });
    });
  });

  describe("getTransactionHistory", () => {
    it("returns paginated transaction list", async () => {
      const result = await portfolioService.getTransactionHistory(1, 20);

      expect(result).toBeDefined();
      expect(Array.isArray(result.transactions)).toBe(true);
      expect(result.pagination).toBeDefined();
      expect(typeof result.pagination.page).toBe("number");
      expect(typeof result.pagination.total).toBe("number");
    });
  });
});
