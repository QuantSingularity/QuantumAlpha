import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Grid,
  IconButton,
  Paper,
  Skeleton,
  Switch,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  BarChart3,
  Edit,
  Pause,
  Play,
  Trash2,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  useDeleteStrategyMutation,
  useGetRiskMetricsQuery,
  useGetStrategyQuery,
  useUpdateStrategyMutation,
} from "../services/api";
import { formatCurrency, formatPercentage } from "../utils/format";

const StrategyDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [selectedTab, setSelectedTab] = useState(0);
  const [editDialog, setEditDialog] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState(false);

  // API Hooks
  const { data: strategy, isLoading, error, refetch } = useGetStrategyQuery(id);
  const { data: riskMetrics } = useGetRiskMetricsQuery(id);
  const [updateStrategy] = useUpdateStrategyMutation();
  const [deleteStrategy] = useDeleteStrategyMutation();

  // Local state for editing
  const [editFormData, setEditFormData] = useState({
    name: "",
    description: "",
    active: false,
  });

  // Handle tab change
  const handleTabChange = (_event, newValue) => {
    setSelectedTab(newValue);
  };

  // Handle edit
  const handleEdit = () => {
    if (strategy) {
      setEditFormData({
        name: strategy.name || "",
        description: strategy.description || "",
        active: strategy.active || false,
      });
      setEditDialog(true);
    }
  };

  const handleSaveEdit = async () => {
    try {
      await updateStrategy({
        id,
        ...editFormData,
      }).unwrap();
      setEditDialog(false);
      refetch();
    } catch (err) {
      console.error("Failed to update strategy:", err);
    }
  };

  // Handle delete
  const handleDelete = async () => {
    try {
      await deleteStrategy(id).unwrap();
      navigate("/strategies");
    } catch (err) {
      console.error("Failed to delete strategy:", err);
    }
  };

  // Handle toggle active status
  const handleToggleActive = async () => {
    try {
      await updateStrategy({
        id,
        active: !strategy?.active,
      }).unwrap();
      refetch();
    } catch (err) {
      console.error("Failed to toggle strategy status:", err);
    }
  };

  // Mock data for demonstration (use real data when available)
  const mockPerformanceData = [
    { date: "2024-01", return: 5.2, benchmark: 3.1 },
    { date: "2024-02", return: 7.8, benchmark: 4.2 },
    { date: "2024-03", return: 6.5, benchmark: 3.8 },
    { date: "2024-04", return: 9.1, benchmark: 5.1 },
    { date: "2024-05", return: 8.3, benchmark: 4.7 },
    { date: "2024-06", return: 10.2, benchmark: 5.9 },
  ];

  const mockTrades = [
    {
      id: 1,
      symbol: "AAPL",
      type: "BUY",
      quantity: 100,
      price: 175.25,
      date: "2024-06-15",
      pnl: 1250.0,
    },
    {
      id: 2,
      symbol: "GOOGL",
      type: "SELL",
      quantity: 50,
      price: 142.8,
      date: "2024-06-14",
      pnl: -320.5,
    },
    {
      id: 3,
      symbol: "MSFT",
      type: "BUY",
      quantity: 75,
      price: 425.6,
      date: "2024-06-13",
      pnl: 890.25,
    },
  ];

  // Loading state
  if (isLoading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Skeleton variant="rectangular" height={200} sx={{ mb: 3 }} />
        <Grid container spacing={3}>
          {[1, 2, 3, 4].map((i) => (
            <Grid item xs={12} md={6} key={i}>
              <Skeleton variant="rectangular" height={150} />
            </Grid>
          ))}
        </Grid>
      </Container>
    );
  }

  // Error state
  if (error) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error">
          Failed to load strategy details. Please try again.
        </Alert>
        <Button
          startIcon={<ArrowLeft />}
          onClick={() => navigate("/strategies")}
          sx={{ mt: 2 }}
        >
          Back to Strategies
        </Button>
      </Container>
    );
  }

  // Use mock data if strategy is not available
  const displayStrategy = strategy || {
    id,
    name: "AI Momentum Strategy",
    description: "Machine learning-based momentum trading strategy",
    active: true,
    totalReturn: 23.5,
    monthlyReturn: 10.2,
    sharpeRatio: 1.85,
    maxDrawdown: -12.3,
    winRate: 68.5,
    avgTrade: 2.4,
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
          <IconButton onClick={() => navigate("/strategies")} sx={{ mr: 2 }}>
            <ArrowLeft />
          </IconButton>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h4" fontWeight="bold">
              {displayStrategy.name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {displayStrategy.description}
            </Typography>
          </Box>
          <Chip
            label={displayStrategy.active ? "Active" : "Inactive"}
            color={displayStrategy.active ? "success" : "default"}
            sx={{ mr: 2 }}
          />
          <Button
            variant="outlined"
            startIcon={displayStrategy.active ? <Pause /> : <Play />}
            onClick={handleToggleActive}
            sx={{ mr: 1 }}
          >
            {displayStrategy.active ? "Pause" : "Activate"}
          </Button>
          <IconButton onClick={handleEdit}>
            <Edit size={20} />
          </IconButton>
          <IconButton onClick={() => setDeleteDialog(true)} color="error">
            <Trash2 size={20} />
          </IconButton>
        </Box>
      </Paper>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                <TrendingUp size={20} style={{ marginRight: 8 }} />
                <Typography variant="body2" color="text.secondary">
                  Total Return
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight="bold" color="primary">
                {formatPercentage(displayStrategy.totalReturn)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                <Activity size={20} style={{ marginRight: 8 }} />
                <Typography variant="body2" color="text.secondary">
                  Sharpe Ratio
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight="bold">
                {displayStrategy.sharpeRatio?.toFixed(2) || "N/A"}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                <TrendingDown size={20} style={{ marginRight: 8 }} />
                <Typography variant="body2" color="text.secondary">
                  Max Drawdown
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight="bold" color="error">
                {formatPercentage(displayStrategy.maxDrawdown)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                <BarChart3 size={20} style={{ marginRight: 8 }} />
                <Typography variant="body2" color="text.secondary">
                  Win Rate
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight="bold">
                {formatPercentage(displayStrategy.winRate)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper elevation={2}>
        <Tabs
          value={selectedTab}
          onChange={handleTabChange}
          sx={{ borderBottom: 1, borderColor: "divider" }}
        >
          <Tab label="Performance" />
          <Tab label="Trades" />
          <Tab label="Risk Metrics" />
          <Tab label="Configuration" />
        </Tabs>

        {/* Tab Panels */}
        <Box sx={{ p: 3 }}>
          {/* Performance Tab */}
          {selectedTab === 0 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Performance Over Time
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={mockPerformanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="return"
                    stroke="#00f2fe"
                    fill="#00f2fe"
                    fillOpacity={0.3}
                    name="Strategy Return %"
                  />
                  <Area
                    type="monotone"
                    dataKey="benchmark"
                    stroke="#ff6b6b"
                    fill="#ff6b6b"
                    fillOpacity={0.3}
                    name="Benchmark %"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </Box>
          )}

          {/* Trades Tab */}
          {selectedTab === 1 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Recent Trades
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Symbol</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell align="right">Quantity</TableCell>
                      <TableCell align="right">Price</TableCell>
                      <TableCell>Date</TableCell>
                      <TableCell align="right">P&L</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {mockTrades.map((trade) => (
                      <TableRow key={trade.id}>
                        <TableCell>{trade.symbol}</TableCell>
                        <TableCell>
                          <Chip
                            label={trade.type}
                            color={trade.type === "BUY" ? "success" : "error"}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right">{trade.quantity}</TableCell>
                        <TableCell align="right">
                          {formatCurrency(trade.price)}
                        </TableCell>
                        <TableCell>{trade.date}</TableCell>
                        <TableCell
                          align="right"
                          sx={{
                            color:
                              trade.pnl >= 0 ? "success.main" : "error.main",
                          }}
                        >
                          {formatCurrency(trade.pnl)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}

          {/* Risk Metrics Tab */}
          {selectedTab === 2 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Risk Analysis
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Value at Risk (95%)
                    </Typography>
                    <Typography variant="h5">
                      {formatCurrency(riskMetrics?.var95 || -15420.5)}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Beta
                    </Typography>
                    <Typography variant="h5">
                      {riskMetrics?.beta?.toFixed(2) || "1.12"}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Volatility (Annualized)
                    </Typography>
                    <Typography variant="h5">
                      {formatPercentage(riskMetrics?.volatility || 18.5)}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Correlation to Market
                    </Typography>
                    <Typography variant="h5">
                      {riskMetrics?.correlation?.toFixed(2) || "0.72"}
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </Box>
          )}

          {/* Configuration Tab */}
          {selectedTab === 3 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Strategy Configuration
              </Typography>
              <Alert severity="info" sx={{ mb: 3 }}>
                <Typography variant="body2">
                  Configuration details are managed by the AI Engine. Contact
                  your administrator for advanced settings.
                </Typography>
              </Alert>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Strategy Type
                  </Typography>
                  <Typography variant="body1" paragraph>
                    Machine Learning - Momentum
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Model Version
                  </Typography>
                  <Typography variant="body1" paragraph>
                    v2.4.1
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Last Updated
                  </Typography>
                  <Typography variant="body1" paragraph>
                    2024-06-15 14:32:00
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Next Rebalance
                  </Typography>
                  <Typography variant="body1" paragraph>
                    2024-06-20 09:30:00
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          )}
        </Box>
      </Paper>

      {/* Edit Dialog */}
      <Dialog
        open={editDialog}
        onClose={() => setEditDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Edit Strategy</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Strategy Name"
            value={editFormData.name}
            onChange={(e) =>
              setEditFormData({ ...editFormData, name: e.target.value })
            }
            margin="normal"
          />
          <TextField
            fullWidth
            label="Description"
            value={editFormData.description}
            onChange={(e) =>
              setEditFormData({ ...editFormData, description: e.target.value })
            }
            margin="normal"
            multiline
            rows={3}
          />
          <FormControlLabel
            control={
              <Switch
                checked={editFormData.active}
                onChange={(e) =>
                  setEditFormData({ ...editFormData, active: e.target.checked })
                }
              />
            }
            label="Active"
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveEdit} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialog} onClose={() => setDeleteDialog(false)}>
        <DialogTitle>
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <AlertTriangle
              size={24}
              style={{ marginRight: 8, color: "#ff6b6b" }}
            />
            Delete Strategy?
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this strategy? This action cannot be
            undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog(false)}>Cancel</Button>
          <Button onClick={handleDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default StrategyDetails;
