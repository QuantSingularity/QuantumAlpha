import React, { useState, useEffect, useCallback } from "react";
import {
  SafeAreaView,
  ScrollView,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  Dimensions,
} from "react-native";
import Icon from "react-native-vector-icons/MaterialCommunityIcons";
import { useNavigation } from "@react-navigation/native";
import * as Animatable from "react-native-animatable";
import HapticFeedback from "react-native-haptic-feedback";

import { useTheme } from "../../context/ThemeContext";
import { useAlert } from "../../context/AlertContext";
import { useApiQuery } from "../../hooks";
import { portfolioService } from "../../services/portfolioService";
import { strategyService } from "../../services/strategyService";
import { alertService } from "../../services/alertService";
import { marketService } from "../../services/marketService";

import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import {
  LoadingSpinner,
  SkeletonLoader,
} from "../../components/ui/LoadingSpinner";
import Chart from "../../components/charts/Chart";
import StrategyCard from "../../components/dashboard/StrategyCard";
import AlertItem from "../../components/alerts/AlertItem";
import MarketOverview from "../../components/dashboard/MarketOverview";
import QuickActions from "../../components/dashboard/QuickActions";
import NewsWidget from "../../components/dashboard/NewsWidget";
import WatchlistWidget from "../../components/dashboard/WatchlistWidget";

import { formatCurrency, formatPercentage } from "../../utils";
import { COLORS, SPACING } from "../../constants";
import { Strategy, Alert, NewsArticle } from "../../types";

