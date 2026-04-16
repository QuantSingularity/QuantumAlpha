import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  Divider,
  Fade,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Snackbar,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Clock,
  DollarSign,
  TrendingDown,
  TrendingUp,
  Zap,
} from "lucide-react";
import { useState } from "react";
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
import Header from "../components/common/Header";

// ── Mock Data ────────────────────────────────────────────────────────────────
const mockQuotes = [
  {
    symbol: "AAPL",
    name: "Apple Inc.",
    price: 182.63,
    change: 2.45,
    changePct: 1.36,
    volume: "45.6M",
  },
  {
    symbol: "TSLA",
    name: "Tesla Inc.",
    price: 245.67,
    change: -4.23,
    changePct: -1.69,
    volume: "89.3M",
  },
  {
    symbol: "NVDA",
    name: "NVIDIA Corp.",
    price: 892.45,
    change: 18.72,
    changePct: 2.14,
    volume: "33.1M",
  },
  {
    symbol: "MSFT",
    name: "Microsoft Corp.",
    price: 337.42,
    change: 1.18,
    changePct: 0.35,
    volume: "21.8M",
  },
  {
    symbol: "GOOGL",
    name: "Alphabet Inc.",
    price: 141.8,
    change: -0.63,
    changePct: -0.44,
    volume: "18.4M",
  },
  {
    symbol: "AMZN",
    name: "Amazon.com Inc.",
    price: 178.25,
    change: 3.47,
    changePct: 1.98,
    volume: "28.7M",
  },
];

const generateChartData = (basePrice) => {
  const data = [];
  let price = basePrice * 0.92;
  const now = Date.now();
  for (let i = 30; i >= 0; i--) {
    price += (Math.random() - 0.45) * (basePrice * 0.008);
    data.push({
      time: new Date(now - i * 5 * 60 * 1000).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
      price: parseFloat(price.toFixed(2)),
    });
  }
  return data;
};

const orderTypes = ["Market", "Limit", "Stop", "Stop-Limit"];

const recentOrders = [
  {
    id: "ORD-001",
    symbol: "AAPL",
    side: "BUY",
    qty: 50,
    price: 180.2,
    status: "Filled",
    time: "10:32 AM",
  },
  {
    id: "ORD-002",
    symbol: "TSLA",
    side: "SELL",
    qty: 25,
    price: 249.9,
    status: "Filled",
    time: "10:15 AM",
  },
  {
    id: "ORD-003",
    symbol: "NVDA",
    side: "BUY",
    qty: 10,
    price: 890.0,
    status: "Pending",
    time: "09:58 AM",
  },
  {
    id: "ORD-004",
    symbol: "MSFT",
    side: "BUY",
    qty: 30,
    price: 336.0,
    status: "Cancelled",
    time: "09:40 AM",
  },
];

