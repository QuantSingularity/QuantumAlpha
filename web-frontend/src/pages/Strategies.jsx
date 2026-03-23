import React, { useState, useEffect } from "react";
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Button,
  Card,
  CardContent,
  CardActions,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  Avatar,
  Fade,
  Tooltip,
  Alert,
  Snackbar,
} from "@mui/material";
import {
  Plus,
  PlayA,
  Pause,
  Settings,
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Eye,
  Edit,
  Delete,
  Copy,
  Download,
  Upload,
  Zap,
  Brain,
  Target,
  Shield,
  Clock,
  DollarSign,
} from "lucide-react";
import { useSelector, useDispatch } from "react-redux";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
} from "recharts";

// Mock data for strategies
const mockStrategies = [
  {
    id: 1,
    name: "AI Momentum Pro",
    description: "Advanced momentum strategy using deep learning models",
    type: "AI",
    status: "active",
    risk: "medium",
    return: 24.8,
    sharpe: 1.85,
    maxDrawdown: -8.2,
    winRate: 73.5,
    totalTrades: 1247,
    avgHoldTime: "2.3 days",
    allocation: 35,
    created: "2024-01-15",
    performance: [
      { date: "2024-01", return: 2.1 },
      { date: "2024-02", return: 3.8 },
      { date: "2024-03", return: -1.2 },
      { date: "2024-04", return: 5.4 },
      { date: "2024-05", return: 4.2 },
      { date: "2024-06", return: 6.1 },
    ],
  },
  {
    id: 2,
    name: "Quantum Alpha",
    description:
      "Quantum-enhanced algorithmic trading with multi-factor models",
    type: "Quantum",
    status: "active",
    risk: "high",
    return: 31.2,
    sharpe: 2.14,
    maxDrawdown: -12.8,
    winRate: 68.9,
    totalTrades: 892,
    avgHoldTime: "1.8 days",
    allocation: 25,
    created: "2024-02-01",
    performance: [
      { date: "2024-01", return: 0 },
      { date: "2024-02", return: 4.2 },
      { date: "2024-03", return: 2.8 },
      { date: "2024-04", return: 7.1 },
      { date: "2024-05", return: 5.9 },
      { date: "2024-06", return: 8.3 },
    ],
  },
  {
    id: 3,
    name: "Conservative Growth",
    description: "Low-risk strategy focusing on stable dividend stocks",
    type: "Traditional",
    status: "active",
    risk: "low",
    return: 12.4,
    sharpe: 1.32,
    maxDrawdown: -4.1,
    winRate: 81.2,
    totalTrades: 324,
    avgHoldTime: "15.2 days",
    allocation: 40,
    created: "2023-11-20",
    performance: [
      { date: "2024-01", return: 1.2 },
      { date: "2024-02", return: 1.8 },
      { date: "2024-03", return: 0.9 },
      { date: "2024-04", return: 2.1 },
      { date: "2024-05", return: 1.6 },
      { date: "2024-06", return: 2.3 },
    ],
  },
  {
    id: 4,
    name: "Mean Reversion Bot",
    description: "Statistical arbitrage using mean reversion patterns",
    type: "Statistical",
    status: "paused",
    risk: "medium",
    return: 18.7,
    sharpe: 1.67,
    maxDrawdown: -6.9,
    winRate: 76.3,
    totalTrades: 2156,
    avgHoldTime: "0.8 days",
    allocation: 0,
    created: "2024-03-10",
    performance: [
      { date: "2024-01", return: 0 },
      { date: "2024-02", return: 0 },
      { date: "2024-03", return: 2.1 },
      { date: "2024-04", return: 3.4 },
      { date: "2024-05", return: 2.8 },
      { date: "2024-06", return: 0 },
    ],
  },
];

