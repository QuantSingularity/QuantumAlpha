import {
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  Fade,
  Grid,
  IconButton,
  Paper,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  DollarSign,
  Eye,
  Plus,
  Settings,
  TrendingUp,
  Zap,
} from "lucide-react";
import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import ErrorBoundary from "../components/common/ErrorBoundary";
import {
  useGetPortfolioQuery,
  useGetStrategiesQuery,
  useGetTradesQuery,
} from "../services/api";
import { toggleModal } from "../store/slices/uiSlice";

// Mock data for demonstration
const mockPortfolioData = {
  portfolioValue: 125847.32,
  dailyChange: 2847.32,
  percentChange: 2.31,
  historicalData: [
    { date: "2024-01-01", value: 100000 },
    { date: "2024-02-01", value: 105000 },
    { date: "2024-03-01", value: 108000 },
    { date: "2024-04-01", value: 112000 },
    { date: "2024-05-01", value: 118000 },
    { date: "2024-06-01", value: 125847 },
  ],
};

const mockStrategies = [
  {
    id: 1,
    name: "AI Momentum",
    return: 15.2,
    status: "active",
    risk: "medium",
  },
  {
    id: 2,
    name: "Quantum Alpha",
    return: 23.8,
    status: "active",
    risk: "high",
  },
  {
    id: 3,
    name: "Conservative Growth",
    return: 8.4,
    status: "active",
    risk: "low",
  },
];

const mockTrades = [
  {
    id: 1,
    symbol: "AAPL",
    type: "buy",
    amount: 1500,
    price: 175.23,
    time: "2 hours ago",
  },
  {
    id: 2,
    symbol: "TSLA",
    type: "sell",
    amount: 2300,
    price: 245.67,
    time: "4 hours ago",
  },
  {
    id: 3,
    symbol: "NVDA",
    type: "buy",
    amount: 1800,
    price: 892.45,
    time: "6 hours ago",
  },
];

