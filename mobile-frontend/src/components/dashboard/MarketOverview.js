import React from "react";
import { View, Text, StyleSheet, ActivityIndicator } from "react-native";
import { Dimensions } from "react-native";
import { LineChart } from "react-native-chart-kit";
import Icon from "react-native-vector-icons/MaterialCommunityIcons";
import { useTheme } from "../../context/ThemeContext";
import { SPACING } from "../../constants";

const MarketOverview = ({ data, loading }) => {
  const { theme, isDarkMode } = useTheme();
  const screenWidth = Dimensions.get("window").width;

  const fallbackData = {
    indices: [
      {
        name: "S&P 500",
        value: "5,328.42",
        changePercent: 0.82,
        direction: "up",
      },
      {
        name: "NASDAQ",
        value: "16,742.39",
        changePercent: 1.14,
        direction: "up",
      },
      {
        name: "DOW",
        value: "38,996.35",
        changePercent: -0.13,
        direction: "down",
      },
    ],
    chartData: {
      labels: ["9AM", "10AM", "11AM", "12PM", "1PM", "2PM", "3PM", "4PM"],
      datasets: [{ data: [5280, 5290, 5310, 5300, 5320, 5315, 5325, 5328] }],
    },
  };

  const marketData = data || fallbackData;

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.card }]}>
        <Text style={[styles.title, { color: theme.text }]}>
          Market Overview
        </Text>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={theme.primary} />
        </View>
      </View>
    );
  }

  const chartConfig = {
    backgroundColor: theme.chartBackground,
    backgroundGradientFrom: theme.chartBackgroundGradientFrom,
    backgroundGradientTo: theme.chartBackgroundGradientTo,
    decimalPlaces: 0,
    color: (opacity = 1) => `rgba(26, 255, 146, ${opacity})`,
    labelColor: (opacity = 1) =>
      isDarkMode
        ? `rgba(255, 255, 255, ${opacity})`
        : `rgba(0, 0, 0, ${opacity})`,
    style: { borderRadius: 16 },
    propsForDots: { r: "4", strokeWidth: "2", stroke: theme.primary },
  };

  const formatIndexValue = (index) => {
    if (typeof index.value === "number") {
      return index.value.toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
    }
    return index.value;
  };

  const formatChange = (index) => {
    const pct = index.changePercent ?? index.change;
    if (pct == null) return "";
    const sign = pct >= 0 ? "+" : "";
    return `${sign}${Number(pct).toFixed(2)}%`;
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.card }]}>
      <Text style={[styles.title, { color: theme.text }]}>Market Overview</Text>

      <View style={styles.indicesContainer}>
        {(marketData.indices || []).map((index, i) => (
          <View key={i} style={styles.indexItem}>
            <Text style={[styles.indexName, { color: theme.textSecondary }]}>
              {index.name}
            </Text>
            <Text style={[styles.indexValue, { color: theme.text }]}>
              {formatIndexValue(index)}
            </Text>
            <View style={styles.changeRow}>
              <Icon
                name={
                  index.direction === "up" ? "trending-up" : "trending-down"
                }
                size={12}
                color={index.direction === "up" ? theme.success : theme.error}
              />
              <Text
                style={[
                  styles.indexChange,
                  {
                    color:
                      index.direction === "up" ? theme.success : theme.error,
                  },
                ]}
              >
                {formatChange(index)}
              </Text>
            </View>
          </View>
        ))}
      </View>

      {marketData.chartData && (
        <LineChart
          data={marketData.chartData}
          width={screenWidth - 72}
          height={160}
          chartConfig={chartConfig}
          bezier
          style={styles.chart}
          withDots={false}
          withInnerLines={false}
          withOuterLines={false}
          withVerticalLines={false}
          withHorizontalLines={true}
          withShadow={true}
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 16,
    padding: SPACING.MD,
    marginTop: SPACING.MD,
    marginHorizontal: SPACING.MD,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
    elevation: 4,
  },
  title: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: SPACING.MD,
  },
  loadingContainer: {
    height: 80,
    justifyContent: "center",
    alignItems: "center",
  },
  indicesContainer: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: SPACING.MD,
  },
  indexItem: {
    alignItems: "center",
    flex: 1,
  },
  indexName: {
    fontSize: 11,
    marginBottom: 4,
    textAlign: "center",
  },
  indexValue: {
    fontSize: 14,
    fontWeight: "bold",
    marginBottom: 4,
    textAlign: "center",
  },
  changeRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  indexChange: {
    fontSize: 12,
    fontWeight: "600",
    marginLeft: 2,
  },
  chart: {
    marginTop: SPACING.SM,
    borderRadius: 12,
    alignSelf: "center",
  },
});

export default MarketOverview;