const Strategies = () => {
  const [strategies, setStrategies] = useState(mockStrategies);
  const [selectedTab, setSelectedTab] = useState(0);
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success",
  });
  const [newStrategy, setNewStrategy] = useState({
    name: "",
    description: "",
    type: "AI",
    risk: "medium",
    allocation: 0,
  });

  const handleTabChange = (event, newValue) => {
    setSelectedTab(newValue);
  };

  const handleCreateStrategy = () => {
    setOpenDialog(true);
    setSelectedStrategy(null);
    setNewStrategy({
      name: "",
      description: "",
      type: "AI",
      risk: "medium",
      allocation: 0,
    });
  };

  const handleEditStrategy = (strategy) => {
    setSelectedStrategy(strategy);
    setNewStrategy({
      name: strategy.name,
      description: strategy.description,
      type: strategy.type,
      risk: strategy.risk,
      allocation: strategy.allocation,
    });
    setOpenDialog(true);
  };

  const handleSaveStrategy = () => {
    if (selectedStrategy) {
      // Update existing strategy
      setStrategies((prev) =>
        prev.map((s) =>
          s.id === selectedStrategy.id ? { ...s, ...newStrategy } : s,
        ),
      );
      setSnackbar({
        open: true,
        message: "Strategy updated successfully!",
        severity: "success",
      });
    } else {
      // Create new strategy
      const newId = Math.max(...strategies.map((s) => s.id)) + 1;
      setStrategies((prev) => [
        ...prev,
        {
          id: newId,
          ...newStrategy,
          status: "inactive",
          return: 0,
          sharpe: 0,
          maxDrawdown: 0,
          winRate: 0,
          totalTrades: 0,
          avgHoldTime: "0 days",
          created: new Date().toISOString().split("T")[0],
          performance: [],
        },
      ]);
      setSnackbar({
        open: true,
        message: "Strategy created successfully!",
        severity: "success",
      });
    }
    setOpenDialog(false);
  };

  const handleToggleStrategy = (strategyId) => {
    setStrategies((prev) =>
      prev.map((s) =>
        s.id === strategyId
          ? { ...s, status: s.status === "active" ? "paused" : "active" }
          : s,
      ),
    );
    const strategy = strategies.find((s) => s.id === strategyId);
    const newStatus = strategy.status === "active" ? "paused" : "active";
    setSnackbar({
      open: true,
      message: `Strategy ${newStatus === "active" ? "activated" : "paused"}!`,
      severity: "info",
    });
  };

  const handleDeleteStrategy = (strategyId) => {
    setStrategies((prev) => prev.filter((s) => s.id !== strategyId));
    setSnackbar({
      open: true,
      message: "Strategy deleted successfully!",
      severity: "warning",
    });
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case "low":
        return "#10b981";
      case "medium":
        return "#f59e0b";
      case "high":
        return "#ef4444";
      default:
        return "#6b7280";
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case "AI":
        return <Brain size={20} />;
      case "Quantum":
        return <Zap size={20} />;
      case "Statistical":
        return <BarChart3 size={20} />;
      case "Traditional":
        return <Shield size={20} />;
      default:
        return <Activity size={20} />;
    }
  };

  const StrategyCard = ({ strategy }) => (
    <Fade in={true} timeout={800}>
      <Card
        sx={{
          height: "100%",
          background: "rgba(255, 255, 255, 0.05)",
          backdropFilter: "blur(10px)",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          borderRadius: 3,
          transition: "all 0.3s ease",
          "&:hover": {
            transform: "translateY(-4px)",
            boxShadow: "0 8px 25px rgba(0, 212, 255, 0.2)",
            border: "1px solid rgba(0, 212, 255, 0.3)",
          },
        }}
      >
        <CardContent sx={{ p: 3 }}>
          {/* Header */}
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              mb: 2,
            }}
          >
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <Avatar
                sx={{
                  bgcolor: getRiskColor(strategy.risk),
                  width: 32,
                  height: 32,
                }}
              >
                {getTypeIcon(strategy.type)}
              </Avatar>
              <Box>
                <Typography variant="h6" fontWeight={700} color="white">
                  {strategy.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {strategy.type} Strategy
                </Typography>
              </Box>
            </Box>
            <Chip
              label={strategy.status}
              size="small"
              sx={{
                background:
                  strategy.status === "active"
                    ? "#10b981"
                    : strategy.status === "paused"
                      ? "#f59e0b"
                      : "#6b7280",
                color: "white",
                fontWeight: 600,
              }}
            />
          </Box>

          {/* Description */}
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mb: 3, minHeight: 40 }}
          >
            {strategy.description}
          </Typography>

          {/* Metrics */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={6}>
              <Box sx={{ textAlign: "center" }}>
                <Typography variant="h5" fontWeight={700} color="#10b981">
                  {strategy.return > 0 ? "+" : ""}
                  {strategy.return}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Return
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box sx={{ textAlign: "center" }}>
                <Typography variant="h5" fontWeight={700} color="#00d4ff">
                  {strategy.sharpe}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Sharpe Ratio
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box sx={{ textAlign: "center" }}>
                <Typography variant="body1" fontWeight={600} color="white">
                  {strategy.winRate}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Win Rate
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box sx={{ textAlign: "center" }}>
                <Typography variant="body1" fontWeight={600} color="white">
                  {strategy.allocation}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Allocation
                </Typography>
              </Box>
            </Grid>
          </Grid>

          {/* Risk Indicator */}
          <Box sx={{ mb: 2 }}>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                mb: 1,
              }}
            >
              <Typography variant="body2" color="text.secondary">
                Risk Level
              </Typography>
              <Chip
                label={strategy.risk}
                size="small"
                variant="outlined"
                sx={{
                  borderColor: getRiskColor(strategy.risk),
                  color: getRiskColor(strategy.risk),
                  textTransform: "capitalize",
                }}
              />
            </Box>
            <LinearProgress
              variant="determinate"
              value={
                strategy.risk === "low"
                  ? 30
                  : strategy.risk === "medium"
                    ? 60
                    : 90
              }
              sx={{
                height: 6,
                borderRadius: 3,
                backgroundColor: "rgba(255, 255, 255, 0.1)",
                "& .MuiLinearProgress-bar": {
                  backgroundColor: getRiskColor(strategy.risk),
                  borderRadius: 3,
                },
              }}
            />
          </Box>
        </CardContent>

        <CardActions sx={{ px: 3, pb: 3, pt: 0 }}>
          <Box sx={{ display: "flex", gap: 1, width: "100%" }}>
            <Tooltip
              title={
                strategy.status === "active"
                  ? "Pause Strategy"
                  : "Start Strategy"
              }
            >
              <IconButton
                size="small"
                onClick={() => handleToggleStrategy(strategy.id)}
                sx={{
                  color: strategy.status === "active" ? "#f59e0b" : "#10b981",
                  "&:hover": { backgroundColor: "rgba(255, 255, 255, 0.1)" },
                }}
              >
                {strategy.status === "active" ? (
                  <Pause size={18} />
                ) : (
                  <Play size={18} />
                )}
              </IconButton>
            </Tooltip>
            <Tooltip title="View Details">
              <IconButton
                size="small"
                sx={{
                  color: "#00d4ff",
                  "&:hover": { backgroundColor: "rgba(255, 255, 255, 0.1)" },
                }}
              >
                <Eye size={18} />
              </IconButton>
            </Tooltip>
            <Tooltip title="Edit Strategy">
              <IconButton
                size="small"
                onClick={() => handleEditStrategy(strategy)}
                sx={{
                  color: "#8b5cf6",
                  "&:hover": { backgroundColor: "rgba(255, 255, 255, 0.1)" },
                }}
              >
                <Edit size={18} />
              </IconButton>
            </Tooltip>
            <Tooltip title="Clone Strategy">
              <IconButton
                size="small"
                sx={{
                  color: "#10b981",
                  "&:hover": { backgroundColor: "rgba(255, 255, 255, 0.1)" },
                }}
              >
                <Copy size={18} />
              </IconButton>
            </Tooltip>
            <Tooltip title="Delete Strategy">
              <IconButton
                size="small"
                onClick={() => handleDeleteStrategy(strategy.id)}
                sx={{
                  color: "#ef4444",
                  "&:hover": { backgroundColor: "rgba(255, 255, 255, 0.1)" },
                }}
              >
                <Delete size={18} />
              </IconButton>
            </Tooltip>
          </Box>
        </CardActions>
      </Card>
    </Fade>
  );

  const PerformanceTable = () => (
    <TableContainer
      component={Paper}
      sx={{
        background: "rgba(255, 255, 255, 0.05)",
        backdropFilter: "blur(10px)",
        border: "1px solid rgba(255, 255, 255, 0.1)",
      }}
    >
      <Table>
        <TableHead>
          <TableRow>
            <TableCell sx={{ color: "white", fontWeight: 600 }}>
              Strategy
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: 600 }}>
              Status
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: 600 }}>
              Return
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: 600 }}>
              Sharpe
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: 600 }}>
              Max DD
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: 600 }}>
              Win Rate
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: 600 }}>
              Trades
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: 600 }}>
              Actions
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {strategies.map((strategy) => (
            <TableRow
              key={strategy.id}
              sx={{
                "&:hover": { backgroundColor: "rgba(255, 255, 255, 0.05)" },
              }}
            >
              <TableCell>
                <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                  <Avatar
                    sx={{
                      bgcolor: getRiskColor(strategy.risk),
                      width: 32,
                      height: 32,
                    }}
                  >
                    {getTypeIcon(strategy.type)}
                  </Avatar>
                  <Box>
                    <Typography variant="body2" fontWeight={600} color="white">
                      {strategy.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {strategy.type}
                    </Typography>
                  </Box>
                </Box>
              </TableCell>
              <TableCell>
                <Chip
                  label={strategy.status}
                  size="small"
                  sx={{
                    background:
                      strategy.status === "active"
                        ? "#10b981"
                        : strategy.status === "paused"
                          ? "#f59e0b"
                          : "#6b7280",
                    color: "white",
                    fontWeight: 600,
                  }}
                />
              </TableCell>
              <TableCell>
                <Typography
                  variant="body2"
                  fontWeight={600}
                  color={strategy.return > 0 ? "#10b981" : "#ef4444"}
                >
                  {strategy.return > 0 ? "+" : ""}
                  {strategy.return}%
                </Typography>
              </TableCell>
              <TableCell>
                <Typography variant="body2" color="white">
                  {strategy.sharpe}
                </Typography>
              </TableCell>
              <TableCell>
                <Typography variant="body2" color="#ef4444">
                  {strategy.maxDrawdown}%
                </Typography>
              </TableCell>
              <TableCell>
                <Typography variant="body2" color="white">
                  {strategy.winRate}%
                </Typography>
              </TableCell>
              <TableCell>
                <Typography variant="body2" color="white">
                  {strategy.totalTrades.toLocaleString()}
                </Typography>
              </TableCell>
              <TableCell>
                <Box sx={{ display: "flex", gap: 0.5 }}>
                  <IconButton
                    size="small"
                    onClick={() => handleToggleStrategy(strategy.id)}
                    sx={{
                      color:
                        strategy.status === "active" ? "#f59e0b" : "#10b981",
                    }}
                  >
                    {strategy.status === "active" ? (
                      <Pause size={16} />
                    ) : (
                      <Play size={16} />
                    )}
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleEditStrategy(strategy)}
                    sx={{ color: "#8b5cf6" }}
                  >
                    <Edit size={16} />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleDeleteStrategy(strategy.id)}
                    sx={{ color: "#ef4444" }}
                  >
                    <Delete size={16} />
                  </IconButton>
                </Box>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
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
                  background: "linear-gradient(45deg, #00d4ff, #ff00ff)",
                  backgroundClip: "text",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                Trading Strategies
              </Typography>
              <Box sx={{ display: "flex", gap: 2 }}>
                <Button
                  variant="outlined"
                  startIcon={<Upload size={20} />}
                  sx={{
                    borderColor: "#00d4ff",
                    color: "#00d4ff",
                    "&:hover": {
                      borderColor: "#00d4ff",
                      background: "rgba(0, 212, 255, 0.1)",
                    },
                  }}
                >
                  Import
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Download size={20} />}
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
                <Button
                  variant="contained"
                  startIcon={<Plus size={20} />}
                  onClick={handleCreateStrategy}
                  sx={{
                    background: "linear-gradient(45deg, #00d4ff, #0099cc)",
                    boxShadow: "0 4px 20px rgba(0, 212, 255, 0.3)",
                    "&:hover": {
                      background: "linear-gradient(45deg, #0099cc, #0066aa)",
                      boxShadow: "0 6px 25px rgba(0, 212, 255, 0.4)",
                    },
                  }}
                >
                  Create Strategy
                </Button>
              </Box>
            </Box>
            <Typography variant="h6" color="text.secondary">
              Manage and monitor your AI-powered trading strategies
            </Typography>
          </Box>
        </Fade>

        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                background: "rgba(16, 185, 129, 0.1)",
                border: "1px solid rgba(16, 185, 129, 0.3)",
                borderRadius: 3,
              }}
            >
              <CardContent sx={{ textAlign: "center", py: 3 }}>
                <Typography variant="h4" fontWeight={700} color="#10b981">
                  {strategies.filter((s) => s.status === "active").length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Active Strategies
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                background: "rgba(0, 212, 255, 0.1)",
                border: "1px solid rgba(0, 212, 255, 0.3)",
                borderRadius: 3,
              }}
            >
              <CardContent sx={{ textAlign: "center", py: 3 }}>
                <Typography variant="h4" fontWeight={700} color="#00d4ff">
                  {strategies.reduce((sum, s) => sum + s.return, 0).toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Return
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                background: "rgba(139, 92, 246, 0.1)",
                border: "1px solid rgba(139, 92, 246, 0.3)",
                borderRadius: 3,
              }}
            >
              <CardContent sx={{ textAlign: "center", py: 3 }}>
                <Typography variant="h4" fontWeight={700} color="#8b5cf6">
                  {(
                    strategies.reduce((sum, s) => sum + s.sharpe, 0) /
                    strategies.length
                  ).toFixed(2)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Avg Sharpe Ratio
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                background: "rgba(245, 158, 11, 0.1)",
                border: "1px solid rgba(245, 158, 11, 0.3)",
                borderRadius: 3,
              }}
            >
              <CardContent sx={{ textAlign: "center", py: 3 }}>
                <Typography variant="h4" fontWeight={700} color="#f59e0b">
                  {strategies
                    .reduce((sum, s) => sum + s.totalTrades, 0)
                    .toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Trades
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

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
            <Tab label="Strategy Cards" />
            <Tab label="Performance Table" />
            <Tab label="Analytics" />
          </Tabs>
        </Paper>

        {/* Tab Content */}
        {selectedTab === 0 && (
          <Grid container spacing={3}>
            {strategies.map((strategy) => (
              <Grid item xs={12} sm={6} lg={4} key={strategy.id}>
                <StrategyCard strategy={strategy} />
              </Grid>
            ))}
          </Grid>
        )}

        {selectedTab === 1 && <PerformanceTable />}

        {selectedTab === 2 && (
          <Grid container spacing={3}>
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
                  Strategy Performance Comparison
                </Typography>
                <Box sx={{ height: 400 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart>
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
                      <RechartsTooltip
                        contentStyle={{
                          backgroundColor: "rgba(0, 0, 0, 0.8)",
                          border: "1px solid rgba(255, 255, 255, 0.2)",
                          borderRadius: "8px",
                          color: "white",
                        }}
                      />
                      <Legend />
                      {strategies.slice(0, 3).map((strategy, index) => (
                        <Line
                          key={strategy.id}
                          type="monotone"
                          dataKey="return"
                          data={strategy.performance}
                          stroke={["#00d4ff", "#10b981", "#f59e0b"][index]}
                          strokeWidth={2}
                          name={strategy.name}
                        />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </Box>
              </Paper>
            </Grid>
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
                  Risk Distribution
                </Typography>
                <Box sx={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={[
                        {
                          risk: "Low",
                          count: strategies.filter((s) => s.risk === "low")
                            .length,
                        },
                        {
                          risk: "Medium",
                          count: strategies.filter((s) => s.risk === "medium")
                            .length,
                        },
                        {
                          risk: "High",
                          count: strategies.filter((s) => s.risk === "high")
                            .length,
                        },
                      ]}
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="rgba(255,255,255,0.1)"
                      />
                      <XAxis stroke="rgba(255,255,255,0.7)" fontSize={12} />
                      <YAxis stroke="rgba(255,255,255,0.7)" fontSize={12} />
                      <RechartsTooltip
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
          </Grid>
        )}

        {/* Create/Edit Strategy Dialog */}
        <Dialog
          open={openDialog}
          onClose={() => setOpenDialog(false)}
          maxWidth="md"
          fullWidth
          PaperProps={{
            sx: {
              background: "rgba(15, 15, 35, 0.95)",
              backdropFilter: "blur(20px)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: 3,
            },
          }}
        >
          <DialogTitle sx={{ color: "white", fontWeight: 700 }}>
            {selectedStrategy ? "Edit Strategy" : "Create New Strategy"}
          </DialogTitle>
          <DialogContent>
            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Strategy Name"
                  value={newStrategy.name}
                  onChange={(e) =>
                    setNewStrategy({ ...newStrategy, name: e.target.value })
                  }
                  sx={{
                    "& .MuiOutlinedInput-root": {
                      color: "white",
                      "& fieldset": { borderColor: "rgba(255, 255, 255, 0.3)" },
                      "&:hover fieldset": { borderColor: "#00d4ff" },
                      "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                    },
                    "& .MuiInputLabel-root": {
                      color: "rgba(255, 255, 255, 0.7)",
                    },
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Description"
                  value={newStrategy.description}
                  onChange={(e) =>
                    setNewStrategy({
                      ...newStrategy,
                      description: e.target.value,
                    })
                  }
                  sx={{
                    "& .MuiOutlinedInput-root": {
                      color: "white",
                      "& fieldset": { borderColor: "rgba(255, 255, 255, 0.3)" },
                      "&:hover fieldset": { borderColor: "#00d4ff" },
                      "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                    },
                    "& .MuiInputLabel-root": {
                      color: "rgba(255, 255, 255, 0.7)",
                    },
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel sx={{ color: "rgba(255, 255, 255, 0.7)" }}>
                    Strategy Type
                  </InputLabel>
                  <Select
                    value={newStrategy.type}
                    onChange={(e) =>
                      setNewStrategy({ ...newStrategy, type: e.target.value })
                    }
                    sx={{
                      color: "white",
                      "& .MuiOutlinedInput-notchedOutline": {
                        borderColor: "rgba(255, 255, 255, 0.3)",
                      },
                      "&:hover .MuiOutlinedInput-notchedOutline": {
                        borderColor: "#00d4ff",
                      },
                      "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                        borderColor: "#00d4ff",
                      },
                    }}
                  >
                    <MenuItem value="AI">AI</MenuItem>
                    <MenuItem value="Quantum">Quantum</MenuItem>
                    <MenuItem value="Statistical">Statistical</MenuItem>
                    <MenuItem value="Traditional">Traditional</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel sx={{ color: "rgba(255, 255, 255, 0.7)" }}>
                    Risk Level
                  </InputLabel>
                  <Select
                    value={newStrategy.risk}
                    onChange={(e) =>
                      setNewStrategy({ ...newStrategy, risk: e.target.value })
                    }
                    sx={{
                      color: "white",
                      "& .MuiOutlinedInput-notchedOutline": {
                        borderColor: "rgba(255, 255, 255, 0.3)",
                      },
                      "&:hover .MuiOutlinedInput-notchedOutline": {
                        borderColor: "#00d4ff",
                      },
                      "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                        borderColor: "#00d4ff",
                      },
                    }}
                  >
                    <MenuItem value="low">Low</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  type="number"
                  label="Initial Allocation (%)"
                  value={newStrategy.allocation}
                  onChange={(e) =>
                    setNewStrategy({
                      ...newStrategy,
                      allocation: parseInt(e.target.value) || 0,
                    })
                  }
                  inputProps={{ min: 0, max: 100 }}
                  sx={{
                    "& .MuiOutlinedInput-root": {
                      color: "white",
                      "& fieldset": { borderColor: "rgba(255, 255, 255, 0.3)" },
                      "&:hover fieldset": { borderColor: "#00d4ff" },
                      "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                    },
                    "& .MuiInputLabel-root": {
                      color: "rgba(255, 255, 255, 0.7)",
                    },
                  }}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions sx={{ p: 3 }}>
            <Button
              onClick={() => setOpenDialog(false)}
              sx={{ color: "rgba(255, 255, 255, 0.7)" }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveStrategy}
              variant="contained"
              sx={{
                background: "linear-gradient(45deg, #00d4ff, #0099cc)",
                "&:hover": {
                  background: "linear-gradient(45deg, #0099cc, #0066aa)",
                },
              }}
            >
              {selectedStrategy ? "Update" : "Create"}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Snackbar */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={4000}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
        >
          <Alert
            severity={snackbar.severity}
            onClose={() => setSnackbar({ ...snackbar, open: false })}
            sx={{
              background: "rgba(0, 0, 0, 0.8)",
              color: "white",
              "& .MuiAlert-icon": { color: "inherit" },
            }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Container>
    </Box>
  );
};

export default Strategies;
