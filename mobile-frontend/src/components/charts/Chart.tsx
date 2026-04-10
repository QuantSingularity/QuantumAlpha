import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  TouchableOpacity,
  ScrollView,
} from "react-native";
import {
  LineChart,
  BarChart,
  PieChart,
  ContributionGraph,
  ProgressChart,
} from "react-native-chart-kit";
import Icon from "react-native-vector-icons/MaterialCommunityIcons";
import { useTheme } from "../../context/ThemeContext";

interface ChartDataset {
  data: number[];
  color?: (opacity: number) => string;
  strokeWidth?: number;
}

interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

interface PieChartData {
  name: string;
  population: number;
  color: string;
  legendFontColor: string;
  legendFontSize: number;
}

interface ChartProps {
  type: "line" | "bar" | "pie" | "area" | "contribution" | "progress";
  data: ChartData | PieChartData[] | any;
  title?: string;
  subtitle?: string;
  height?: number;
  showLegend?: boolean;
  interactive?: boolean;
  timeframe?: "1D" | "1W" | "1M" | "3M" | "1Y" | "ALL";
  onTimeframeChange?: (timeframe: string) => void;
  style?: any;
}

const Chart: React.FC<ChartProps> = ({
  type,
  data,
  title,
  subtitle,
  height = 220,
  showLegend = false,
  interactive = false,
  timeframe = "1D",
  onTimeframeChange,
  style,
}) => {
  const { theme, isDarkMode } = useTheme();
  const screenWidth = Dimensions.get("window").width;
  const [selectedPoint, setSelectedPoint] = useState<any>(null);

  const timeframes = ["1D", "1W", "1M", "3M", "1Y", "ALL"];

  const chartConfig = {
    backgroundColor: theme.chartBackground,
    backgroundGradientFrom: theme.chartBackgroundGradientFrom,
    backgroundGradientTo: theme.chartBackgroundGradientTo,
    decimalPlaces: 2,
    color: (opacity = 1) => `rgba(26, 255, 146, ${opacity})`,
    labelColor: (opacity = 1) =>
      isDarkMode
        ? `rgba(255, 255, 255, ${opacity})`
        : `rgba(0, 0, 0, ${opacity})`,
    style: { borderRadius: 16 },
    propsForDots: {
      r: "4",
      strokeWidth: "2",
      stroke: theme.primary,
    },
    propsForBackgroundLines: {
      strokeDasharray: "",
      stroke: isDarkMode ? "#333" : "#e0e0e0",
      strokeWidth: 1,
    },
    fillShadowGradient: theme.primary,
    fillShadowGradientOpacity: 0.3,
  };

  const renderChart = () => {
    const chartWidth = screenWidth - 40;

    switch (type) {
      case "line":
        return (
          <LineChart
            data={data as ChartData}
            width={chartWidth}
            height={height}
            chartConfig={chartConfig}
            bezier
            style={styles.chart}
            onDataPointClick={interactive ? setSelectedPoint : undefined}
            withHorizontalLabels={true}
            withVerticalLabels={true}
            withInnerLines={true}
            withOuterLines={false}
            withDots={true}
            withShadow={false}
          />
        );

      // "area" is rendered as LineChart with shadow enabled —
      // react-native-chart-kit has no dedicated AreaChart export
      case "area":
        return (
          <LineChart
            data={data as ChartData}
            width={chartWidth}
            height={height}
            chartConfig={chartConfig}
            bezier
            style={styles.chart}
            withHorizontalLabels={true}
            withVerticalLabels={true}
            withInnerLines={true}
            withOuterLines={false}
            withDots={false}
            withShadow={true}
          />
        );

      case "bar":
        return (
          <BarChart
            data={data as ChartData}
            width={chartWidth}
            height={height}
            chartConfig={chartConfig}
            style={styles.chart}
            withHorizontalLabels={true}
            withVerticalLabels={true}
            withInnerLines={true}
            showBarTops={false}
            showValuesOnTopOfBars={false}
            yAxisLabel=""
            yAxisSuffix=""
          />
        );

      case "pie":
        return (
          <PieChart
            data={data as PieChartData[]}
            width={chartWidth}
            height={height}
            chartConfig={chartConfig}
            accessor="population"
            backgroundColor="transparent"
            paddingLeft="15"
            style={styles.chart}
            absolute={false}
          />
        );

      case "progress":
        return (
          <ProgressChart
            data={data}
            width={chartWidth}
            height={height}
            strokeWidth={16}
            radius={32}
            chartConfig={chartConfig}
            style={styles.chart}
            hideLegend={false}
          />
        );

      case "contribution":
        return (
          <ContributionGraph
            values={data}
            endDate={new Date()}
            numDays={105}
            width={chartWidth}
            height={height}
            chartConfig={chartConfig}
            style={styles.chart}
          />
        );

      default:
        return null;
    }
  };

  const renderTimeframeSelector = () => {
    if (!onTimeframeChange) return null;

    return (
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.timeframeContainer}
        contentContainerStyle={styles.timeframeContent}
      >
        {timeframes.map((tf) => (
          <TouchableOpacity
            key={tf}
            style={[
              styles.timeframeButton,
              {
                backgroundColor:
                  tf === timeframe ? theme.primary : "transparent",
                borderColor: theme.primary,
              },
            ]}
            onPress={() => onTimeframeChange(tf)}
          >
            <Text
              style={[
                styles.timeframeText,
                {
                  color: tf === timeframe ? "#ffffff" : theme.primary,
                },
              ]}
            >
              {tf}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    );
  };

  const renderSelectedPoint = () => {
    if (!selectedPoint || !interactive) return null;

    return (
      <View
        style={[styles.selectedPointContainer, { backgroundColor: theme.card }]}
      >
        <Text style={[styles.selectedPointText, { color: theme.text }]}>
          Value: {selectedPoint.value}
        </Text>
        <Text style={[styles.selectedPointText, { color: theme.text }]}>
          Index: {selectedPoint.index}
        </Text>
      </View>
    );
  };

  return (
    <View style={[styles.container, style]}>
      {(title || subtitle) && (
        <View style={styles.header}>
          {title && (
            <Text style={[styles.title, { color: theme.text }]}>{title}</Text>
          )}
          {subtitle && (
            <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
              {subtitle}
            </Text>
          )}
        </View>
      )}

      {renderTimeframeSelector()}

      <View style={styles.chartContainer}>{renderChart()}</View>

      {renderSelectedPoint()}

      {showLegend && type === "pie" && (
        <View style={styles.legendContainer}>
          {(data as PieChartData[]).map((item, index) => (
            <View key={index} style={styles.legendItem}>
              <View
                style={[styles.legendColor, { backgroundColor: item.color }]}
              />
              <Text style={[styles.legendText, { color: theme.text }]}>
                {item.name}
              </Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 10,
  },
  header: {
    paddingHorizontal: 20,
    marginBottom: 10,
  },
  title: {
    fontSize: 18,
    fontWeight: "bold",
  },
  subtitle: {
    fontSize: 14,
    opacity: 0.7,
    marginTop: 4,
  },
  timeframeContainer: {
    marginBottom: 15,
  },
  timeframeContent: {
    paddingHorizontal: 20,
  },
  timeframeButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    marginRight: 8,
  },
  timeframeText: {
    fontSize: 12,
    fontWeight: "600",
  },
  chartContainer: {
    alignItems: "center",
  },
  chart: {
    borderRadius: 16,
  },
  selectedPointContainer: {
    margin: 20,
    padding: 10,
    borderRadius: 8,
    alignItems: "center",
  },
  selectedPointText: {
    fontSize: 14,
  },
  legendContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "center",
    paddingHorizontal: 20,
    marginTop: 10,
  },
  legendItem: {
    flexDirection: "row",
    alignItems: "center",
    marginRight: 15,
    marginBottom: 5,
  },
  legendColor: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 6,
  },
  legendText: {
    fontSize: 12,
  },
});

export default Chart;
