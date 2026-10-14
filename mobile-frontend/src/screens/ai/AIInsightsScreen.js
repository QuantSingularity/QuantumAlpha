import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useTheme } from "../../context/ThemeContext";
import aiService from "../../services/aiService";

const STRATEGIES = ["prediction", "technical", "ensemble"];

const formatPercent = (value) =>
  `${value >= 0 ? "+" : ""}${(value * 100).toFixed(2)}%`;

const AIInsightsScreen = () => {
  const { theme } = useTheme();
  const [models, setModels] = useState([]);
  const [modelId, setModelId] = useState(null);
  const [strategy, setStrategy] = useState("technical");
  const [symbolsText, setSymbolsText] = useState("AAPL, MSFT");
  const [signals, setSignals] = useState([]);
  const [forecast, setForecast] = useState(null);
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState(null);

  const symbols = useMemo(
    () =>
      symbolsText
        .split(",")
        .map((s) => s.trim().toUpperCase())
        .filter(Boolean)
        .slice(0, 10),
    [symbolsText],
  );

  const loadModels = useCallback(async () => {
    try {
      const trained = await aiService.getTrainedModels();
      setModels(trained);
      setModelId((current) => current || (trained[0] ? trained[0].id : null));
      setMessage(null);
    } catch (error) {
      setMessage(error.message);
    }
  }, []);

  useEffect(() => {
    loadModels();
  }, [loadModels]);

  const needsModel = strategy !== "technical";

  const run = useCallback(async () => {
    if (!symbols.length) {
      setMessage("Enter at least one symbol");
      return;
    }
    if (needsModel && !modelId) {
      setMessage("Select a trained model for this strategy");
      return;
    }
    setLoading(true);
    setMessage(null);
    try {
      const result = await aiService.generateSignals({
        symbols,
        modelId,
        strategy,
      });
      setSignals(result.signals);
      setErrors(result.errors);
      if (modelId && symbols[0]) {
        try {
          setForecast(await aiService.predict({ modelId, symbol: symbols[0] }));
        } catch (error) {
          setForecast(null);
        }
      }
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }, [symbols, modelId, strategy, needsModel]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadModels();
    setRefreshing(false);
  }, [loadModels]);

  const colorFor = (type) =>
    type === "buy"
      ? theme.success
      : type === "sell"
        ? theme.error
        : theme.textSecondary;

  const styles = useMemo(() => createStyles(theme), [theme]);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          tintColor={theme.primary}
        />
      }
    >
      <View style={styles.card}>
        <Text style={styles.label}>Symbols</Text>
        <TextInput
          style={styles.input}
          value={symbolsText}
          onChangeText={setSymbolsText}
          autoCapitalize="characters"
          autoCorrect={false}
          placeholder="AAPL, MSFT"
          placeholderTextColor={theme.textSecondary}
        />
        <Text style={styles.label}>Strategy</Text>
        <View style={styles.row}>
          {STRATEGIES.map((item) => (
            <TouchableOpacity
              key={item}
              style={[styles.chip, strategy === item && styles.chipActive]}
              onPress={() => setStrategy(item)}
            >
              <Text
                style={[
                  styles.chipText,
                  strategy === item && styles.chipTextActive,
                ]}
              >
                {item}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
        <Text style={styles.label}>Model</Text>
        {models.length === 0 ? (
          <Text style={styles.muted}>No trained models available</Text>
        ) : (
          <View style={styles.row}>
            {models.map((model) => (
              <TouchableOpacity
                key={model.id}
                style={[styles.chip, modelId === model.id && styles.chipActive]}
                onPress={() => setModelId(model.id)}
              >
                <Text
                  style={[
                    styles.chipText,
                    modelId === model.id && styles.chipTextActive,
                  ]}
                >
                  {model.name}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        )}
        <TouchableOpacity
          style={styles.button}
          onPress={run}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Text style={styles.buttonText}>Generate Signals</Text>
          )}
        </TouchableOpacity>
        {message ? <Text style={styles.error}>{message}</Text> : null}
      </View>

      {signals.map((signal) => (
        <View key={`${signal.symbol}-${signal.strategy}`} style={styles.card}>
          <View style={styles.spread}>
            <Text style={styles.title}>{signal.symbol}</Text>
            <Text style={[styles.badge, { color: colorFor(signal.type) }]}>
              {signal.type.toUpperCase()}
            </Text>
          </View>
          <Text style={styles.muted}>
            Strength {(signal.strength * 100).toFixed(0)}% at $
            {signal.price.toFixed(2)}
          </Text>
          {signal.expectedReturn !== null ? (
            <Text style={styles.muted}>
              Expected return {formatPercent(signal.expectedReturn)}
            </Text>
          ) : null}
        </View>
      ))}

      {errors.map((item) => (
        <Text key={item.symbol} style={styles.error}>
          {item.symbol}: {item.error}
        </Text>
      ))}

      {forecast ? (
        <View style={styles.card}>
          <Text style={styles.title}>{forecast.symbol} forecast</Text>
          <Text style={styles.muted}>
            {forecast.direction} with{" "}
            {(forecast.probabilityUp * 100).toFixed(0)}% probability of a rise
          </Text>
          {forecast.points.map((point) => (
            <View key={point.step} style={styles.spread}>
              <Text style={styles.muted}>Step {point.step}</Text>
              <Text style={styles.value}>
                ${point.value.toFixed(2)} ({point.lower.toFixed(2)} to{" "}
                {point.upper.toFixed(2)})
              </Text>
            </View>
          ))}
        </View>
      ) : null}
    </ScrollView>
  );
};

const createStyles = (theme) =>
  StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background },
    content: { padding: 16, paddingBottom: 40 },
    card: {
      backgroundColor: theme.card,
      borderRadius: 14,
      padding: 16,
      marginBottom: 12,
      borderWidth: 1,
      borderColor: theme.border,
    },
    label: {
      color: theme.textSecondary,
      fontSize: 12,
      marginTop: 8,
      marginBottom: 6,
    },
    input: {
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 10,
      color: theme.text,
      paddingHorizontal: 12,
      paddingVertical: 10,
    },
    row: { flexDirection: "row", flexWrap: "wrap" },
    chip: {
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 16,
      paddingHorizontal: 12,
      paddingVertical: 6,
      marginRight: 8,
      marginBottom: 8,
    },
    chipActive: { backgroundColor: theme.primary, borderColor: theme.primary },
    chipText: { color: theme.text, fontSize: 13 },
    chipTextActive: { color: "#FFFFFF" },
    button: {
      backgroundColor: theme.primary,
      borderRadius: 12,
      paddingVertical: 12,
      alignItems: "center",
      marginTop: 12,
    },
    buttonText: { color: "#FFFFFF", fontWeight: "700" },
    title: { color: theme.text, fontSize: 18, fontWeight: "700" },
    badge: { fontSize: 14, fontWeight: "800" },
    spread: {
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
      marginTop: 4,
    },
    muted: { color: theme.textSecondary, fontSize: 13, marginTop: 2 },
    value: { color: theme.text, fontSize: 13 },
    error: { color: theme.error, fontSize: 13, marginTop: 8 },
  });

export default AIInsightsScreen;
