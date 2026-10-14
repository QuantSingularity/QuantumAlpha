import { aiAPI } from "./api";

const SIGNAL_TYPES = new Set(["buy", "sell", "hold"]);

const normalizeError = (error) => {
  const message =
    error?.response?.data?.error?.message ||
    error?.response?.data?.error ||
    error?.message ||
    "AI service unavailable";
  const wrapped = new Error(
    typeof message === "string" ? message : "AI service unavailable",
  );
  wrapped.status = error?.response?.status || 0;
  wrapped.code = error?.response?.data?.code || null;
  return wrapped;
};

const unwrap = (response) => {
  const body =
    response && response.data !== undefined ? response.data : response;
  return body && body.success !== undefined && body.data !== undefined
    ? body.data
    : body;
};

export const normalizeSignal = (signal) => ({
  symbol: signal.symbol,
  type: SIGNAL_TYPES.has(signal.type) ? signal.type : "hold",
  strength: Number(signal.strength) || 0,
  price: Number(signal.price) || 0,
  strategy: signal.strategy || "prediction",
  modelId: signal.model_id || null,
  generatedAt: signal.generated_at || null,
  expectedReturn: signal.prediction
    ? Number(signal.prediction.expected_return) || 0
    : null,
  direction: signal.prediction ? signal.prediction.direction : null,
});

export const normalizeForecast = (forecast) => ({
  symbol: forecast.symbol,
  modelId: forecast.model_id,
  latestPrice: Number(forecast.latest_price) || 0,
  asOf: forecast.as_of,
  horizon: forecast.horizon,
  direction: forecast.prediction.direction,
  expectedReturn: Number(forecast.prediction.expected_return) || 0,
  changePercent: Number(forecast.prediction.change_percent) || 0,
  probabilityUp: Number(forecast.prediction.probability_up) || 0,
  confidence: Number(forecast.prediction.confidence) || 0,
  points: (forecast.predictions || []).map((p) => ({
    step: p.step,
    timestamp: p.timestamp,
    value: Number(p.value),
    lower: Number(p.lower),
    upper: Number(p.upper),
  })),
});

export const aiService = {
  async getModels(params) {
    try {
      const models = unwrap(await aiAPI.getModels(params));
      return Array.isArray(models) ? models : [];
    } catch (error) {
      throw normalizeError(error);
    }
  },

  async getTrainedModels() {
    const models = await aiService.getModels();
    return models.filter((m) => m.status === "trained");
  },

  async predict({ modelId, symbol, timeframe = "1d", horizon }) {
    try {
      const body = { model_id: modelId, symbol, timeframe };
      if (horizon) body.horizon = horizon;
      return normalizeForecast(unwrap(await aiAPI.predict(body)));
    } catch (error) {
      throw normalizeError(error);
    }
  },

  async generateSignals({
    symbols,
    modelId,
    strategy = "prediction",
    timeframe = "1d",
  }) {
    try {
      const body = { symbols, strategy, timeframe };
      if (modelId) body.model_id = modelId;
      const data = unwrap(await aiAPI.generateSignals(body));
      return {
        signals: (data.signals || []).map(normalizeSignal),
        errors: data.errors || [],
      };
    } catch (error) {
      throw normalizeError(error);
    }
  },

  async getModelHealth(modelId, symbol) {
    try {
      return unwrap(
        await aiAPI.getModelHealth(modelId, symbol ? { symbol } : undefined),
      );
    } catch (error) {
      throw normalizeError(error);
    }
  },

  async getRLRecommendation({ modelId, symbol, timeframe = "1d" }) {
    try {
      const data = unwrap(
        await aiAPI.getRLRecommendation({
          model_id: modelId,
          symbol,
          timeframe,
        }),
      );
      return {
        action: data.recommendation.action,
        targetExposure: data.recommendation.target_exposure,
        price: data.recommendation.price,
        returnPct: Number(data.return) * 100,
      };
    } catch (error) {
      throw normalizeError(error);
    }
  },
};

export default aiService;