const Dashboard = () => {
  const theme = useTheme();
  const dispatch = useDispatch();
  const _isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const [_animationDelay] = useState(0);

  // Get data from Redux store and API
  const { portfolioValue, dailyChange, percentChange, historicalData } =
    useSelector((state) => state.portfolio);
  const { strategies, recentTrades } = useSelector((state) => state.strategy);

  // RTK Query hooks with automatic loading and error states
  const {
    data: portfolioData,
    isLoading: portfolioLoading,
    error: portfolioError,
  } = useGetPortfolioQuery();

  const {
    data: strategiesData,
    isLoading: strategiesLoading,
    error: strategiesError,
  } = useGetStrategiesQuery();

  const {
    data: tradesData,
    isLoading: tradesLoading,
    error: tradesError,
  } = useGetTradesQuery({ limit: 5 });

  // Use mock data for demonstration
  const displayPortfolioData = portfolioData || mockPortfolioData;
  const displayStrategies = strategiesData || mockStrategies;
  const displayTrades = tradesData || mockTrades;

  // Handle deposit/withdraw modals
  const handleOpenDepositModal = () => {
    dispatch(toggleModal({ modal: "deposit", value: true }));
  };

  const handleOpenWithdrawModal = () => {
    dispatch(toggleModal({ modal: "withdraw", value: true }));
  };

  const StatCard = ({ title, value, change, icon: Icon, color, delay = 0 }) => (
    <Fade in={true} timeout={800} style={{ transitionDelay: `${delay}ms` }}>
      <Card
        sx={{
          height: "100%",
          background: `linear-gradient(135deg, ${color}15, ${color}05)`,
          border: `1px solid ${color}30`,
          borderRadius: 3,
          transition: "all 0.3s ease",
          cursor: "pointer",
          "&:hover": {
            transform: "translateY(-4px)",
            boxShadow: `0 8px 25px ${color}25`,
            border: `1px solid ${color}50`,
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
              {title}
            </Typography>
            <Avatar sx={{ bgcolor: `${color}20`, width: 40, height: 40 }}>
              <Icon size={20} color={color} />
            </Avatar>
          </Box>
          <Typography
            variant="h4"
            fontWeight={700}
            sx={{ mb: 1, color: color }}
          >
            {value}
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            {change > 0 ? (
              <ArrowUpRight size={16} color="#10b981" />
            ) : (
              <ArrowDownRight size={16} color="#ef4444" />
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
    </Fade>
  );

  return (
    <ErrorBoundary>
      <Box
        sx={{
          minHeight: "100vh",
          background:
            "linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%)",
          py: 4,
        }}
      >
        <Container maxWidth="xl">
          {/* Hero Section */}
          <Fade in={true} timeout={1000}>
            <Box sx={{ mb: 6, textAlign: "center" }}>
              <Typography
                variant="h2"
                fontWeight={800}
                sx={{
                  background:
                    "linear-gradient(45deg, #00d4ff, #ff00ff, #00ff88)",
                  backgroundClip: "text",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  mb: 2,
                  fontSize: { xs: "2.5rem", md: "3.5rem" },
                }}
              >
                QuantumAlpha Dashboard
              </Typography>
              <Typography
                variant="h6"
                color="text.secondary"
                sx={{ maxWidth: 600, mx: "auto", mb: 4 }}
              >
                Advanced AI-powered trading platform with quantum-enhanced
                algorithms
              </Typography>
              <Box
                sx={{
                  display: "flex",
                  gap: 2,
                  justifyContent: "center",
                  flexWrap: "wrap",
                }}
              >
                <Button
                  variant="contained"
                  size="large"
                  startIcon={<Plus size={20} />}
                  onClick={handleOpenDepositModal}
                  sx={{
                    px: 4,
                    py: 1.5,
                    fontWeight: 600,
                    background: "linear-gradient(45deg, #00d4ff, #0099cc)",
                    boxShadow: "0 4px 20px rgba(0, 212, 255, 0.3)",
                    "&:hover": {
                      background: "linear-gradient(45deg, #0099cc, #0066aa)",
                      boxShadow: "0 6px 25px rgba(0, 212, 255, 0.4)",
                      transform: "translateY(-2px)",
                    },
                  }}
                >
                  Add Funds
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  startIcon={<Settings size={20} />}
                  onClick={handleOpenWithdrawModal}
                  sx={{
                    px: 4,
                    py: 1.5,
                    fontWeight: 600,
                    borderWidth: 2,
                    borderColor: "#00d4ff",
                    color: "#00d4ff",
                    "&:hover": {
                      borderWidth: 2,
                      borderColor: "#00d4ff",
                      background: "rgba(0, 212, 255, 0.1)",
                      transform: "translateY(-2px)",
                    },
                  }}
                >
                  Settings
                </Button>
              </Box>
            </Box>
          </Fade>

          {/* Stats Cards */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Portfolio Value"
                value={`$${displayPortfolioData.portfolioValue?.toLocaleString() || "125,847"}`}
                change={displayPortfolioData.percentChange || 2.31}
                icon={DollarSign}
                color="#00d4ff"
                delay={0}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Daily P&L"
                value={`$${displayPortfolioData.dailyChange?.toLocaleString() || "2,847"}`}
                change={1.8}
                icon={TrendingUp}
                color="#10b981"
                delay={200}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Active Strategies"
                value={displayStrategies?.length || 3}
                change={12.5}
                icon={Activity}
                color="#f59e0b"
                delay={400}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Win Rate"
                value="87.3%"
                change={5.2}
                icon={BarChart3}
                color="#8b5cf6"
                delay={600}
              />
            </Grid>
          </Grid>

          {/* Performance Chart */}
          <Fade in={true} timeout={1200}>
            <Paper
              elevation={0}
              sx={{
                p: 4,
                mb: 4,
                borderRadius: 4,
                background: "rgba(255, 255, 255, 0.05)",
                backdropFilter: "blur(10px)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",
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
                  Portfolio Performance
                </Typography>
                <Chip
                  label="Real-time"
                  icon={<Zap size={16} />}
                  sx={{
                    background: "linear-gradient(45deg, #10b981, #059669)",
                    color: "white",
                    fontWeight: 600,
                  }}
                />
              </Box>
              <Box sx={{ height: 350 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={displayPortfolioData.historicalData}>
                    <defs>
                      <linearGradient
                        id="colorValue"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="5%"
                          stopColor="#00d4ff"
                          stopOpacity={0.3}
                        />
                        <stop
                          offset="95%"
                          stopColor="#00d4ff"
                          stopOpacity={0}
                        />
                      </linearGradient>
                    </defs>
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
                      tickFormatter={(value) =>
                        `$${(value / 1000).toFixed(0)}k`
                      }
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "rgba(0, 0, 0, 0.8)",
                        border: "1px solid rgba(255, 255, 255, 0.2)",
                        borderRadius: "8px",
                        color: "white",
                      }}
                      formatter={(value) => [
                        `$${value.toLocaleString()}`,
                        "Portfolio Value",
                      ]}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#00d4ff"
                      strokeWidth={3}
                      fillOpacity={1}
                      fill="url(#colorValue)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </Box>
            </Paper>
          </Fade>

          {/* Strategy Performance and Recent Trades */}
          <Grid container spacing={4}>
            <Grid item xs={12} lg={8}>
              <Fade in={true} timeout={1400}>
                <Paper
                  elevation={0}
                  sx={{
                    p: 4,
                    height: "100%",
                    borderRadius: 4,
                    background: "rgba(255, 255, 255, 0.05)",
                    backdropFilter: "blur(10px)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",
                  }}
                >
                  <Typography
                    variant="h5"
                    fontWeight={700}
                    color="white"
                    sx={{ mb: 3 }}
                  >
                    AI Strategy Performance
                  </Typography>
                  <Box
                    sx={{ display: "flex", flexDirection: "column", gap: 2 }}
                  >
                    {displayStrategies.map((strategy) => (
                      <Card
                        key={strategy.id || strategy.name}
                        sx={{
                          background: "rgba(255, 255, 255, 0.05)",
                          border: "1px solid rgba(255, 255, 255, 0.1)",
                          borderRadius: 2,
                          transition: "all 0.3s ease",
                          "&:hover": {
                            background: "rgba(255, 255, 255, 0.1)",
                            transform: "translateX(8px)",
                          },
                        }}
                      >
                        <CardContent sx={{ p: 3 }}>
                          <Box
                            sx={{
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "space-between",
                            }}
                          >
                            <Box>
                              <Typography
                                variant="h6"
                                fontWeight={600}
                                color="white"
                              >
                                {strategy.name}
                              </Typography>
                              <Box
                                sx={{
                                  display: "flex",
                                  alignItems: "center",
                                  gap: 2,
                                  mt: 1,
                                }}
                              >
                                <Chip
                                  label={strategy.status}
                                  size="small"
                                  sx={{
                                    background:
                                      strategy.status === "active"
                                        ? "#10b981"
                                        : "#6b7280",
                                    color: "white",
                                    fontWeight: 500,
                                  }}
                                />
                                <Chip
                                  label={`${strategy.risk} risk`}
                                  size="small"
                                  variant="outlined"
                                  sx={{
                                    borderColor:
                                      strategy.risk === "high"
                                        ? "#ef4444"
                                        : strategy.risk === "medium"
                                          ? "#f59e0b"
                                          : "#10b981",
                                    color:
                                      strategy.risk === "high"
                                        ? "#ef4444"
                                        : strategy.risk === "medium"
                                          ? "#f59e0b"
                                          : "#10b981",
                                  }}
                                />
                              </Box>
                            </Box>
                            <Box sx={{ textAlign: "right" }}>
                              <Typography
                                variant="h5"
                                fontWeight={700}
                                color={
                                  strategy.return > 0 ? "#10b981" : "#ef4444"
                                }
                              >
                                +{strategy.return}%
                              </Typography>
                              <IconButton
                                size="small"
                                sx={{ color: "#00d4ff" }}
                              >
                                <Eye size={16} />
                              </IconButton>
                            </Box>
                          </Box>
                        </CardContent>
                      </Card>
                    ))}
                  </Box>
                </Paper>
              </Fade>
            </Grid>
            <Grid item xs={12} lg={4}>
              <Fade in={true} timeout={1600}>
                <Paper
                  elevation={0}
                  sx={{
                    p: 4,
                    height: "100%",
                    borderRadius: 4,
                    background: "rgba(255, 255, 255, 0.05)",
                    backdropFilter: "blur(10px)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",
                  }}
                >
                  <Typography
                    variant="h5"
                    fontWeight={700}
                    color="white"
                    sx={{ mb: 3 }}
                  >
                    Recent Trades
                  </Typography>
                  <Box
                    sx={{ display: "flex", flexDirection: "column", gap: 2 }}
                  >
                    {displayTrades.map((trade, _index) => (
                      <Card
                        key={trade.id}
                        sx={{
                          background: "rgba(255, 255, 255, 0.05)",
                          border: "1px solid rgba(255, 255, 255, 0.1)",
                          borderRadius: 2,
                          transition: "all 0.3s ease",
                          "&:hover": {
                            background: "rgba(255, 255, 255, 0.1)",
                          },
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
                              variant="subtitle1"
                              fontWeight={600}
                              color="white"
                            >
                              {trade.symbol}
                            </Typography>
                            <Chip
                              label={trade.type.toUpperCase()}
                              size="small"
                              sx={{
                                background:
                                  trade.type === "buy" ? "#10b981" : "#ef4444",
                                color: "white",
                                fontWeight: 500,
                                fontSize: "0.75rem",
                              }}
                            />
                          </Box>
                          <Typography variant="body2" color="text.secondary">
                            ${trade.amount.toLocaleString()} @ ${trade.price}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {trade.time}
                          </Typography>
                        </CardContent>
                      </Card>
                    ))}
                  </Box>
                </Paper>
              </Fade>
            </Grid>
          </Grid>
        </Container>
      </Box>
    </ErrorBoundary>
  );
};

export default Dashboard;
