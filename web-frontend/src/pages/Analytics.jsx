import {
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  Fade,
  FormControl,
  Grid,
  LinearProgress,
  MenuItem,
  Paper,
  Select,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Typography,
} from "@mui/material";
import {
  Activity,
  Download,
  Filter,
  RefreshCw,
  Shield,
  Target,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { useState } from "react";
import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  PieChart as RechartsPieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

// Mock data for analytics
const mockPortfolioData = [
  { date: "2024-01", value: 100000, return: 0, benchmark: 0 },
  { date: "2024-02", value: 105000, return: 5.0, benchmark: 2.1 },
  { date: "2024-03", value: 108500, return: 8.5, benchmark: 4.2 },
  { date: "2024-04", value: 115200, return: 15.2, benchmark: 6.8 },
  { date: "2024-05", value: 121800, return: 21.8, benchmark: 9.3 },
  { date: "2024-06", value: 128400, return: 28.4, benchmark: 11.7 },
];

const mockRiskMetrics = [
  {
    metric: "Value at Risk (95%)",
    value: "$12,450",
    change: -2.1,
    color: "#ef4444",
  },
  {
    metric: "Expected Shortfall",
    value: "$18,200",
    change: -1.8,
    color: "#f59e0b",
  },
  { metric: "Sharpe Ratio", value: "1.85", change: 0.12, color: "#10b981" },
  { metric: "Sortino Ratio", value: "2.34", change: 0.18, color: "#00d4ff" },
  { metric: "Maximum Drawdown", value: "8.2%", change: 0.5, color: "#ef4444" },
  { metric: "Beta", value: "0.78", change: -0.03, color: "#8b5cf6" },
];

const mockAssetAllocation = [
  { name: "Technology", value: 35, color: "#00d4ff" },
  { name: "Healthcare", value: 20, color: "#10b981" },
  { name: "Finance", value: 18, color: "#f59e0b" },
  { name: "Consumer", value: 15, color: "#8b5cf6" },
  { name: "Energy", value: 8, color: "#ef4444" },
  { name: "Other", value: 4, color: "#6b7280" },
];

const mockStrategyPerformance = [
  {
    strategy: "AI Momentum Pro",
    return: 24.8,
    volatility: 12.3,
    sharpe: 1.85,
    allocation: 35,
  },
  {
    strategy: "Quantum Alpha",
    return: 31.2,
    volatility: 18.7,
    sharpe: 2.14,
    allocation: 25,
  },
  {
    strategy: "Conservative Growth",
    return: 12.4,
    volatility: 6.8,
    sharpe: 1.32,
    allocation: 40,
  },
];

const mockTradeAnalysis = [
  {
    date: "2024-06-01",
    symbol: "AAPL",
    type: "buy",
    quantity: 100,
    price: 175.23,
    pnl: 1250,
    strategy: "AI Momentum Pro",
  },
  {
    date: "2024-06-02",
    symbol: "TSLA",
    type: "sell",
    quantity: 50,
    price: 245.67,
    pnl: -320,
    strategy: "Quantum Alpha",
  },
  {
    date: "2024-06-03",
    symbol: "NVDA",
    type: "buy",
    quantity: 25,
    price: 892.45,
    pnl: 2100,
    strategy: "AI Momentum Pro",
  },
  {
    date: "2024-06-04",
    symbol: "MSFT",
    type: "buy",
    quantity: 75,
    price: 412.89,
    pnl: 890,
    strategy: "Conservative Growth",
  },
  {
    date: "2024-06-05",
    symbol: "GOOGL",
    type: "sell",
    quantity: 30,
    price: 2785.34,
    pnl: 1560,
    strategy: "Quantum Alpha",
  },
];

const mockCorrelationData = [
  { asset1: "AAPL", asset2: "MSFT", correlation: 0.78 },
  { asset1: "AAPL", asset2: "GOOGL", correlation: 0.65 },
  { asset1: "AAPL", asset2: "TSLA", correlation: 0.42 },
  { asset1: "MSFT", asset2: "GOOGL", correlation: 0.71 },
  { asset1: "MSFT", asset2: "TSLA", correlation: 0.38 },
  { asset1: "GOOGL", asset2: "TSLA", correlation: 0.45 },
];

const Analytics = () => {
  const [selectedTab, setSelectedTab] = useState(0);
  const [timeframe, setTimeframe] = useState("6M");
  const [refreshing, setRefreshing] = useState(false);

  const handleTabChange = (_event, newValue) => {
    setSelectedTab(newValue);
  };

  const handleRefresh = () => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 2000);
  };

  const MetricCard = ({ metric, value, change, color, icon: Icon }) => (
    <Card
      sx={{
        height: "100%",
        background: `linear-gradient(135deg, ${color}15, ${color}05)`,
        border: `1px solid ${color}30`,
        borderRadius: 3,
        transition: "all 0.3s ease",
        "&:hover": {
          transform: "translateY(-2px)",
          boxShadow: `0 8px 25px ${color}25`,
        },
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            mb: 2,
          }}
        >
          <Typography variant="body2" color="text.secondary" fontWeight={500}>
            {metric}
          </Typography>
          {Icon && (
            <Avatar sx={{ bgcolor: `${color}20`, width: 32, height: 32 }}>
              <Icon size={16} color={color} />
            </Avatar>
          )}
        </Box>
        <Typography variant="h4" fontWeight={700} sx={{ mb: 1, color: color }}>
          {value}
        </Typography>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          {change > 0 ? (
            <TrendingUp size={16} color="#10b981" />
          ) : (
            <TrendingDown size={16} color="#ef4444" />
          )}
          <Typography
            variant="body2"
            color={change > 0 ? "#10b981" : "#ef4444"}
            fontWeight={600}
          >
            {change > 0 ? "+" : ""}
            {change}%
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );

  const PerformanceOverview = () => (
    <Grid container spacing={3}>
      {/* Portfolio Performance Chart */}
      <Grid item xs={12} lg={8}>
        <Paper
          sx={{
            p: 4,
            background: "rgba(255, 255, 255, 0.05)",
            backdropFilter: "blur(10px)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
          }}
        >
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              mb: 3,
            }}
          >
            <Typography variant="h5" fontWeight={700} color="white">
              Portfolio vs Benchmark Performance
            </Typography>
            <Box sx={{ display: "flex", gap: 2 }}>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <Select
                  value={timeframe}
                  onChange={(e) => setTimeframe(e.target.value)}
                  sx={{
                    color: "white",
                    "& .MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(255, 255, 255, 0.3)",
                    },
                    "&:hover .MuiOutlinedInput-notchedOutline": {
                      borderColor: "#00d4ff",
                    },
                  }}
                >
                  <MenuItem value="1M">1M</MenuItem>
                  <MenuItem value="3M">3M</MenuItem>
                  <MenuItem value="6M">6M</MenuItem>
                  <MenuItem value="1Y">1Y</MenuItem>
                  <MenuItem value="ALL">All</MenuItem>
                </Select>
              </FormControl>
              <Button
                variant="outlined"
                size="small"
                startIcon={<RefreshCw size={16} />}
                onClick={handleRefresh}
                disabled={refreshing}
                sx={{
                  borderColor: "#00d4ff",
                  color: "#00d4ff",
                  "&:hover": {
                    borderColor: "#00d4ff",
                    background: "rgba(0, 212, 255, 0.1)",
                  },
                }}
              >
                Refresh
              </Button>
            </Box>
          </Box>
          <Box sx={{ height: 400 }}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={mockPortfolioData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="rgba(255,255,255,0.1)"
                />
                <XAxis
                  dataKey="date"
                  stroke="rgba(255,255,255,0.7)"
                  fontSize={12}
                />
                <YAxis
                  stroke="rgba(255,255,255,0.7)"
                  fontSize={12}
                  tickFormatter={(value) => `${value}%`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "rgba(0, 0, 0, 0.8)",
                    border: "1px solid rgba(255, 255, 255, 0.2)",
                    borderRadius: "8px",
                    color: "white",
                  }}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="return"
                  fill="url(#colorPortfolio)"
                  stroke="#00d4ff"
                  strokeWidth={3}
                  name="Portfolio Return"
                />
                <Line
                  type="monotone"
                  dataKey="benchmark"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  name="Benchmark"
                />
                <defs>
                  <linearGradient
                    id="colorPortfolio"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
                  </linearGradient>
                </defs>
              </ComposedChart>
            </ResponsiveContainer>
          </Box>
        </Paper>
      </Grid>

      {/* Asset Allocation */}
      <Grid item xs={12} lg={4}>
        <Paper
          sx={{
            p: 4,
            background: "rgba(255, 255, 255, 0.05)",
            backdropFilter: "blur(10px)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
            height: "fit-content",
          }}
        >
          <Typography
            variant="h5"
            fontWeight={700}
            color="white"
            sx={{ mb: 3 }}
          >
            Asset Allocation
          </Typography>
          <Box sx={{ height: 300, mb: 2 }}>
            <ResponsiveContainer width="100%" height="100%">
              <RechartsPieChart>
                <Pie
                  data={mockAssetAllocation}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={120}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {mockAssetAllocation.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "rgba(0, 0, 0, 0.8)",
                    border: "1px solid rgba(255, 255, 255, 0.2)",
                    borderRadius: "8px",
                    color: "white",
                  }}
                />
              </RechartsPieChart>
            </ResponsiveContainer>
          </Box>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
            {mockAssetAllocation.map((asset, index) => (
              <Box
                key={index}
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Box
                    sx={{
                      width: 12,
                      height: 12,
                      borderRadius: "50%",
                      backgroundColor: asset.color,
                    }}
                  />
                  <Typography variant="body2" color="white">
                    {asset.name}
                  </Typography>
                </Box>
                <Typography variant="body2" fontWeight={600} color="white">
                  {asset.value}%
                </Typography>
              </Box>
            ))}
          </Box>
        </Paper>
      </Grid>

      {/* Risk Metrics */}
      <Grid item xs={12}>
        <Typography variant="h5" fontWeight={700} color="white" sx={{ mb: 3 }}>
          Risk Analytics
        </Typography>
        <Grid container spacing={3}>
          {mockRiskMetrics.map((metric, index) => (
            <Grid item xs={12} sm={6} md={4} lg={2} key={index}>
              <MetricCard
                metric={metric.metric}
                value={metric.value}
                change={metric.change}
                color={metric.color}
                icon={
                  index === 0
                    ? Shield
                    : index === 1
                      ? Target
                      : index === 2
                        ? TrendingUp
                        : Activity
                }
              />
            </Grid>
          ))}
        </Grid>
      </Grid>
    </Grid>
  );

  const StrategyAnalysis = () => (
    <Grid container spacing={3}>
      {/* Strategy Performance Scatter */}
      <Grid item xs={12} lg={8}>
        <Paper
          sx={{
            p: 4,
            background: "rgba(255, 255, 255, 0.05)",
            backdropFilter: "blur(10px)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
          }}
        >
          <Typography
            variant="h5"
            fontWeight={700}
            color="white"
            sx={{ mb: 3 }}
          >
            Risk-Return Analysis
          </Typography>
          <Box sx={{ height: 400 }}>
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="rgba(255,255,255,0.1)"
                />
                <XAxis
                  type="number"
                  dataKey="volatility"
                  name="Volatility"
                  stroke="rgba(255,255,255,0.7)"
                  fontSize={12}
                  tickFormatter={(value) => `${value}%`}
                />
                <YAxis
                  type="number"
                  dataKey="return"
                  name="Return"
                  stroke="rgba(255,255,255,0.7)"
                  fontSize={12}
                  tickFormatter={(value) => `${value}%`}
                />
                <Tooltip
                  cursor={{ strokeDasharray: "3 3" }}
                  contentStyle={{
                    backgroundColor: "rgba(0, 0, 0, 0.8)",
                    border: "1px solid rgba(255, 255, 255, 0.2)",
                    borderRadius: "8px",
                    color: "white",
                  }}
                  formatter={(value, name) => [
                    `${value}${name === "return" ? "%" : name === "volatility" ? "%" : ""}`,
                    name === "return"
                      ? "Return"
                      : name === "volatility"
                        ? "Volatility"
                        : "Sharpe Ratio",
                  ]}
                />
                <Scatter
                  name="Strategies"
                  data={mockStrategyPerformance}
                  fill="#00d4ff"
                />
              </ScatterChart>
            </ResponsiveContainer>
          </Box>
        </Paper>
      </Grid>

      {/* Strategy Performance Table */}
      <Grid item xs={12} lg={4}>
        <Paper
          sx={{
            p: 4,
            background: "rgba(255, 255, 255, 0.05)",
            backdropFilter: "blur(10px)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
          }}
        >
          <Typography
            variant="h5"
            fontWeight={700}
            color="white"
            sx={{ mb: 3 }}
          >
            Strategy Rankings
          </Typography>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {mockStrategyPerformance
              .sort((a, b) => b.sharpe - a.sharpe)
              .map((strategy, index) => (
                <Card
                  key={index}
                  sx={{
                    background: "rgba(255, 255, 255, 0.05)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    borderRadius: 2,
                  }}
                >
                  <CardContent sx={{ p: 2 }}>
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        mb: 1,
                      }}
                    >
                      <Typography
                        variant="body1"
                        fontWeight={600}
                        color="white"
                      >
                        {strategy.strategy}
                      </Typography>
                      <Chip
                        label={`#${index + 1}`}
                        size="small"
                        sx={{
                          background:
                            index === 0
                              ? "#10b981"
                              : index === 1
                                ? "#f59e0b"
                                : "#8b5cf6",
                          color: "white",
                          fontWeight: 600,
                        }}
                      />
                    </Box>
                    <Grid container spacing={1}>
                      <Grid item xs={4}>
                        <Typography variant="caption" color="text.secondary">
                          Return
                        </Typography>
                        <Typography
                          variant="body2"
                          fontWeight={600}
                          color="#10b981"
                        >
                          {strategy.return}%
                        </Typography>
                      </Grid>
                      <Grid item xs={4}>
                        <Typography variant="caption" color="text.secondary">
                          Volatility
                        </Typography>
                        <Typography
                          variant="body2"
                          fontWeight={600}
                          color="#f59e0b"
                        >
                          {strategy.volatility}%
                        </Typography>
                      </Grid>
                      <Grid item xs={4}>
                        <Typography variant="caption" color="text.secondary">
                          Sharpe
                        </Typography>
                        <Typography
                          variant="body2"
                          fontWeight={600}
                          color="#00d4ff"
                        >
                          {strategy.sharpe}
                        </Typography>
                      </Grid>
                    </Grid>
                    <Box sx={{ mt: 2 }}>
                      <Box
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          mb: 1,
                        }}
                      >
                        <Typography variant="caption" color="text.secondary">
                          Allocation: {strategy.allocation}%
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={strategy.allocation}
                        sx={{
                          height: 4,
                          borderRadius: 2,
                          backgroundColor: "rgba(255, 255, 255, 0.1)",
                          "& .MuiLinearProgress-bar": {
                            backgroundColor: "#00d4ff",
                            borderRadius: 2,
                          },
                        }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              ))}
          </Box>
        </Paper>
      </Grid>
    </Grid>
  );

  const TradeAnalysis = () => (
    <Grid container spacing={3}>
      {/* Recent Trades Table */}
      <Grid item xs={12}>
        <Paper
          sx={{
            p: 4,
            background: "rgba(255, 255, 255, 0.05)",
            backdropFilter: "blur(10px)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
          }}
        >
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              mb: 3,
            }}
          >
            <Typography variant="h5" fontWeight={700} color="white">
              Trade Analysis
            </Typography>
            <Box sx={{ display: "flex", gap: 2 }}>
              <Button
                variant="outlined"
                size="small"
                startIcon={<Filter size={16} />}
                sx={{
                  borderColor: "#00d4ff",
                  color: "#00d4ff",
                  "&:hover": {
                    borderColor: "#00d4ff",
                    background: "rgba(0, 212, 255, 0.1)",
                  },
                }}
              >
                Filter
              </Button>
              <Button
                variant="outlined"
                size="small"
                startIcon={<Download size={16} />}
                sx={{
                  borderColor: "#00d4ff",
                  color: "#00d4ff",
                  "&:hover": {
                    borderColor: "#00d4ff",
                    background: "rgba(0, 212, 255, 0.1)",
                  },
                }}
              >
                Export
              </Button>
            </Box>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: "white", fontWeight: 600 }}>
                    Date
                  </TableCell>
                  <TableCell sx={{ color: "white", fontWeight: 600 }}>
                    Symbol
                  </TableCell>
                  <TableCell sx={{ color: "white", fontWeight: 600 }}>
                    Type
                  </TableCell>
                  <TableCell sx={{ color: "white", fontWeight: 600 }}>
                    Quantity
                  </TableCell>
                  <TableCell sx={{ color: "white", fontWeight: 600 }}>
                    Price
                  </TableCell>
                  <TableCell sx={{ color: "white", fontWeight: 600 }}>
                    P&L
                  </TableCell>
                  <TableCell sx={{ color: "white", fontWeight: 600 }}>
                    Strategy
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {mockTradeAnalysis.map((trade, index) => (
                  <TableRow
                    key={index}
                    sx={{
                      "&:hover": {
                        backgroundColor: "rgba(255, 255, 255, 0.05)",
                      },
                    }}
                  >
                    <TableCell sx={{ color: "white" }}>{trade.date}</TableCell>
                    <TableCell sx={{ color: "white", fontWeight: 600 }}>
                      {trade.symbol}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={trade.type.toUpperCase()}
                        size="small"
                        sx={{
                          background:
                            trade.type === "buy" ? "#10b981" : "#ef4444",
                          color: "white",
                          fontWeight: 600,
                        }}
                      />
                    </TableCell>
                    <TableCell sx={{ color: "white" }}>
                      {trade.quantity}
                    </TableCell>
                    <TableCell sx={{ color: "white" }}>
                      ${trade.price.toFixed(2)}
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="body2"
                        fontWeight={600}
                        color={trade.pnl > 0 ? "#10b981" : "#ef4444"}
                      >
                        {trade.pnl > 0 ? "+" : ""}${trade.pnl}
                      </Typography>
                    </TableCell>
                    <TableCell
                      sx={{ color: "text.secondary", fontSize: "0.875rem" }}
                    >
                      {trade.strategy}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </Grid>

      {/* P&L Distribution */}
      <Grid item xs={12} md={6}>
        <Paper
          sx={{
            p: 4,
            background: "rgba(255, 255, 255, 0.05)",
            backdropFilter: "blur(10px)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
          }}
        >
          <Typography
            variant="h5"
            fontWeight={700}
            color="white"
            sx={{ mb: 3 }}
          >
            P&L Distribution
          </Typography>
          <Box sx={{ height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={[
                  { range: "-1000+", count: 1 },
                  { range: "-500 to -1000", count: 0 },
                  { range: "-100 to -500", count: 1 },
                  { range: "0 to -100", count: 0 },
                  { range: "0 to 100", count: 0 },
                  { range: "100 to 500", count: 1 },
                  { range: "500 to 1000", count: 1 },
                  { range: "1000+", count: 2 },
                ]}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="rgba(255,255,255,0.1)"
                />
                <XAxis
                  dataKey="range"
                  stroke="rgba(255,255,255,0.7)"
                  fontSize={10}
                  angle={-45}
                  textAnchor="end"
                />
                <YAxis stroke="rgba(255,255,255,0.7)" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "rgba(0, 0, 0, 0.8)",
                    border: "1px solid rgba(255, 255, 255, 0.2)",
                    borderRadius: "8px",
                    color: "white",
                  }}
                />
                <Bar dataKey="count" fill="#00d4ff" />
              </BarChart>
            </ResponsiveContainer>
          </Box>
        </Paper>
      </Grid>

      {/* Win/Loss Ratio */}
      <Grid item xs={12} md={6}>
        <Paper
          sx={{
            p: 4,
            background: "rgba(255, 255, 255, 0.05)",
            backdropFilter: "blur(10px)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
          }}
        >
          <Typography
            variant="h5"
            fontWeight={700}
            color="white"
            sx={{ mb: 3 }}
          >
            Win/Loss Analysis
          </Typography>
          <Box sx={{ height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <RechartsPieChart>
                <Pie
                  data={[
                    { name: "Winning Trades", value: 4, color: "#10b981" },
                    { name: "Losing Trades", value: 1, color: "#ef4444" },
                  ]}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={120}
                  paddingAngle={5}
                  dataKey="value"
                >
                  <Cell fill="#10b981" />
                  <Cell fill="#ef4444" />
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "rgba(0, 0, 0, 0.8)",
                    border: "1px solid rgba(255, 255, 255, 0.2)",
                    borderRadius: "8px",
                    color: "white",
                  }}
                />
                <Legend />
              </RechartsPieChart>
            </ResponsiveContainer>
          </Box>
          <Box sx={{ mt: 2, textAlign: "center" }}>
            <Typography variant="h4" fontWeight={700} color="#10b981">
              80%
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Win Rate
            </Typography>
          </Box>
        </Paper>
      </Grid>
    </Grid>
  );

  const CorrelationAnalysis = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Paper
          sx={{
            p: 4,
            background: "rgba(255, 255, 255, 0.05)",
            backdropFilter: "blur(10px)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
          }}
        >
          <Typography
            variant="h5"
            fontWeight={700}
            color="white"
            sx={{ mb: 3 }}
          >
            Asset Correlation Matrix
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: "white", fontWeight: 600 }}>
                    Asset Pair
                  </TableCell>
                  <TableCell sx={{ color: "white", fontWeight: 600 }}>
                    Correlation
                  </TableCell>
                  <TableCell sx={{ color: "white", fontWeight: 600 }}>
                    Strength
                  </TableCell>
                  <TableCell sx={{ color: "white", fontWeight: 600 }}>
                    Visual
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {mockCorrelationData.map((item, index) => (
                  <TableRow
                    key={index}
                    sx={{
                      "&:hover": {
                        backgroundColor: "rgba(255, 255, 255, 0.05)",
                      },
                    }}
                  >
                    <TableCell sx={{ color: "white" }}>
                      {item.asset1} - {item.asset2}
                    </TableCell>
                    <TableCell sx={{ color: "white", fontWeight: 600 }}>
                      {item.correlation.toFixed(2)}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={
                          Math.abs(item.correlation) > 0.7
                            ? "Strong"
                            : Math.abs(item.correlation) > 0.4
                              ? "Moderate"
                              : "Weak"
                        }
                        size="small"
                        sx={{
                          background:
                            Math.abs(item.correlation) > 0.7
                              ? "#ef4444"
                              : Math.abs(item.correlation) > 0.4
                                ? "#f59e0b"
                                : "#10b981",
                          color: "white",
                          fontWeight: 600,
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      <LinearProgress
                        variant="determinate"
                        value={Math.abs(item.correlation) * 100}
                        sx={{
                          height: 8,
                          borderRadius: 4,
                          backgroundColor: "rgba(255, 255, 255, 0.1)",
                          "& .MuiLinearProgress-bar": {
                            backgroundColor:
                              item.correlation > 0 ? "#10b981" : "#ef4444",
                            borderRadius: 4,
                          },
                        }}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </Grid>
    </Grid>
  );

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background:
          "linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%)",
        py: 4,
      }}
    >
      <Container maxWidth="xl">
        {/* Header */}
        <Fade in={true} timeout={800}>
          <Box sx={{ mb: 4 }}>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                mb: 2,
              }}
            >
              <Typography
                variant="h3"
                fontWeight={800}
                sx={{
                  background: "linear-gradient(45deg, #00d4ff, #8b5cf6)",
                  backgroundClip: "text",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                Portfolio Analytics
              </Typography>
              <Button
                variant="contained"
                startIcon={<Download size={20} />}
                sx={{
                  background: "linear-gradient(45deg, #00d4ff, #0099cc)",
                  boxShadow: "0 4px 20px rgba(0, 212, 255, 0.3)",
                  "&:hover": {
                    background: "linear-gradient(45deg, #0099cc, #0066aa)",
                    boxShadow: "0 6px 25px rgba(0, 212, 255, 0.4)",
                  },
                }}
              >
                Export Report
              </Button>
            </Box>
            <Typography variant="h6" color="text.secondary">
              Comprehensive analysis of your portfolio performance and risk
              metrics
            </Typography>
          </Box>
        </Fade>

        {/* Refresh Indicator */}
        {refreshing && (
          <Box sx={{ mb: 2 }}>
            <LinearProgress sx={{ borderRadius: 1 }} />
          </Box>
        )}

        {/* Tabs */}
        <Paper
          sx={{
            mb: 4,
            background: "rgba(255, 255, 255, 0.05)",
            backdropFilter: "blur(10px)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
          }}
        >
          <Tabs
            value={selectedTab}
            onChange={handleTabChange}
            sx={{
              "& .MuiTab-root": {
                color: "rgba(255, 255, 255, 0.7)",
                fontWeight: 600,
                "&.Mui-selected": {
                  color: "#00d4ff",
                },
              },
              "& .MuiTabs-indicator": {
                backgroundColor: "#00d4ff",
              },
            }}
          >
            <Tab label="Performance Overview" />
            <Tab label="Strategy Analysis" />
            <Tab label="Trade Analysis" />
            <Tab label="Correlation Analysis" />
          </Tabs>
        </Paper>

        {/* Tab Content */}
        {selectedTab === 0 && <PerformanceOverview />}
        {selectedTab === 1 && <StrategyAnalysis />}
        {selectedTab === 2 && <TradeAnalysis />}
        {selectedTab === 3 && <CorrelationAnalysis />}
      </Container>
    </Box>
  );
};

export default Analytics;
