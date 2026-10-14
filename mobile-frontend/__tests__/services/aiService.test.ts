import {
  aiService,
  normalizeForecast,
  normalizeSignal,
} from "../../src/services/aiService";
import { aiAPI } from "../../src/services/api";

jest.mock("../../src/services/api", () => ({
  aiAPI: {
    getModels: jest.fn(),
    predict: jest.fn(),
    generateSignals: jest.fn(),
    getModelHealth: jest.fn(),
    getRLRecommendation: jest.fn(),
  },
}));

const mocked = aiAPI as jest.Mocked<typeof aiAPI>;

describe("aiService", () => {
  beforeEach(() => jest.clearAllMocks());

  it("normalizes signals and coerces unknown types to hold", () => {
    expect(
      normalizeSignal({
        symbol: "AAPL",
        type: "weird",
        strength: "0.4",
        price: "10",
      }).type,
    ).toBe("hold");
    expect(
      normalizeSignal({
        symbol: "AAPL",
        type: "buy",
        strength: "0.4",
        price: "10",
      }).strength,
    ).toBe(0.4);
  });

  it("normalizes forecasts", () => {
    const forecast = normalizeForecast({
      symbol: "AAPL",
      model_id: "m1",
      latest_price: 100,
      horizon: 1,
      prediction: {
        direction: "bullish",
        expected_return: 0.01,
        change_percent: 1,
        probability_up: 0.7,
        confidence: 0.4,
      },
      predictions: [
        { step: 1, timestamp: "t", value: 101, lower: 99, upper: 103 },
      ],
    });
    expect(forecast.points[0].upper).toBe(103);
    expect(forecast.direction).toBe("bullish");
  });

  it("unwraps enveloped responses and filters trained models", async () => {
    mocked.getModels.mockResolvedValue({
      data: {
        success: true,
        data: [
          { id: "a", status: "trained" },
          { id: "b", status: "created" },
        ],
      },
    } as any);
    const models = await aiService.getTrainedModels();
    expect(models.map((m: any) => m.id)).toEqual(["a"]);
  });

  it("sends the expected signal request", async () => {
    mocked.generateSignals.mockResolvedValue({
      data: { signals: [], errors: [] },
    } as any);
    await aiService.generateSignals({
      symbols: ["AAPL"],
      modelId: "m1",
      strategy: "ensemble",
    });
    expect(mocked.generateSignals).toHaveBeenCalledWith({
      symbols: ["AAPL"],
      strategy: "ensemble",
      timeframe: "1d",
      model_id: "m1",
    });
  });

  it("wraps upstream errors with status", async () => {
    mocked.predict.mockRejectedValue({
      response: {
        status: 409,
        data: { error: "Model is not trained", code: "MODEL_NOT_TRAINED" },
      },
    });
    await expect(
      aiService.predict({ modelId: "m", symbol: "AAPL" }),
    ).rejects.toMatchObject({
      status: 409,
      code: "MODEL_NOT_TRAINED",
    });
  });
});
