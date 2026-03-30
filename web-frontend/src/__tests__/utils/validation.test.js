import {
  isInRange,
  isRequired,
  isValidEmail,
  isValidPhone,
  isValidStockSymbol,
  validatePassword,
} from "../../utils/validation";

describe("Validation Utilities", () => {
  describe("isValidEmail", () => {
    it("validates correct email addresses", () => {
      expect(isValidEmail("test@example.com")).toBe(true);
      expect(isValidEmail("user.name@domain.co.uk")).toBe(true);
    });

    it("rejects invalid email addresses", () => {
      expect(isValidEmail("invalid")).toBe(false);
      expect(isValidEmail("test@")).toBe(false);
      expect(isValidEmail("@example.com")).toBe(false);
      expect(isValidEmail("test@.com")).toBe(false);
    });
  });

  describe("validatePassword", () => {
    it("validates strong passwords", () => {
      const result = validatePassword("Password123!");
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it("rejects weak passwords", () => {
      const result = validatePassword("weak");
      expect(result.isValid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });

    it("requires minimum length", () => {
      const result = validatePassword("Pass1!");
      expect(result.isValid).toBe(false);
      expect(result.errors.some((e) => e.includes("8 characters"))).toBe(true);
    });

    it("requires uppercase letters", () => {
      const result = validatePassword("password123!");
      expect(result.isValid).toBe(false);
      expect(result.errors.some((e) => e.includes("uppercase"))).toBe(true);
    });

    it("requires lowercase letters", () => {
      const result = validatePassword("PASSWORD123!");
      expect(result.isValid).toBe(false);
      expect(result.errors.some((e) => e.includes("lowercase"))).toBe(true);
    });

    it("requires numbers", () => {
      const result = validatePassword("Password!");
      expect(result.isValid).toBe(false);
      expect(result.errors.some((e) => e.includes("number"))).toBe(true);
    });

    it("requires special characters", () => {
      const result = validatePassword("Password123");
      expect(result.isValid).toBe(false);
      expect(result.errors.some((e) => e.includes("special character"))).toBe(
        true,
      );
    });
  });

  describe("isValidStockSymbol", () => {
    it("validates correct stock symbols", () => {
      expect(isValidStockSymbol("AAPL")).toBe(true);
      expect(isValidStockSymbol("GOOGL")).toBe(true);
      expect(isValidStockSymbol("MSFT")).toBe(true);
    });

    it("handles lowercase symbols", () => {
      expect(isValidStockSymbol("aapl")).toBe(true);
    });

    it("rejects invalid symbols", () => {
      expect(isValidStockSymbol("TOOLONG")).toBe(false);
      expect(isValidStockSymbol("AA-PL")).toBe(false);
      expect(isValidStockSymbol("123")).toBe(false);
      expect(isValidStockSymbol("")).toBe(false);
    });
  });

  describe("isValidPhone", () => {
    it("validates correct phone numbers", () => {
      expect(isValidPhone("+1234567890")).toBe(true);
      expect(isValidPhone("(123) 456-7890")).toBe(true);
      expect(isValidPhone("123-456-7890")).toBe(true);
    });

    it("rejects invalid phone numbers", () => {
      expect(isValidPhone("abc")).toBe(false);
      expect(isValidPhone("123")).toBe(false);
      expect(isValidPhone("")).toBe(false);
    });
  });

  describe("isInRange", () => {
    it("validates numbers in range", () => {
      expect(isInRange(50, 0, 100)).toBe(true);
      expect(isInRange(0, 0, 100)).toBe(true);
      expect(isInRange(100, 0, 100)).toBe(true);
    });

    it("rejects numbers out of range", () => {
      expect(isInRange(-1, 0, 100)).toBe(false);
      expect(isInRange(101, 0, 100)).toBe(false);
    });

    it("handles invalid numbers", () => {
      expect(isInRange("abc", 0, 100)).toBe(false);
    });
  });

  describe("isRequired", () => {
    it("validates non-empty values", () => {
      expect(isRequired("test")).toBe(true);
      expect(isRequired(123)).toBe(true);
      expect(isRequired(true)).toBe(true);
    });

    it("rejects empty values", () => {
      expect(isRequired("")).toBe(false);
      expect(isRequired("   ")).toBe(false);
      expect(isRequired(null)).toBe(false);
      expect(isRequired(undefined)).toBe(false);
    });
  });
});