const DashboardScreen = () => {
  const navigation = useNavigation<any>();
  const { theme } = useTheme();
  const { addAlert } = useAlert();

  const [refreshing, setRefreshing] = useState(false);
  const [selectedTimeframe, setSelectedTimeframe] = useState("1D");

  const {
    data: portfolioData,
    isLoading: portfolioLoading,
    refetch: refetchPortfolio,
  } = useApiQuery(
    ["portfolio", "summary"],
    () => portfolioService.getPortfolioSummary(),
    { refetchInterval: 30000 },
  );

  const {
    data: performanceData,
    isLoading: performanceLoading,
    refetch: refetchPerformance,
  } = useApiQuery(
    ["portfolio", "performance", selectedTimeframe],
    () => portfolioService.getPerformanceHistory(selectedTimeframe),
    { refetchInterval: 60000 },
  );

  const {
    data: strategies,
    isLoading: strategiesLoading,
    refetch: refetchStrategies,
  } = useApiQuery(
    ["strategies", "active"],
    () => strategyService.getActiveStrategies(),
    { refetchInterval: 300000 },
  );

  const {
    data: recentAlerts,
    isLoading: alertsLoading,
    refetch: refetchAlerts,
  } = useApiQuery(["alerts", "recent"], () => alertService.getRecentAlerts(5), {
    refetchInterval: 60000,
  });

  const { data: marketOverview, isLoading: marketLoading } = useApiQuery(
    ["market", "overview"],
    () => marketService.getMarketOverview(),
    { refetchInterval: 30000 },
  );

  const { data: newsData, isLoading: newsLoading } = useApiQuery(
    ["news", "latest"],
    () => marketService.getLatestNews(5),
    { refetchInterval: 300000 },
  );

  useEffect(() => {
    const alertListener = alertService.subscribeToAlerts((newAlert: Alert) => {
      addAlert(newAlert);
      HapticFeedback.trigger("notificationSuccess");
    });

    return () => {
      alertListener.unsubscribe();
    };
  }, [addAlert]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    HapticFeedback.trigger("impactLight");

    try {
      await Promise.all([
        refetchPortfolio(),
        refetchPerformance(),
        refetchStrategies(),
        refetchAlerts(),
      ]);
    } catch (error) {
      console.error("Error refreshing dashboard:", error);
    } finally {
      setRefreshing(false);
    }
  }, [refetchPortfolio, refetchPerformance, refetchStrategies, refetchAlerts]);

  const navigateToStrategy = useCallback(
    (strategy: Strategy) => {
      HapticFeedback.trigger("impactLight");
      navigation.navigate("StrategyDetail", {
        id: strategy.id,
        name: strategy.name,
      });
    },
    [navigation],
  );

  const navigateToAlerts = useCallback(() => {
    HapticFeedback.trigger("impactLight");
    navigation.navigate("AlertsTab");
  }, [navigation]);

  const navigateToNotifications = useCallback(() => {
    HapticFeedback.trigger("impactLight");
    navigation.navigate("Notifications");
  }, [navigation]);

  const handleTimeframeChange = useCallback((timeframe: string) => {
    setSelectedTimeframe(timeframe);
    HapticFeedback.trigger("impactLight");
  }, []);

  const renderHeader = () => (
    <Card
      variant="elevated"
      padding="medium"
      margin="none"
      style={styles.header}
    >
      <View style={styles.headerContent}>
        <View>
          <Text style={[styles.title, { color: theme.text }]}>
            QuantumAlpha
          </Text>
          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
            Portfolio Dashboard
          </Text>
        </View>
        <View style={styles.headerIcons}>
          <TouchableOpacity
            style={styles.iconButton}
            onPress={navigateToNotifications}
          >
            <Icon name="bell" size={24} color={theme.text} />
            {recentAlerts && recentAlerts.length > 0 && (
              <View style={[styles.badge, { backgroundColor: theme.error }]}>
                <Text style={styles.badgeText}>
                  {recentAlerts.length > 9 ? "9+" : recentAlerts.length}
                </Text>
              </View>
            )}
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.iconButton}
            onPress={() => navigation.openDrawer()}
          >
            <Icon name="menu" size={24} color={theme.text} />
          </TouchableOpacity>
        </View>
      </View>
    </Card>
  );

  const renderPortfolioSummary = () => {
    if (portfolioLoading) {
      return <SkeletonLoader type="card" style={styles.portfolioSummary} />;
    }

    if (!portfolioData) return null;

    // portfolioService returns percentChange (not dailyChangePercent)
    const isPositive = (portfolioData.dailyChange ?? 0) >= 0;

    return (
      <Animatable.View animation="fadeInUp" delay={100}>
        <Card
          variant="elevated"
          padding="large"
          margin="medium"
          style={styles.portfolioSummary}
        >
          <Text style={[styles.portfolioLabel, { color: theme.textSecondary }]}>
            Total Portfolio Value
          </Text>
          <Text style={[styles.portfolioValue, { color: theme.text }]}>
            {formatCurrency(portfolioData.totalValue)}
          </Text>
          <View style={styles.changeContainer}>
            <Icon
              name={isPositive ? "trending-up" : "trending-down"}
              size={20}
              color={isPositive ? COLORS.CHART.POSITIVE : COLORS.CHART.NEGATIVE}
            />
            <Text
              style={[
                styles.changeText,
                {
                  color: isPositive
                    ? COLORS.CHART.POSITIVE
                    : COLORS.CHART.NEGATIVE,
                  marginLeft: SPACING.XS,
                },
              ]}
            >
              {formatCurrency(portfolioData.dailyChange ?? 0)} (
              {formatPercentage(portfolioData.percentChange ?? 0)})
            </Text>
          </View>
          <Text style={[styles.changeLabel, { color: theme.textSecondary }]}>
            Today's Change
          </Text>
        </Card>
      </Animatable.View>
    );
  };

  const renderPerformanceChart = () => {
    if (performanceLoading) {
      return <SkeletonLoader type="chart" style={styles.chartContainer} />;
    }

    if (!performanceData) return null;

    const chartData = {
      labels: performanceData.labels,
      datasets: [{ data: performanceData.values }],
    };

    return (
      <Animatable.View animation="fadeInUp" delay={200}>
        <Chart
          type="line"
          data={chartData}
          title="Portfolio Performance"
          height={220}
          timeframe={selectedTimeframe}
          onTimeframeChange={handleTimeframeChange}
          interactive
          style={styles.chartContainer}
        />
      </Animatable.View>
    );
  };

  const renderQuickActions = () => (
    <Animatable.View animation="fadeInUp" delay={300}>
      <QuickActions />
    </Animatable.View>
  );

  const renderMarketOverview = () => (
    <Animatable.View animation="fadeInUp" delay={400}>
      <MarketOverview data={marketOverview} loading={marketLoading} />
    </Animatable.View>
  );

  const renderStrategies = () => {
    if (strategiesLoading) {
      return (
        <SkeletonLoader
          type="list"
          count={3}
          style={styles.strategiesContainer}
        />
      );
    }

    return (
      <Animatable.View animation="fadeInUp" delay={500}>
        <View style={styles.strategiesContainer}>
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>
              Active Strategies
            </Text>
            <TouchableOpacity
              onPress={() => navigation.navigate("StrategyTab")}
            >
              <Text style={[styles.seeAllText, { color: theme.primary }]}>
                See All
              </Text>
            </TouchableOpacity>
          </View>

          {strategies && strategies.length > 0 ? (
            strategies.slice(0, 3).map((strategy: Strategy, index: number) => (
              <Animatable.View
                key={strategy.id}
                animation="fadeInRight"
                delay={600 + index * 100}
              >
                <StrategyCard
                  strategy={strategy}
                  onPress={() => navigateToStrategy(strategy)}
                />
              </Animatable.View>
            ))
          ) : (
            <Card variant="outlined" padding="large" margin="small">
              <View style={styles.emptyState}>
                <Icon name="strategy" size={40} color={theme.text + "60"} />
                <Text style={[styles.emptyStateText, { color: theme.text }]}>
                  No active strategies
                </Text>
                <Button
                  title="Explore Strategies"
                  onPress={() => navigation.navigate("StrategyTab")}
                  variant="outline"
                  size="small"
                  style={{ marginTop: SPACING.MD }}
                />
              </View>
            </Card>
          )}
        </View>
      </Animatable.View>
    );
  };

  const renderWatchlist = () => (
    <Animatable.View animation="fadeInUp" delay={600}>
      <WatchlistWidget />
    </Animatable.View>
  );

  const renderNews = () => (
    <Animatable.View animation="fadeInUp" delay={700}>
      <NewsWidget data={newsData} loading={newsLoading} />
    </Animatable.View>
  );

  const renderAlerts = () => {
    if (alertsLoading) {
      return (
        <SkeletonLoader type="list" count={3} style={styles.alertsContainer} />
      );
    }

    return (
      <Animatable.View animation="fadeInUp" delay={800}>
        <View style={styles.alertsContainer}>
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>
              Recent Alerts
            </Text>
            <TouchableOpacity onPress={navigateToAlerts}>
              <Text style={[styles.seeAllText, { color: theme.primary }]}>
                See All
              </Text>
            </TouchableOpacity>
          </View>

          {recentAlerts && recentAlerts.length > 0 ? (
            recentAlerts.map((alert: Alert, index: number) => (
              <Animatable.View
                key={alert.id}
                animation="fadeInLeft"
                delay={900 + index * 100}
              >
                <AlertItem alert={alert} />
              </Animatable.View>
            ))
          ) : (
            <Card variant="outlined" padding="large" margin="small">
              <View style={styles.emptyState}>
                <Icon name="bell-off" size={40} color={theme.text + "60"} />
                <Text style={[styles.emptyStateText, { color: theme.text }]}>
                  No recent alerts
                </Text>
                <Button
                  title="Create Alert"
                  onPress={() => navigation.navigate("AlertsTab")}
                  variant="outline"
                  size="small"
                  style={{ marginTop: SPACING.MD }}
                />
              </View>
            </Card>
          )}
        </View>
      </Animatable.View>
    );
  };

  if (portfolioLoading && !portfolioData) {
    return (
      <SafeAreaView
        style={[styles.container, { backgroundColor: theme.background }]}
      >
        <LoadingSpinner size="large" />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.background }]}
    >
      {renderHeader()}

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
        {renderPortfolioSummary()}
        {renderPerformanceChart()}
        {renderQuickActions()}
        {renderMarketOverview()}
        {renderStrategies()}
        {renderWatchlist()}
        {renderNews()}
        {renderAlerts()}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    marginHorizontal: SPACING.MD,
    marginTop: SPACING.SM,
  },
  headerContent: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
  },
  subtitle: {
    fontSize: 14,
    marginTop: 2,
    opacity: 0.7,
  },
  headerIcons: {
    flexDirection: "row",
  },
  iconButton: {
    padding: SPACING.SM,
    marginLeft: SPACING.SM,
    position: "relative",
  },
  badge: {
    position: "absolute",
    right: 0,
    top: 0,
    minWidth: 18,
    height: 18,
    borderRadius: 9,
    justifyContent: "center",
    alignItems: "center",
  },
  badgeText: {
    color: "#ffffff",
    fontSize: 10,
    fontWeight: "bold",
  },
  scrollContent: {
    paddingBottom: SPACING.XXL,
  },
  portfolioSummary: {
    alignItems: "center",
  },
  portfolioLabel: {
    fontSize: 14,
    marginBottom: SPACING.XS,
  },
  portfolioValue: {
    fontSize: 36,
    fontWeight: "bold",
    marginBottom: SPACING.SM,
  },
  changeContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: SPACING.XS,
  },
  changeText: {
    fontSize: 16,
    fontWeight: "600",
  },
  changeLabel: {
    fontSize: 12,
    opacity: 0.6,
  },
  chartContainer: {
    marginTop: SPACING.MD,
  },
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: SPACING.MD,
    paddingHorizontal: SPACING.MD,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: "bold",
  },
  seeAllText: {
    fontSize: 14,
    fontWeight: "600",
  },
  strategiesContainer: {
    marginTop: SPACING.MD,
  },
  alertsContainer: {
    marginTop: SPACING.MD,
  },
  emptyState: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: SPACING.LG,
  },
  emptyStateText: {
    marginTop: SPACING.SM,
    fontSize: 16,
    textAlign: "center",
  },
});

export default DashboardScreen;