// ── Component ─────────────────────────────────────────────────────────────────
const Trading = () => {
  const [selectedSymbol, setSelectedSymbol] = useState(mockQuotes[0]);
  const [chartData] = useState(() => generateChartData(mockQuotes[0].price));
  const [orderSide, setOrderSide] = useState(0); // 0 = Buy, 1 = Sell
  const [orderType, setOrderType] = useState("Market");
  const [quantity, setQuantity] = useState("");
  const [limitPrice, setLimitPrice] = useState("");
  const [stopPrice, setStopPrice] = useState("");
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success",
  });
  const [orders, setOrders] = useState(recentOrders);

  const handleSelectSymbol = (q) => {
    setSelectedSymbol(q);
  };

  const estimatedTotal =
    quantity && selectedSymbol
      ? (
          parseFloat(quantity) *
          (orderType === "Market"
            ? selectedSymbol.price
            : parseFloat(limitPrice) || selectedSymbol.price)
        ).toFixed(2)
      : "—";

  const handlePlaceOrder = () => {
    if (!quantity || parseFloat(quantity) <= 0) {
      setSnackbar({
        open: true,
        message: "Please enter a valid quantity.",
        severity: "error",
      });
      return;
    }
    if (
      (orderType === "Limit" || orderType === "Stop-Limit") &&
      (!limitPrice || parseFloat(limitPrice) <= 0)
    ) {
      setSnackbar({
        open: true,
        message: "Please enter a valid limit price.",
        severity: "error",
      });
      return;
    }

    const newOrder = {
      id: `ORD-${String(orders.length + 5).padStart(3, "0")}`,
      symbol: selectedSymbol.symbol,
      side: orderSide === 0 ? "BUY" : "SELL",
      qty: parseFloat(quantity),
      price:
        orderType === "Market" ? selectedSymbol.price : parseFloat(limitPrice),
      status: orderType === "Market" ? "Filled" : "Pending",
      time: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };

    setOrders([newOrder, ...orders]);
    setSnackbar({
      open: true,
      message: `${newOrder.side} order for ${newOrder.qty} ${newOrder.symbol} placed successfully!`,
      severity: "success",
    });
    setQuantity("");
    setLimitPrice("");
    setStopPrice("");
  };

  const statusColor = (s) =>
    s === "Filled" ? "#10b981" : s === "Pending" ? "#f59e0b" : "#6b7280";

  return (
    <ErrorBoundary>
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Header
          title="Trading"
          subtitle="Place orders and monitor real-time market prices"
          breadcrumbs={[
            { label: "Dashboard", path: "/dashboard" },
            { label: "Trading" },
          ]}
        />

        <Grid container spacing={3}>
          {/* ── Quotes panel ── */}
          <Grid item xs={12} lg={3}>
            <Paper
              sx={{
                borderRadius: 3,
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.1)",
                overflow: "hidden",
              }}
            >
              <Box
                sx={{
                  p: 2.5,
                  borderBottom: "1px solid rgba(255,255,255,0.08)",
                }}
              >
                <Typography variant="h6" fontWeight={700} color="white">
                  Market Quotes
                </Typography>
              </Box>
              {mockQuotes.map((q) => (
                <Box
                  key={q.symbol}
                  onClick={() => handleSelectSymbol(q)}
                  sx={{
                    px: 2.5,
                    py: 2,
                    cursor: "pointer",
                    borderBottom: "1px solid rgba(255,255,255,0.05)",
                    background:
                      selectedSymbol.symbol === q.symbol
                        ? "rgba(0,212,255,0.08)"
                        : "transparent",
                    borderLeft:
                      selectedSymbol.symbol === q.symbol
                        ? "3px solid #00d4ff"
                        : "3px solid transparent",
                    transition: "all 0.2s",
                    "&:hover": { background: "rgba(255,255,255,0.06)" },
                  }}
                >
                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      mb: 0.5,
                    }}
                  >
                    <Typography
                      variant="subtitle2"
                      fontWeight={700}
                      color="white"
                    >
                      {q.symbol}
                    </Typography>
                    <Typography
                      variant="subtitle2"
                      fontWeight={700}
                      color="white"
                    >
                      ${q.price.toFixed(2)}
                    </Typography>
                  </Box>
                  <Box
                    sx={{ display: "flex", justifyContent: "space-between" }}
                  >
                    <Typography variant="caption" color="text.secondary">
                      {q.name.split(" ").slice(0, 2).join(" ")}
                    </Typography>
                    <Box
                      sx={{ display: "flex", alignItems: "center", gap: 0.5 }}
                    >
                      {q.change >= 0 ? (
                        <ArrowUpRight size={13} color="#10b981" />
                      ) : (
                        <ArrowDownRight size={13} color="#ef4444" />
                      )}
                      <Typography
                        variant="caption"
                        fontWeight={600}
                        sx={{ color: q.change >= 0 ? "#10b981" : "#ef4444" }}
                      >
                        {q.change >= 0 ? "+" : ""}
                        {q.changePct.toFixed(2)}%
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              ))}
            </Paper>
          </Grid>

          {/* ── Chart + Order Form ── */}
          <Grid item xs={12} lg={6}>
            <Fade in timeout={600}>
              <Paper
                sx={{
                  borderRadius: 3,
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.1)",
                  mb: 3,
                }}
              >
                <Box
                  sx={{
                    p: 3,
                    borderBottom: "1px solid rgba(255,255,255,0.08)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                  }}
                >
                  <Box>
                    <Typography variant="h5" fontWeight={800} color="white">
                      {selectedSymbol.symbol}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {selectedSymbol.name}
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: "right" }}>
                    <Typography variant="h4" fontWeight={800} color="white">
                      ${selectedSymbol.price.toFixed(2)}
                    </Typography>
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "flex-end",
                        gap: 0.5,
                      }}
                    >
                      {selectedSymbol.change >= 0 ? (
                        <TrendingUp size={16} color="#10b981" />
                      ) : (
                        <TrendingDown size={16} color="#ef4444" />
                      )}
                      <Typography
                        variant="body2"
                        fontWeight={700}
                        sx={{
                          color:
                            selectedSymbol.change >= 0 ? "#10b981" : "#ef4444",
                        }}
                      >
                        {selectedSymbol.change >= 0 ? "+" : ""}
                        {selectedSymbol.change.toFixed(2)} (
                        {selectedSymbol.changePct.toFixed(2)}%)
                      </Typography>
                    </Box>
                  </Box>
                </Box>
                <Box sx={{ p: 2, height: 260 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient
                          id="priceGrad"
                          x1="0"
                          y1="0"
                          x2="0"
                          y2="1"
                        >
                          <stop
                            offset="5%"
                            stopColor="#00d4ff"
                            stopOpacity={0.25}
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
                        stroke="rgba(255,255,255,0.06)"
                      />
                      <XAxis
                        dataKey="time"
                        stroke="rgba(255,255,255,0.5)"
                        fontSize={10}
                        tick={{ fontSize: 10 }}
                        interval={5}
                      />
                      <YAxis
                        stroke="rgba(255,255,255,0.5)"
                        fontSize={10}
                        domain={["auto", "auto"]}
                        tickFormatter={(v) => `$${v.toFixed(0)}`}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "rgba(0,0,0,0.85)",
                          border: "1px solid rgba(255,255,255,0.2)",
                          borderRadius: 8,
                          color: "white",
                        }}
                        formatter={(v) => [`$${v.toFixed(2)}`, "Price"]}
                      />
                      <Area
                        type="monotone"
                        dataKey="price"
                        stroke="#00d4ff"
                        strokeWidth={2}
                        fill="url(#priceGrad)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </Box>
                <Box sx={{ px: 3, pb: 2, display: "flex", gap: 3 }}>
                  {[
                    {
                      label: "Volume",
                      value: selectedSymbol.volume,
                      icon: Activity,
                    },
                    {
                      label: "Bid",
                      value: `$${(selectedSymbol.price - 0.05).toFixed(2)}`,
                      icon: TrendingDown,
                    },
                    {
                      label: "Ask",
                      value: `$${(selectedSymbol.price + 0.05).toFixed(2)}`,
                      icon: TrendingUp,
                    },
                    { label: "Spread", value: "$0.10", icon: BarChart3 },
                  ].map((m) => (
                    <Box key={m.label} sx={{ flex: 1, textAlign: "center" }}>
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        display="block"
                      >
                        {m.label}
                      </Typography>
                      <Typography
                        variant="body2"
                        fontWeight={700}
                        color="white"
                      >
                        {m.value}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              </Paper>
            </Fade>

            {/* Order Form */}
            <Paper
              sx={{
                borderRadius: 3,
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.1)",
                p: 3,
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  mb: 2.5,
                }}
              >
                <Typography variant="h6" fontWeight={700} color="white">
                  Place Order
                </Typography>
                <Chip
                  label={selectedSymbol.symbol}
                  size="small"
                  sx={{
                    background: "rgba(0,212,255,0.15)",
                    color: "#00d4ff",
                    fontWeight: 700,
                  }}
                />
              </Box>

              {/* Buy / Sell tabs */}
              <Tabs
                value={orderSide}
                onChange={(_, v) => setOrderSide(v)}
                sx={{
                  mb: 3,
                  "& .MuiTab-root": { fontWeight: 700, flex: 1 },
                  "& .Mui-selected": {
                    color:
                      orderSide === 0
                        ? "#10b981 !important"
                        : "#ef4444 !important",
                  },
                  "& .MuiTabs-indicator": {
                    background: orderSide === 0 ? "#10b981" : "#ef4444",
                  },
                }}
              >
                <Tab label="Buy" />
                <Tab label="Sell" />
              </Tabs>

              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormControl fullWidth size="small">
                    <InputLabel sx={{ color: "rgba(255,255,255,0.5)" }}>
                      Order Type
                    </InputLabel>
                    <Select
                      value={orderType}
                      label="Order Type"
                      onChange={(e) => setOrderType(e.target.value)}
                      sx={{
                        color: "white",
                        "& .MuiOutlinedInput-notchedOutline": {
                          borderColor: "rgba(255,255,255,0.2)",
                        },
                      }}
                    >
                      {orderTypes.map((t) => (
                        <MenuItem key={t} value={t}>
                          {t}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Quantity"
                    type="number"
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    inputProps={{ min: 1 }}
                    InputLabelProps={{ sx: { color: "rgba(255,255,255,0.5)" } }}
                    sx={{
                      "& .MuiOutlinedInput-root": {
                        color: "white",
                        "& fieldset": { borderColor: "rgba(255,255,255,0.2)" },
                        "&:hover fieldset": { borderColor: "#00d4ff" },
                        "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                      },
                    }}
                  />
                </Grid>
                {(orderType === "Limit" || orderType === "Stop-Limit") && (
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      size="small"
                      label="Limit Price"
                      type="number"
                      value={limitPrice}
                      onChange={(e) => setLimitPrice(e.target.value)}
                      InputLabelProps={{
                        sx: { color: "rgba(255,255,255,0.5)" },
                      }}
                      sx={{
                        "& .MuiOutlinedInput-root": {
                          color: "white",
                          "& fieldset": {
                            borderColor: "rgba(255,255,255,0.2)",
                          },
                          "&:hover fieldset": { borderColor: "#00d4ff" },
                          "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                        },
                      }}
                    />
                  </Grid>
                )}
                {(orderType === "Stop" || orderType === "Stop-Limit") && (
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      size="small"
                      label="Stop Price"
                      type="number"
                      value={stopPrice}
                      onChange={(e) => setStopPrice(e.target.value)}
                      InputLabelProps={{
                        sx: { color: "rgba(255,255,255,0.5)" },
                      }}
                      sx={{
                        "& .MuiOutlinedInput-root": {
                          color: "white",
                          "& fieldset": {
                            borderColor: "rgba(255,255,255,0.2)",
                          },
                          "&:hover fieldset": { borderColor: "#00d4ff" },
                          "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                        },
                      }}
                    />
                  </Grid>
                )}
                <Grid item xs={12}>
                  <Box
                    sx={{
                      p: 2,
                      borderRadius: 2,
                      background: "rgba(255,255,255,0.04)",
                      border: "1px solid rgba(255,255,255,0.1)",
                      display: "flex",
                      justifyContent: "space-between",
                    }}
                  >
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Market Price
                      </Typography>
                      <Typography
                        variant="body1"
                        fontWeight={700}
                        color="white"
                      >
                        ${selectedSymbol.price.toFixed(2)}
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: "right" }}>
                      <Typography variant="caption" color="text.secondary">
                        Est. Total
                      </Typography>
                      <Typography
                        variant="body1"
                        fontWeight={700}
                        color="#00d4ff"
                      >
                        {estimatedTotal !== "—"
                          ? `$${parseFloat(estimatedTotal).toLocaleString()}`
                          : "—"}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
                <Grid item xs={12}>
                  <Button
                    fullWidth
                    size="large"
                    onClick={handlePlaceOrder}
                    startIcon={
                      orderSide === 0 ? (
                        <TrendingUp size={18} />
                      ) : (
                        <TrendingDown size={18} />
                      )
                    }
                    sx={{
                      py: 1.6,
                      fontWeight: 700,
                      fontSize: "1rem",
                      borderRadius: 2,
                      background:
                        orderSide === 0
                          ? "linear-gradient(45deg, #10b981, #059669)"
                          : "linear-gradient(45deg, #ef4444, #dc2626)",
                      color: "white",
                      boxShadow: `0 4px 20px ${orderSide === 0 ? "#10b98150" : "#ef444450"}`,
                      "&:hover": {
                        transform: "translateY(-2px)",
                        boxShadow: `0 6px 25px ${orderSide === 0 ? "#10b98170" : "#ef444470"}`,
                      },
                    }}
                  >
                    {orderSide === 0 ? "Place Buy Order" : "Place Sell Order"}
                  </Button>
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          {/* ── Order Book / History ── */}
          <Grid item xs={12} lg={3}>
            <Paper
              sx={{
                borderRadius: 3,
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.1)",
                overflow: "hidden",
              }}
            >
              <Box
                sx={{
                  p: 2.5,
                  borderBottom: "1px solid rgba(255,255,255,0.08)",
                  display: "flex",
                  alignItems: "center",
                  gap: 1,
                }}
              >
                <Clock size={16} color="#00d4ff" />
                <Typography variant="h6" fontWeight={700} color="white">
                  Order History
                </Typography>
              </Box>
              <Box
                sx={{
                  p: 2,
                  display: "flex",
                  flexDirection: "column",
                  gap: 1.5,
                }}
              >
                {orders.map((o) => (
                  <Card
                    key={o.id}
                    sx={{
                      background: "rgba(255,255,255,0.03)",
                      border: "1px solid rgba(255,255,255,0.08)",
                      borderRadius: 2,
                    }}
                  >
                    <CardContent sx={{ p: "12px !important" }}>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          mb: 0.5,
                        }}
                      >
                        <Box
                          sx={{ display: "flex", alignItems: "center", gap: 1 }}
                        >
                          <Typography
                            variant="subtitle2"
                            fontWeight={700}
                            color="white"
                          >
                            {o.symbol}
                          </Typography>
                          <Chip
                            label={o.side}
                            size="small"
                            sx={{
                              height: 18,
                              fontSize: "0.65rem",
                              fontWeight: 700,
                              background:
                                o.side === "BUY" ? "#10b98125" : "#ef444425",
                              color: o.side === "BUY" ? "#10b981" : "#ef4444",
                              border: `1px solid ${o.side === "BUY" ? "#10b98140" : "#ef444440"}`,
                            }}
                          />
                        </Box>
                        <Chip
                          label={o.status}
                          size="small"
                          sx={{
                            height: 18,
                            fontSize: "0.65rem",
                            background: `${statusColor(o.status)}25`,
                            color: statusColor(o.status),
                          }}
                        />
                      </Box>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                        }}
                      >
                        <Typography variant="caption" color="text.secondary">
                          {o.qty} shares @ ${o.price.toFixed(2)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {o.time}
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            </Paper>

            {/* Account Summary */}
            <Paper
              sx={{
                mt: 3,
                p: 3,
                borderRadius: 3,
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.1)",
              }}
            >
              <Box
                sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}
              >
                <DollarSign size={16} color="#00d4ff" />
                <Typography variant="h6" fontWeight={700} color="white">
                  Account
                </Typography>
              </Box>
              <Divider sx={{ mb: 2, borderColor: "rgba(255,255,255,0.08)" }} />
              {[
                {
                  label: "Buying Power",
                  value: "$48,235.00",
                  color: "#10b981",
                },
                { label: "Cash Balance", value: "$52,100.00", color: "white" },
                { label: "Margin Used", value: "$3,865.00", color: "#f59e0b" },
                { label: "Open P&L", value: "+$2,847.32", color: "#10b981" },
              ].map((item) => (
                <Box
                  key={item.label}
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    mb: 1.5,
                  }}
                >
                  <Typography variant="body2" color="text.secondary">
                    {item.label}
                  </Typography>
                  <Typography
                    variant="body2"
                    fontWeight={700}
                    sx={{ color: item.color }}
                  >
                    {item.value}
                  </Typography>
                </Box>
              ))}
            </Paper>
          </Grid>
        </Grid>
      </Container>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          variant="filled"
          icon={<Zap size={16} />}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </ErrorBoundary>
  );
};

export default Trading;
