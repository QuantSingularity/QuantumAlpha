import React, { useState, useEffect, useRef } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
  Animated,
  RefreshControl,
} from "react-native";
import { LineChart, PieChart } from "react-native-chart-kit";
import Icon from "react-native-vector-icons/MaterialCommunityIcons";
import { useNavigation } from "@react-navigation/native";
import { useTheme } from "../../context/ThemeContext";
import { portfolioService } from "../../services/portfolioService";

const PortfolioScreen = () => {
  const navigation = useNavigation();
  const { theme, isDarkMode } = useTheme();

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [portfolioData, setPortfolioData] = useState(null);
  const [performanceData, setPerformanceData] = useState(null);
  const [assetAllocation, setAssetAllocation] = useState([]);
  const [holdings, setHoldings] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState("1M");

  // useRef prevents Animated values from being recreated on every render
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(50)).current;

  const screenWidth = Dimensions.get("window").width;

  useEffect(() => {
    loadPortfolioData();

    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(translateY, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const loadPortfolioData = async () => {
    try {
      setLoading(true);

      const [portfolioSummary, performance, allocation, holdingsData] =
        await Promise.all([
          portfolioService.getPortfolioSummary(),
          portfolioService.getPerformanceHistory(selectedPeriod),
          portfolioService.getAssetAllocation(),
          portfolioService.getHoldings(),
        ]);

      setPortfolioData(portfolioSummary);
      setPerformanceData(performance);
      setAssetAllocation(allocation);
      setHoldings(holdingsData);
    } catch (error) {
      console.error("Error loading portfolio data:", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadPortfolioData();
  };

  const handlePeriodChange = async (period) => {
    setSelectedPeriod(period);
    try {
      const performance = await portfolioService.getPerformanceHistory(period);
      setPerformanceData(performance);
    } catch (error) {
      console.error("Error loading performance data:", error);
    }
  };

  if (loading && !refreshing) {
    return (
      <View
        style={[styles.loadingContainer, { backgroundColor: theme.background }]}
      >
        <ActivityIndicator size="large" color={theme.primary} />
        <Text style={[styles.loadingText, { color: theme.text }]}>
          Loading portfolio data...
        </Text>
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
    propsForDots: { r: "6", strokeWidth: "2", stroke: theme.primary },
  };

  const pieColors = [
    "#1aff92",
    "#0a84ff",
    "#ffcc00",
    "#ff453a",
    "#32d74b",
    "#bf5af2",
    "#ff9f0a",
  ];

  const pieChartData = assetAllocation.map((item, index) => ({
    name: item.name,
    value: item.percentage,
    color: pieColors[index % pieColors.length],
    legendFontColor: theme.text,
    legendFontSize: 12,
  }));

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      {portfolioData && (
        <Animated.View
          style={[
            styles.header,
            {
              backgroundColor: theme.card,
              opacity: fadeAnim,
              transform: [{ translateY }],
            },
          ]}
        >
          <Text style={[styles.headerTitle, { color: theme.textSecondary }]}>
            Portfolio
          </Text>
          <Text style={[styles.portfolioValue, { color: theme.text }]}>
            ${portfolioData.totalValue.toLocaleString()}
          </Text>
          <View style={styles.changeContainer}>
            <Icon
              name={
                portfolioData.dailyChange >= 0 ? "trending-up" : "trending-down"
              }
              size={18}
              color={
                portfolioData.dailyChange >= 0 ? theme.success : theme.error
              }
            />
            <Text
              style={[
                styles.changeText,
                {
                  color:
                    portfolioData.dailyChange >= 0
                      ? theme.success
                      : theme.error,
                  marginLeft: 4,
                },
              ]}
            >
              {portfolioData.dailyChange >= 0 ? "+" : ""}
              {portfolioData.dailyChange.toLocaleString()} (
              {portfolioData.percentChange}%)
            </Text>
            <Text style={[styles.changeLabel, { color: theme.textSecondary }]}>
              {" "}
              Today
            </Text>
          </View>
        </Animated.View>
      )}

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={theme.primary}
            colors={[theme.primary]}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        {performanceData && (
          <View style={[styles.card, { backgroundColor: theme.card }]}>
            <View style={styles.cardHeader}>
              <Text style={[styles.cardTitle, { color: theme.text }]}>
                Performance
              </Text>
              <View style={styles.periodSelector}>
                {["1D", "1W", "1M", "3M", "1Y", "ALL"].map((period) => (
                  <TouchableOpacity
                    key={period}
                    style={[
                      styles.periodButton,
                      selectedPeriod === period && [
                        styles.activePeriodButton,
                        { backgroundColor: theme.primary },
                      ],
                    ]}
                    onPress={() => handlePeriodChange(period)}
                  >
                    <Text
                      style={[
                        styles.periodButtonText,
                        {
                          color:
                            selectedPeriod === period ? "#FFFFFF" : theme.text,
                        },
                      ]}
                    >
                      {period}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <LineChart
              data={{
                labels: performanceData.labels,
                datasets: [{ data: performanceData.values }],
              }}
              width={screenWidth - 72}
              height={200}
              chartConfig={chartConfig}
              bezier
              style={styles.chart}
              withShadow={true}
            />
          </View>
        )}

        {assetAllocation.length > 0 && (
          <View style={[styles.card, { backgroundColor: theme.card }]}>
            <Text style={[styles.cardTitle, { color: theme.text }]}>
              Asset Allocation
            </Text>

            <View style={styles.pieChartContainer}>
              <PieChart
                data={pieChartData}
                width={screenWidth - 72}
                height={200}
                chartConfig={chartConfig}
                accessor="value"
                backgroundColor="transparent"
                paddingLeft="15"
                absolute={false}
              />
            </View>

            <View style={styles.allocationLegend}>
              {assetAllocation.map((item, index) => (
                <View key={index} style={styles.legendItem}>
                  <View
                    style={[
                      styles.legendColor,
                      { backgroundColor: pieChartData[index]?.color },
                    ]}
                  />
                  <Text style={[styles.legendText, { color: theme.text }]}>
                    {item.name}: {item.percentage}% ($
                    {item.value.toLocaleString()})
                  </Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {holdings.length > 0 && (
          <View style={[styles.card, { backgroundColor: theme.card }]}>
            <View style={styles.cardHeader}>
              <Text style={[styles.cardTitle, { color: theme.text }]}>
                Holdings
              </Text>
            </View>

            <View
              style={[
                styles.holdingsHeader,
                { borderBottomColor: theme.border },
              ]}
            >
              <Text
                style={[
                  styles.holdingsHeaderText,
                  { color: theme.textSecondary },
                ]}
              >
                Asset
              </Text>
              <Text
                style={[
                  styles.holdingsHeaderText,
                  { color: theme.textSecondary },
                ]}
              >
                Value
              </Text>
              <Text
                style={[
                  styles.holdingsHeaderText,
                  { color: theme.textSecondary },
                ]}
              >
                Change
              </Text>
            </View>

            {holdings.map((holding, index) => (
              <TouchableOpacity
                key={holding.symbol || index}
                style={[
                  styles.holdingItem,
                  index < holdings.length - 1 && {
                    borderBottomWidth: 1,
                    borderBottomColor: theme.border,
                  },
                ]}
                onPress={() =>
                  navigation.navigate("AssetDetail", {
                    symbol: holding.symbol,
                  })
                }
              >
                <View style={styles.holdingInfo}>
                  <Text style={[styles.holdingSymbol, { color: theme.text }]}>
                    {holding.symbol}
                  </Text>
                  <Text
                    style={[styles.holdingName, { color: theme.textSecondary }]}
                  >
                    {holding.name}
                  </Text>
                </View>

                <View style={styles.holdingValue}>
                  <Text
                    style={[styles.holdingValueText, { color: theme.text }]}
                  >
                    ${holding.value.toLocaleString()}
                  </Text>
                  <Text
                    style={[
                      styles.holdingQuantity,
                      { color: theme.textSecondary },
                    ]}
                  >
                    {holding.quantity} @ ${holding.price}
                  </Text>
                </View>

                <View style={styles.holdingChange}>
                  <Text
                    style={[
                      styles.holdingChangeText,
                      {
                        color:
                          holding.change >= 0 ? theme.success : theme.error,
                      },
                    ]}
                  >
                    {holding.change >= 0 ? "+" : ""}
                    {holding.change}%
                  </Text>
                </View>
              </TouchableOpacity>
            ))}
          </View>
        )}

        <View style={[styles.card, { backgroundColor: theme.card }]}>
          <Text style={[styles.cardTitle, { color: theme.text }]}>
            Quick Actions
          </Text>

          <View style={styles.actionButtons}>
            {[
              {
                icon: "bank-transfer-in",
                label: "Deposit",
                color: theme.primary,
                route: "TradeTab",
              },
              {
                icon: "bank-transfer-out",
                label: "Withdraw",
                color: theme.error,
                route: "TradeTab",
              },
              {
                icon: "swap-horizontal",
                label: "Trade",
                color: theme.info,
                route: "TradeTab",
              },
              {
                icon: "strategy",
                label: "Strategies",
                color: theme.warning,
                route: "StrategyTab",
              },
            ].map((action) => (
              <TouchableOpacity
                key={action.label}
                style={[
                  styles.actionButton,
                  { backgroundColor: action.color + "20" },
                ]}
                onPress={() => navigation.navigate(action.route)}
              >
                <Icon name={action.icon} size={24} color={action.color} />
                <Text style={[styles.actionButtonText, { color: theme.text }]}>
                  {action.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  loadingContainer: { flex: 1, justifyContent: "center", alignItems: "center" },
  loadingText: { marginTop: 10, fontSize: 16 },
  header: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(0,0,0,0.08)",
  },
  headerTitle: { fontSize: 14, marginBottom: 4 },
  portfolioValue: { fontSize: 34, fontWeight: "bold", marginTop: 2 },
  changeContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 6,
  },
  changeText: { fontSize: 16, fontWeight: "600" },
  changeLabel: { fontSize: 13 },
  scrollContent: { padding: 16, paddingBottom: 48 },
  card: {
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 3,
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  cardTitle: { fontSize: 18, fontWeight: "bold" },
  periodSelector: {
    flexDirection: "row",
    backgroundColor: "rgba(0,0,0,0.05)",
    borderRadius: 16,
    padding: 2,
  },
  periodButton: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 14 },
  activePeriodButton: { elevation: 2 },
  periodButtonText: { fontSize: 12, fontWeight: "500" },
  chart: { borderRadius: 16, marginTop: 8, alignSelf: "center" },
  pieChartContainer: { alignItems: "center", marginVertical: 8 },
  allocationLegend: { marginTop: 8 },
  legendItem: { flexDirection: "row", alignItems: "center", marginBottom: 8 },
  legendColor: { width: 12, height: 12, borderRadius: 6, marginRight: 8 },
  legendText: { fontSize: 14 },
  holdingsHeader: {
    flexDirection: "row",
    paddingBottom: 10,
    borderBottomWidth: 1,
    marginBottom: 4,
  },
  holdingsHeaderText: { fontSize: 12, fontWeight: "600", flex: 1 },
  holdingItem: { flexDirection: "row", paddingVertical: 12 },
  holdingInfo: { flex: 2 },
  holdingSymbol: { fontSize: 15, fontWeight: "600" },
  holdingName: { fontSize: 12, marginTop: 2 },
  holdingValue: { flex: 2, alignItems: "flex-end" },
  holdingValueText: { fontSize: 15, fontWeight: "500" },
  holdingQuantity: { fontSize: 11, marginTop: 2 },
  holdingChange: { flex: 1, alignItems: "flex-end" },
  holdingChangeText: { fontSize: 15, fontWeight: "600" },
  actionButtons: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    marginTop: 12,
  },
  actionButton: {
    width: "48%",
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
    marginBottom: 10,
  },
  actionButtonText: { fontSize: 14, fontWeight: "500", marginTop: 8 },
});

export default PortfolioScreen;
