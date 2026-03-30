import {
  Alert,
  Autocomplete,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Fade,
  Grid,
  IconButton,
  Menu,
  MenuItem,
  Paper,
  Snackbar,
  TextField,
  Typography,
} from "@mui/material";
import {
  Activity,
  Bell,
  Delete,
  Eye,
  MoreVertical,
  Plus,
  Search,
  SortAsc,
  SortDesc,
  Star,
  Target,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { useEffect, useState } from "react";

const Watchlist = () => {
  const [watchlistItems, setWatchlistItems] = useState([
    {
      id: 1,
      symbol: "AAPL",
      name: "Apple Inc.",
      price: 182.1,
      change: 2.45,
      changePercent: 1.36,
      volume: 45678900,
      marketCap: "2.85T",
      pe: 28.5,
      alerts: [
        { type: "price", value: 185, condition: "above" },
        { type: "price", value: 175, condition: "below" },
      ],
      addedDate: new Date("2024-01-15"),
      category: "Tech",
    },
    {
      id: 2,
      symbol: "TSLA",
      name: "Tesla, Inc.",
      price: 245.67,
      change: -3.21,
      changePercent: -1.29,
      volume: 32145600,
      marketCap: "780B",
      pe: 65.2,
      alerts: [{ type: "price", value: 250, condition: "above" }],
      addedDate: new Date("2024-01-20"),
      category: "Auto",
    },
    {
      id: 3,
      symbol: "GOOGL",
      name: "Alphabet Inc.",
      price: 138.45,
      change: 1.87,
      changePercent: 1.37,
      volume: 28934500,
      marketCap: "1.75T",
      pe: 24.8,
      alerts: [],
      addedDate: new Date("2024-02-01"),
      category: "Tech",
    },
    {
      id: 4,
      symbol: "MSFT",
      name: "Microsoft Corporation",
      price: 378.92,
      change: 4.56,
      changePercent: 1.22,
      volume: 19876543,
      marketCap: "2.81T",
      pe: 32.1,
      alerts: [{ type: "volume", value: 25000000, condition: "above" }],
      addedDate: new Date("2024-01-10"),
      category: "Tech",
    },
    {
      id: 5,
      symbol: "NVDA",
      name: "NVIDIA Corporation",
      price: 456.78,
      change: 12.34,
      changePercent: 2.78,
      volume: 41234567,
      marketCap: "1.12T",
      pe: 58.9,
      alerts: [],
      addedDate: new Date("2024-02-05"),
      category: "Tech",
    },
  ]);

  const [filteredItems, setFilteredItems] = useState(watchlistItems);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState("symbol");
  const [sortOrder, setSortOrder] = useState("asc");
  const [filterCategory, setFilterCategory] = useState("All");
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [_alertDialogOpen, _setAlertDialogOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [newSymbol, setNewSymbol] = useState("");
  const [anchorEl, setAnchorEl] = useState(null);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success",
  });

  const categories = ["All", "Tech", "Auto", "Finance", "Healthcare", "Energy"];
  const popularSymbols = [
    "AAPL",
    "TSLA",
    "GOOGL",
    "MSFT",
    "NVDA",
    "AMZN",
    "META",
    "NFLX",
    "AMD",
    "INTC",
  ];

  useEffect(() => {
    let filtered = watchlistItems;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(
        (item) =>
          item.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.name.toLowerCase().includes(searchTerm.toLowerCase()),
      );
    }

    // Filter by category
    if (filterCategory !== "All") {
      filtered = filtered.filter((item) => item.category === filterCategory);
    }

    // Sort
    filtered.sort((a, b) => {
      let aValue = a[sortBy];
      let bValue = b[sortBy];

      if (typeof aValue === "string") {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (sortOrder === "asc") {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    setFilteredItems(filtered);
  }, [watchlistItems, searchTerm, sortBy, sortOrder, filterCategory]);

  const addToWatchlist = () => {
    if (!newSymbol.trim()) return;

    const newItem = {
      id: Date.now(),
      symbol: newSymbol.toUpperCase(),
      name: `${newSymbol.toUpperCase()} Corporation`,
      price: Math.random() * 500 + 50,
      change: (Math.random() - 0.5) * 10,
      changePercent: (Math.random() - 0.5) * 5,
      volume: Math.floor(Math.random() * 50000000) + 1000000,
      marketCap: `${(Math.random() * 2 + 0.1).toFixed(1)}T`,
      pe: Math.random() * 50 + 10,
      alerts: [],
      addedDate: new Date(),
      category: "Tech",
    };

    setWatchlistItems((prev) => [...prev, newItem]);
    setNewSymbol("");
    setAddDialogOpen(false);
    setSnackbar({
      open: true,
      message: `${newSymbol.toUpperCase()} added to watchlist`,
      severity: "success",
    });
  };

  const removeFromWatchlist = (id) => {
    setWatchlistItems((prev) => prev.filter((item) => item.id !== id));
    setSnackbar({
      open: true,
      message: "Item removed from watchlist",
      severity: "info",
    });
  };

  const handleMenuClick = (event, item) => {
    setAnchorEl(event.currentTarget);
    setSelectedItem(item);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedItem(null);
  };

  const formatNumber = (num) => {
    if (num >= 1e9) return `${(num / 1e9).toFixed(1)}B`;
    if (num >= 1e6) return `${(num / 1e6).toFixed(1)}M`;
    if (num >= 1e3) return `${(num / 1e3).toFixed(1)}K`;
    return num.toString();
  };

  const WatchlistItem = ({ item }) => {
    const isPositive = item.change >= 0;
    const changeColor = isPositive ? "#10b981" : "#ef4444";
    const TrendIcon = isPositive ? TrendingUp : TrendingDown;

    return (
      <Fade in={true} timeout={500}>
        <Card
          sx={{
            mb: 2,
            background: "rgba(255, 255, 255, 0.05)",
            backdropFilter: "blur(20px)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
            transition: "all 0.3s ease",
            "&:hover": {
              transform: "translateY(-2px)",
              boxShadow: "0 8px 25px rgba(0, 212, 255, 0.15)",
              border: "1px solid rgba(0, 212, 255, 0.3)",
            },
          }}
        >
          <CardContent sx={{ p: 3 }}>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={3}>
                <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                  <Avatar
                    sx={{
                      bgcolor: "#00d4ff20",
                      color: "#00d4ff",
                      fontWeight: 700,
                    }}
                  >
                    {item.symbol[0]}
                  </Avatar>
                  <Box>
                    <Typography variant="h6" fontWeight={700} color="white">
                      {item.symbol}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {item.name}
                    </Typography>
                  </Box>
                </Box>
              </Grid>

              <Grid item xs={6} sm={2}>
                <Typography variant="h6" fontWeight={700} color="white">
                  ${item.price.toFixed(2)}
                </Typography>
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                  <TrendIcon size={14} color={changeColor} />
                  <Typography
                    variant="body2"
                    color={changeColor}
                    fontWeight={600}
                  >
                    {isPositive ? "+" : ""}
                    {item.change.toFixed(2)} ({isPositive ? "+" : ""}
                    {item.changePercent.toFixed(2)}%)
                  </Typography>
                </Box>
              </Grid>

              <Grid item xs={6} sm={2}>
                <Typography variant="body2" color="text.secondary">
                  Volume
                </Typography>
                <Typography variant="body1" color="white" fontWeight={600}>
                  {formatNumber(item.volume)}
                </Typography>
              </Grid>

              <Grid item xs={6} sm={2}>
                <Typography variant="body2" color="text.secondary">
                  Market Cap
                </Typography>
                <Typography variant="body1" color="white" fontWeight={600}>
                  {item.marketCap}
                </Typography>
              </Grid>

              <Grid item xs={6} sm={2}>
                <Box
                  sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}
                >
                  <Chip
                    label={item.category}
                    size="small"
                    sx={{
                      background: "#00d4ff20",
                      color: "#00d4ff",
                      fontWeight: 600,
                    }}
                  />
                  {item.alerts.length > 0 && (
                    <Chip
                      icon={<Bell size={12} />}
                      label={item.alerts.length}
                      size="small"
                      sx={{
                        background: "#f59e0b20",
                        color: "#f59e0b",
                        fontWeight: 600,
                      }}
                    />
                  )}
                </Box>
                <Typography variant="caption" color="text.secondary">
                  P/E: {item.pe.toFixed(1)}
                </Typography>
              </Grid>

              <Grid item xs={12} sm={1}>
                <IconButton
                  onClick={(e) => handleMenuClick(e, item)}
                  sx={{ color: "#00d4ff" }}
                >
                  <MoreVertical size={20} />
                </IconButton>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Fade>
    );
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background:
          "linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%)",
        py: 4,
      }}
    >
      <Box sx={{ maxWidth: 1400, mx: "auto", px: 3 }}>
        {/* Header */}
        <Fade in={true} timeout={800}>
          <Paper
            elevation={0}
            sx={{
              p: 4,
              mb: 4,
              borderRadius: 4,
              background: "rgba(255, 255, 255, 0.05)",
              backdropFilter: "blur(20px)",
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
              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <Star size={32} color="#00d4ff" />
                <Box>
                  <Typography variant="h4" fontWeight={700} color="white">
                    My Watchlist
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Track your favorite stocks and assets
                  </Typography>
                </Box>
              </Box>
              <Button
                variant="contained"
                startIcon={<Plus size={20} />}
                onClick={() => setAddDialogOpen(true)}
                sx={{
                  px: 3,
                  py: 1.5,
                  fontWeight: 600,
                  background: "linear-gradient(45deg, #00d4ff, #0099cc)",
                  "&:hover": {
                    background: "linear-gradient(45deg, #0099cc, #0066aa)",
                  },
                }}
              >
                Add Symbol
              </Button>
            </Box>

            {/* Filters and Search */}
            <Grid container spacing={3} alignItems="center">
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  placeholder="Search symbols or companies..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <Search
                        size={20}
                        color="#00d4ff"
                        style={{ marginRight: 8 }}
                      />
                    ),
                  }}
                  sx={{
                    "& .MuiOutlinedInput-root": {
                      background: "rgba(255, 255, 255, 0.05)",
                      "& fieldset": { borderColor: "rgba(255, 255, 255, 0.2)" },
                      "&:hover fieldset": { borderColor: "#00d4ff" },
                      "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                    },
                    "& .MuiOutlinedInput-input": { color: "white" },
                  }}
                />
              </Grid>
              <Grid item xs={12} md={2}>
                <Autocomplete
                  value={filterCategory}
                  onChange={(_e, newValue) => setFilterCategory(newValue)}
                  options={categories}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Category"
                      sx={{
                        "& .MuiOutlinedInput-root": {
                          background: "rgba(255, 255, 255, 0.05)",
                          "& fieldset": {
                            borderColor: "rgba(255, 255, 255, 0.2)",
                          },
                          "&:hover fieldset": { borderColor: "#00d4ff" },
                          "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                        },
                        "& .MuiInputLabel-root": {
                          color: "rgba(255, 255, 255, 0.7)",
                        },
                        "& .MuiOutlinedInput-input": { color: "white" },
                      }}
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12} md={2}>
                <Autocomplete
                  value={sortBy}
                  onChange={(_e, newValue) => setSortBy(newValue)}
                  options={["symbol", "price", "change", "volume", "marketCap"]}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Sort By"
                      sx={{
                        "& .MuiOutlinedInput-root": {
                          background: "rgba(255, 255, 255, 0.05)",
                          "& fieldset": {
                            borderColor: "rgba(255, 255, 255, 0.2)",
                          },
                          "&:hover fieldset": { borderColor: "#00d4ff" },
                          "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                        },
                        "& .MuiInputLabel-root": {
                          color: "rgba(255, 255, 255, 0.7)",
                        },
                        "& .MuiOutlinedInput-input": { color: "white" },
                      }}
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12} md={1}>
                <IconButton
                  onClick={() =>
                    setSortOrder(sortOrder === "asc" ? "desc" : "asc")
                  }
                  sx={{ color: "#00d4ff" }}
                >
                  {sortOrder === "asc" ? (
                    <SortAsc size={24} />
                  ) : (
                    <SortDesc size={24} />
                  )}
                </IconButton>
              </Grid>
              <Grid item xs={12} md={3}>
                <Box sx={{ display: "flex", gap: 1 }}>
                  <Chip
                    label={`${filteredItems.length} items`}
                    sx={{
                      background: "#00d4ff20",
                      color: "#00d4ff",
                      fontWeight: 600,
                    }}
                  />
                  <Chip
                    label={`${watchlistItems.filter((item) => item.alerts.length > 0).length} with alerts`}
                    sx={{
                      background: "#f59e0b20",
                      color: "#f59e0b",
                      fontWeight: 600,
                    }}
                  />
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Fade>

        {/* Watchlist Items */}
        <Box>
          {filteredItems.map((item) => (
            <WatchlistItem key={item.id} item={item} />
          ))}
        </Box>

        {filteredItems.length === 0 && (
          <Fade in={true} timeout={1000}>
            <Paper
              elevation={0}
              sx={{
                p: 6,
                textAlign: "center",
                borderRadius: 4,
                background: "rgba(255, 255, 255, 0.05)",
                backdropFilter: "blur(20px)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
              }}
            >
              <Star size={64} color="#6b7280" style={{ marginBottom: 16 }} />
              <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
                No items in your watchlist
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Add some symbols to start tracking your favorite stocks
              </Typography>
              <Button
                variant="contained"
                startIcon={<Plus size={20} />}
                onClick={() => setAddDialogOpen(true)}
                sx={{
                  px: 3,
                  py: 1.5,
                  fontWeight: 600,
                  background: "linear-gradient(45deg, #00d4ff, #0099cc)",
                  "&:hover": {
                    background: "linear-gradient(45deg, #0099cc, #0066aa)",
                  },
                }}
              >
                Add Your First Symbol
              </Button>
            </Paper>
          </Fade>
        )}

        {/* Add Symbol Dialog */}
        <Dialog
          open={addDialogOpen}
          onClose={() => setAddDialogOpen(false)}
          PaperProps={{
            sx: {
              background: "rgba(0, 0, 0, 0.9)",
              backdropFilter: "blur(20px)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: 3,
              minWidth: 400,
            },
          }}
        >
          <DialogTitle sx={{ color: "white", fontWeight: 700 }}>
            Add to Watchlist
          </DialogTitle>
          <DialogContent>
            <Autocomplete
              freeSolo
              options={popularSymbols}
              value={newSymbol}
              onInputChange={(_e, newValue) => setNewSymbol(newValue)}
              renderInput={(params) => (
                <TextField
                  {...params}
                  autoFocus
                  margin="dense"
                  label="Symbol"
                  placeholder="Enter stock symbol (e.g., AAPL)"
                  fullWidth
                  variant="outlined"
                  sx={{
                    mt: 2,
                    "& .MuiOutlinedInput-root": {
                      background: "rgba(255, 255, 255, 0.05)",
                      "& fieldset": { borderColor: "rgba(255, 255, 255, 0.2)" },
                      "&:hover fieldset": { borderColor: "#00d4ff" },
                      "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                    },
                    "& .MuiInputLabel-root": {
                      color: "rgba(255, 255, 255, 0.7)",
                    },
                    "& .MuiOutlinedInput-input": { color: "white" },
                  }}
                />
              )}
            />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Popular symbols: {popularSymbols.join(", ")}
            </Typography>
          </DialogContent>
          <DialogActions sx={{ p: 3 }}>
            <Button
              onClick={() => setAddDialogOpen(false)}
              sx={{ color: "text.secondary" }}
            >
              Cancel
            </Button>
            <Button
              onClick={addToWatchlist}
              variant="contained"
              disabled={!newSymbol.trim()}
              sx={{
                background: "linear-gradient(45deg, #00d4ff, #0099cc)",
                "&:hover": {
                  background: "linear-gradient(45deg, #0099cc, #0066aa)",
                },
              }}
            >
              Add to Watchlist
            </Button>
          </DialogActions>
        </Dialog>

        {/* Context Menu */}
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
          <MenuItem onClick={handleMenuClose} sx={{ color: "white" }}>
            <Eye size={16} style={{ marginRight: 8 }} />
            View Details
          </MenuItem>
          <MenuItem onClick={handleMenuClose} sx={{ color: "white" }}>
            <Target size={16} style={{ marginRight: 8 }} />
            Set Alert
          </MenuItem>
          <MenuItem onClick={handleMenuClose} sx={{ color: "white" }}>
            <Activity size={16} style={{ marginRight: 8 }} />
            View Chart
          </MenuItem>
          <Divider sx={{ backgroundColor: "rgba(255, 255, 255, 0.1)" }} />
          <MenuItem
            onClick={() => {
              if (selectedItem) {
                removeFromWatchlist(selectedItem.id);
              }
              handleMenuClose();
            }}
            sx={{ color: "#ef4444" }}
          >
            <Delete size={16} style={{ marginRight: 8 }} />
            Remove from Watchlist
          </MenuItem>
        </Menu>

        {/* Snackbar */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={3000}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        >
          <Alert
            onClose={() => setSnackbar({ ...snackbar, open: false })}
            severity={snackbar.severity}
            sx={{
              background: "rgba(0, 0, 0, 0.9)",
              backdropFilter: "blur(20px)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              color: "white",
            }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    </Box>
  );
};

export default Watchlist;
