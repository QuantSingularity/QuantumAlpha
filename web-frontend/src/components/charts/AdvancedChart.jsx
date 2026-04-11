import {
  Box,
  Button,
  ButtonGroup,
  Card,
  CardContent,
  Chip,
  Fade,
  Grid,
  IconButton,
  Menu,
  MenuItem,
  Paper,
  Typography,
} from "@mui/material";
import {
  BarChart3,
  Download,
  Eye,
  EyeOff,
  Maximize2,
  Minimize2,
  MoreVertical,
  Settings,
  Target,
  TrendingUp,
  Zap,
} from "lucide-react";
import { useRef, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts";

const AdvancedChart = ({
  symbol = "AAPL",
  title = "Advanced Trading Chart",
}) => {
  const [chartType, setChartType] = useState("line");
  const [timeframe, setTimeframe] = useState("1D");
  const [indicators, setIndicators] = useState({
    sma: true,
    ema: false,
    bollinger: false,
    rsi: false,
    macd: false,
    volume: true,
  });
  const [anchorEl, setAnchorEl] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef(null);

  // Mock data for demonstration
  const [chartData, _setChartData] = useState([
    {
      time: "09:30",
      open: 175.2,
      high: 176.5,
      low: 174.8,
      close: 176.2,
      volume: 1200000,
      sma: 175.5,
      ema: 175.8,
    },
    {
      time: "10:00",
      open: 176.2,
      high: 177.1,
      low: 175.9,
      close: 176.8,
      volume: 980000,
      sma: 175.7,
      ema: 176.0,
    },
    {
      time: "10:30",
      open: 176.8,
      high: 178.2,
      low: 176.5,
      close: 177.9,
      volume: 1100000,
      sma: 176.0,
      ema: 176.3,
    },
    {
      time: "11:00",
      open: 177.9,
      high: 178.5,
      low: 177.2,
      close: 178.1,
      volume: 850000,
      sma: 176.3,
      ema: 176.7,
    },
    {
      time: "11:30",
      open: 178.1,
      high: 179.0,
      low: 177.8,
      close: 178.7,
      volume: 920000,
      sma: 176.6,
      ema: 177.1,
    },
    {
      time: "12:00",
      open: 178.7,
      high: 179.2,
      low: 178.3,
      close: 178.9,
      volume: 760000,
      sma: 176.9,
      ema: 177.5,
    },
    {
      time: "12:30",
      open: 178.9,
      high: 179.8,
      low: 178.6,
      close: 179.4,
      volume: 890000,
      sma: 177.2,
      ema: 177.9,
    },
    {
      time: "13:00",
      open: 179.4,
      high: 180.1,
      low: 179.0,
      close: 179.8,
      volume: 1050000,
      sma: 177.5,
      ema: 178.3,
    },
    {
      time: "13:30",
      open: 179.8,
      high: 180.5,
      low: 179.3,
      close: 180.2,
      volume: 970000,
      sma: 177.8,
      ema: 178.7,
    },
    {
      time: "14:00",
      open: 180.2,
      high: 181.0,
      low: 179.9,
      close: 180.6,
      volume: 1150000,
      sma: 178.1,
      ema: 179.1,
    },
    {
      time: "14:30",
      open: 180.6,
      high: 181.2,
      low: 180.1,
      close: 180.9,
      volume: 820000,
      sma: 178.4,
      ema: 179.5,
    },
    {
      time: "15:00",
      open: 180.9,
      high: 181.5,
      low: 180.4,
      close: 181.2,
      volume: 940000,
      sma: 178.7,
      ema: 179.9,
    },
    {
      time: "15:30",
      open: 181.2,
      high: 182.0,
      low: 180.8,
      close: 181.7,
      volume: 1080000,
      sma: 179.0,
      ema: 180.3,
    },
    {
      time: "16:00",
      open: 181.7,
      high: 182.3,
      low: 181.4,
      close: 182.1,
      volume: 1200000,
      sma: 179.3,
      ema: 180.7,
    },
  ]);

  const toggleIndicator = (indicator) => {
    setIndicators((prev) => ({
      ...prev,
      [indicator]: !prev[indicator],
    }));
  };

  const handleMenuClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const exportChart = () => {
    const dataStr = JSON.stringify(chartData, null, 2);
    const dataUri =
      "data:application/json;charset=utf-8," + encodeURIComponent(dataStr);
    const link = document.createElement("a");
    link.setAttribute("href", dataUri);
    link.setAttribute("download", `${symbol}-chart-data.json`);
    link.click();
    handleMenuClose();
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current
        ?.requestFullscreen()
        .then(() => setIsFullscreen(true))
        .catch(() => setIsFullscreen((v) => !v));
    } else {
      document
        .exitFullscreen()
        .then(() => setIsFullscreen(false))
        .catch(() => setIsFullscreen((v) => !v));
    }
  };

  const _CustomCandlestick = (props) => {
    const { payload, x, y, width, height } = props;
    if (!payload) return null;

    const { open, close, high, low } = payload;
    const isGreen = close > open;
    const color = isGreen ? "#10b981" : "#ef4444";
    const bodyHeight = Math.abs(close - open);
    const _bodyY = Math.min(open, close);

    return (
      <g>
        {/* Wick */}
        <line
          x1={x + width / 2}
          y1={y + ((high - Math.max(open, close)) * height) / (high - low)}
          x2={x + width / 2}
          y2={y + ((high - Math.min(open, close)) * height) / (high - low)}
          stroke={color}
          strokeWidth={1}
        />
        {/* Body */}
        <rect
          x={x + width * 0.2}
          y={y + ((high - Math.max(open, close)) * height) / (high - low)}
          width={width * 0.6}
          height={(bodyHeight * height) / (high - low)}
          fill={color}
          stroke={color}
        />
      </g>
    );
  };

  const renderChart = () => {
    switch (chartType) {
      case "line":
        return (
          <LineChart data={chartData}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255,255,255,0.1)"
            />
            <XAxis
              dataKey="time"
              stroke="rgba(255,255,255,0.7)"
              fontSize={12}
            />
            <YAxis
              stroke="rgba(255,255,255,0.7)"
              fontSize={12}
              domain={["dataMin - 1", "dataMax + 1"]}
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
            <Line
              type="monotone"
              dataKey="close"
              stroke="#00d4ff"
              strokeWidth={2}
              dot={false}
              name="Price"
            />
            {indicators.sma && (
              <Line
                type="monotone"
                dataKey="sma"
                stroke="#f59e0b"
                strokeWidth={1}
                strokeDasharray="5 5"
                dot={false}
                name="SMA"
              />
            )}
            {indicators.ema && (
              <Line
                type="monotone"
                dataKey="ema"
                stroke="#8b5cf6"
                strokeWidth={1}
                strokeDasharray="3 3"
                dot={false}
                name="EMA"
              />
            )}
          </LineChart>
        );

      case "area":
        return (
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255,255,255,0.1)"
            />
            <XAxis
              dataKey="time"
              stroke="rgba(255,255,255,0.7)"
              fontSize={12}
            />
            <YAxis
              stroke="rgba(255,255,255,0.7)"
              fontSize={12}
              domain={["dataMin - 1", "dataMax + 1"]}
            />
            <RechartsTooltip
              contentStyle={{
                backgroundColor: "rgba(0, 0, 0, 0.8)",
                border: "1px solid rgba(255, 255, 255, 0.2)",
                borderRadius: "8px",
                color: "white",
              }}
            />
            <Area
              type="monotone"
              dataKey="close"
              stroke="#00d4ff"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorPrice)"
            />
          </AreaChart>
        );

      case "bar":
        return (
          <BarChart data={chartData}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255,255,255,0.1)"
            />
            <XAxis
              dataKey="time"
              stroke="rgba(255,255,255,0.7)"
              fontSize={12}
            />
            <YAxis stroke="rgba(255,255,255,0.7)" fontSize={12} />
            <RechartsTooltip
              contentStyle={{
                backgroundColor: "rgba(0, 0, 0, 0.8)",
                border: "1px solid rgba(255, 255, 255, 0.2)",
                borderRadius: "8px",
                color: "white",
              }}
            />
            <Bar dataKey="volume" fill="#00d4ff" />
          </BarChart>
        );

      default: // candlestick
        return (
          <LineChart data={chartData}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255,255,255,0.1)"
            />
            <XAxis
              dataKey="time"
              stroke="rgba(255,255,255,0.7)"
              fontSize={12}
            />
            <YAxis
              stroke="rgba(255,255,255,0.7)"
              fontSize={12}
              domain={["dataMin - 1", "dataMax + 1"]}
            />
            <RechartsTooltip
              contentStyle={{
                backgroundColor: "rgba(0, 0, 0, 0.8)",
                border: "1px solid rgba(255, 255, 255, 0.2)",
                borderRadius: "8px",
                color: "white",
              }}
              formatter={(value, name) => {
                if (name === "high") return [`H: $${value}`, "High"];
                if (name === "low") return [`L: $${value}`, "Low"];
                if (name === "open") return [`O: $${value}`, "Open"];
                if (name === "close") return [`C: $${value}`, "Close"];
                return [value, name];
              }}
            />
            <Line type="monotone" dataKey="high" stroke="transparent" />
            <Line type="monotone" dataKey="low" stroke="transparent" />
            <Line type="monotone" dataKey="open" stroke="transparent" />
            <Line
              type="monotone"
              dataKey="close"
              stroke="#00d4ff"
              strokeWidth={2}
              dot={false}
            />
            {indicators.sma && (
              <Line
                type="monotone"
                dataKey="sma"
                stroke="#f59e0b"
                strokeWidth={1}
                strokeDasharray="5 5"
                dot={false}
                name="SMA"
              />
            )}
          </LineChart>
        );
    }
  };

  return (
    <Fade in={true} timeout={1000}>
      <Paper
        ref={containerRef}
        elevation={0}
        sx={{
          p: 3,
          borderRadius: 4,
          background: "rgba(255, 255, 255, 0.05)",
          backdropFilter: "blur(20px)",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",
          height: isFullscreen ? "100vh" : "auto",
        }}
      >
        {/* Header */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            mb: 3,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <Typography variant="h6" fontWeight={700} color="white">
              {title} - {symbol}
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
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <ButtonGroup size="small" sx={{ mr: 2 }}>
              {["1D", "1W", "1M", "3M", "1Y"].map((tf) => (
                <Button
                  key={tf}
                  variant={timeframe === tf ? "contained" : "outlined"}
                  onClick={() => setTimeframe(tf)}
                  sx={{
                    borderColor: "#00d4ff",
                    color: timeframe === tf ? "white" : "#00d4ff",
                    background:
                      timeframe === tf
                        ? "linear-gradient(45deg, #00d4ff, #0099cc)"
                        : "transparent",
                    "&:hover": {
                      borderColor: "#00d4ff",
                      background:
                        timeframe === tf
                          ? "linear-gradient(45deg, #0099cc, #0066aa)"
                          : "rgba(0, 212, 255, 0.1)",
                    },
                  }}
                >
                  {tf}
                </Button>
              ))}
            </ButtonGroup>
            <IconButton onClick={toggleFullscreen} sx={{ color: "#00d4ff" }}>
              {isFullscreen ? <Minimize2 size={20} /> : <Maximize2 size={20} />}
            </IconButton>
            <IconButton onClick={handleMenuClick} sx={{ color: "#00d4ff" }}>
              <MoreVertical size={20} />
            </IconButton>
          </Box>
        </Box>

        {/* Chart Type Selector */}
        <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3 }}>
          <ButtonGroup size="small">
            {[
              { type: "candlestick", label: "Candlestick", icon: BarChart3 },
              { type: "line", label: "Line", icon: TrendingUp },
              { type: "area", label: "Area", icon: Activity },
              { type: "bar", label: "Volume", icon: BarChart3 },
            ].map(({ type, label, icon: Icon }) => (
              <Button
                key={type}
                variant={chartType === type ? "contained" : "outlined"}
                startIcon={<Icon size={16} />}
                onClick={() => setChartType(type)}
                sx={{
                  borderColor: "#00d4ff",
                  color: chartType === type ? "white" : "#00d4ff",
                  background:
                    chartType === type
                      ? "linear-gradient(45deg, #00d4ff, #0099cc)"
                      : "transparent",
                  "&:hover": {
                    borderColor: "#00d4ff",
                    background:
                      chartType === type
                        ? "linear-gradient(45deg, #0099cc, #0066aa)"
                        : "rgba(0, 212, 255, 0.1)",
                  },
                }}
              >
                {label}
              </Button>
            ))}
          </ButtonGroup>
        </Box>

        {/* Indicators */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
            mb: 3,
            flexWrap: "wrap",
          }}
        >
          <Typography variant="body2" color="text.secondary" sx={{ mr: 2 }}>
            Indicators:
          </Typography>
          {Object.entries(indicators).map(([key, enabled]) => (
            <Chip
              key={key}
              label={key.toUpperCase()}
              onClick={() => toggleIndicator(key)}
              icon={enabled ? <Eye size={14} /> : <EyeOff size={14} />}
              sx={{
                background: enabled
                  ? "linear-gradient(45deg, #00d4ff, #0099cc)"
                  : "rgba(255, 255, 255, 0.1)",
                color: "white",
                fontWeight: 500,
                "&:hover": {
                  background: enabled
                    ? "linear-gradient(45deg, #0099cc, #0066aa)"
                    : "rgba(255, 255, 255, 0.2)",
                },
              }}
            />
          ))}
        </Box>

        {/* Chart */}
        <Box sx={{ height: isFullscreen ? 600 : 400, width: "100%" }}>
          <ResponsiveContainer width="100%" height="100%">
            {renderChart()}
          </ResponsiveContainer>
        </Box>

        {/* Volume Chart (if enabled) */}
        {indicators.volume && chartType !== "bar" && (
          <Box sx={{ height: 100, width: "100%", mt: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Volume
            </Typography>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <XAxis dataKey="time" hide />
                <YAxis hide />
                <Bar dataKey="volume" fill="#00d4ff" opacity={0.6} />
              </BarChart>
            </ResponsiveContainer>
          </Box>
        )}

        {/* Stats */}
        <Grid container spacing={2} sx={{ mt: 2 }}>
          <Grid item xs={6} sm={3}>
            <Card
              sx={{
                background: "rgba(16, 185, 129, 0.1)",
                border: "1px solid rgba(16, 185, 129, 0.3)",
              }}
            >
              <CardContent sx={{ p: 2, textAlign: "center" }}>
                <Typography variant="body2" color="text.secondary">
                  Open
                </Typography>
                <Typography variant="h6" color="#10b981" fontWeight={700}>
                  ${chartData[0]?.open.toFixed(2)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card
              sx={{
                background: "rgba(239, 68, 68, 0.1)",
                border: "1px solid rgba(239, 68, 68, 0.3)",
              }}
            >
              <CardContent sx={{ p: 2, textAlign: "center" }}>
                <Typography variant="body2" color="text.secondary">
                  High
                </Typography>
                <Typography variant="h6" color="#ef4444" fontWeight={700}>
                  ${Math.max(...chartData.map((d) => d.high)).toFixed(2)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card
              sx={{
                background: "rgba(59, 130, 246, 0.1)",
                border: "1px solid rgba(59, 130, 246, 0.3)",
              }}
            >
              <CardContent sx={{ p: 2, textAlign: "center" }}>
                <Typography variant="body2" color="text.secondary">
                  Low
                </Typography>
                <Typography variant="h6" color="#3b82f6" fontWeight={700}>
                  ${Math.min(...chartData.map((d) => d.low)).toFixed(2)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card
              sx={{
                background: "rgba(0, 212, 255, 0.1)",
                border: "1px solid rgba(0, 212, 255, 0.3)",
              }}
            >
              <CardContent sx={{ p: 2, textAlign: "center" }}>
                <Typography variant="body2" color="text.secondary">
                  Close
                </Typography>
                <Typography variant="h6" color="#00d4ff" fontWeight={700}>
                  ${chartData[chartData.length - 1]?.close.toFixed(2)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          PaperProps={{
            sx: {
              background: "rgba(0, 0, 0, 0.9)",
              backdropFilter: "blur(20px)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: 2,
            },
          }}
        >
          <MenuItem onClick={exportChart} sx={{ color: "white" }}>
            <Download size={16} style={{ marginRight: 8 }} />
            Export Chart
          </MenuItem>
          <MenuItem onClick={handleMenuClose} sx={{ color: "white" }}>
            <Settings size={16} style={{ marginRight: 8 }} />
            Chart Settings
          </MenuItem>
          <MenuItem onClick={handleMenuClose} sx={{ color: "white" }}>
            <Target size={16} style={{ marginRight: 8 }} />
            Add Alert
          </MenuItem>
        </Menu>
      </Paper>
    </Fade>
  );
};

export default AdvancedChart;
