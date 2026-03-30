import {
  formatCompactNumber,
  formatCurrency,
  formatDate,
  formatNumber,
  formatPercentage,
  formatRelativeTime,
} from "../../utils/format";

describe("Format Utilities", () => {
  describe("formatCurrency", () => {
    it("formats positive numbers correctly", () => {
      expect(formatCurrency(1234.56)).toBe("$1,234.56");
    });

    it("formats negative numbers correctly", () => {
      expect(formatCurrency(-1234.56)).toBe("-$1,234.56");
    });

    it("handles zero", () => {
      expect(formatCurrency(0)).toBe("$0.00");
    });

    it("handles null and undefined", () => {
      expect(formatCurrency(null)).toBe("$0.00");
      expect(formatCurrency(undefined)).toBe("$0.00");
    });
  });

  describe("formatPercentage", () => {
    it("formats positive percentages correctly", () => {
      expect(formatPercentage(12.34)).toBe("12.34%");
    });

    it("formats negative percentages correctly", () => {
      expect(formatPercentage(-5.67)).toBe("-5.67%");
    });

    it("handles custom decimal places", () => {
      expect(formatPercentage(12.3456, 3)).toBe("12.346%");
    });

    it("handles null and undefined", () => {
      expect(formatPercentage(null)).toBe("0.00%");
      expect(formatPercentage(undefined)).toBe("0.00%");
    });
  });

  describe("formatCompactNumber", () => {
    it("formats thousands correctly", () => {
      expect(formatCompactNumber(1500)).toBe("1.50K");
    });

    it("formats millions correctly", () => {
      expect(formatCompactNumber(2500000)).toBe("2.50M");
    });

    it("formats billions correctly", () => {
      expect(formatCompactNumber(3500000000)).toBe("3.50B");
    });

    it("formats small numbers correctly", () => {
      expect(formatCompactNumber(123.45)).toBe("123.45");
    });

    it("handles negative numbers", () => {
      expect(formatCompactNumber(-1500)).toBe("-1.50K");
    });
  });

  describe("formatNumber", () => {
    it("formats numbers with thousand separators", () => {
      expect(formatNumber(1234567.89)).toBe("1,234,567.89");
    });

    it("formats with custom decimals", () => {
      expect(formatNumber(1234.5678, 3)).toBe("1,234.568");
    });
  });

  describe("formatDate", () => {
    it("formats date in short format", () => {
      const date = new Date("2024-06-15T12:00:00Z");
      const result = formatDate(date, "short");
      expect(result).toContain("Jun");
      expect(result).toContain("2024");
    });

    it("handles invalid dates", () => {
      expect(formatDate("invalid")).toBe("");
      expect(formatDate(null)).toBe("");
    });
  });

  describe("formatRelativeTime", () => {
    it('formats recent times as "just now"', () => {
      const now = new Date();
      expect(formatRelativeTime(now)).toBe("just now");
    });

    it("formats minutes ago", () => {
      const date = new Date(Date.now() - 5 * 60 * 1000); // 5 minutes ago
      expect(formatRelativeTime(date)).toBe("5 minutes ago");
    });

    it("handles invalid dates", () => {
      expect(formatRelativeTime(null)).toBe("");
      expect(formatRelativeTime("invalid")).toBe("");
    });
  });
});
