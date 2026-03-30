import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  CardMedia,
  Chip,
  Fade,
  Grid,
  IconButton,
  InputAdornment,
  Menu,
  MenuItem,
  Paper,
  Skeleton,
  Snackbar,
  TextField,
  Typography,
} from "@mui/material";
import {
  Bookmark,
  BookmarkCheck,
  Clock,
  ExternalLink,
  Eye,
  Globe,
  MessageCircle,
  MoreVertical,
  Newspaper,
  RotateCcw,
  Search,
  Share,
  ThumbsUp,
  TrendingDown,
  TrendingUp,
  Zap,
} from "lucide-react";
import { useEffect, useState } from "react";

const NewsFeed = () => {
  const [newsItems, setNewsItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [bookmarkedItems, setBookmarkedItems] = useState(new Set());
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success",
  });

  const categories = [
    "All",
    "Markets",
    "Technology",
    "Crypto",
    "Economy",
    "Earnings",
    "Analysis",
  ];

  // Mock news data
  const mockNews = [
    {
      id: 1,
      title: "Apple Reports Record Q4 Earnings, Beats Wall Street Expectations",
      summary:
        "Apple Inc. reported quarterly earnings that exceeded analyst expectations, driven by strong iPhone sales and services revenue growth.",
      content:
        "Apple Inc. (AAPL) announced its fourth-quarter financial results today, reporting revenue of $89.5 billion, up 8% year-over-year...",
      source: "Financial Times",
      author: "Sarah Johnson",
      publishedAt: new Date(Date.now() - 2 * 60 * 60 * 1000),
      category: "Earnings",
      imageUrl:
        "https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=400&h=200&fit=crop",
      sentiment: "positive",
      views: 15420,
      likes: 342,
      comments: 89,
      tags: ["AAPL", "Earnings", "Technology"],
      readTime: "3 min read",
    },
    {
      id: 2,
      title: "Federal Reserve Signals Potential Rate Cut in December Meeting",
      summary:
        "Fed officials hint at possible interest rate reduction following recent inflation data showing continued cooling.",
      content:
        "The Federal Reserve indicated today that a rate cut may be on the table for the December FOMC meeting...",
      source: "Reuters",
      author: "Michael Chen",
      publishedAt: new Date(Date.now() - 4 * 60 * 60 * 1000),
      category: "Economy",
      imageUrl:
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=400&h=200&fit=crop",
      sentiment: "neutral",
      views: 23150,
      likes: 567,
      comments: 234,
      tags: ["Fed", "Interest Rates", "Economy"],
      readTime: "5 min read",
    },
    {
      id: 3,
      title: "Tesla Stock Surges 12% on Autonomous Vehicle Breakthrough",
      summary:
        "Tesla shares jumped after the company announced significant progress in its Full Self-Driving technology.",
      content:
        "Tesla Inc. (TSLA) shares soared in after-hours trading following the companys announcement of a major breakthrough...",
      source: "Bloomberg",
      author: "David Rodriguez",
      publishedAt: new Date(Date.now() - 6 * 60 * 60 * 1000),
      category: "Technology",
      imageUrl:
        "https://images.unsplash.com/photo-1560958089-b8a1929cea89?w=400&h=200&fit=crop",
      sentiment: "positive",
      views: 31240,
      likes: 892,
      comments: 156,
      tags: ["TSLA", "Autonomous Vehicles", "Technology"],
      readTime: "4 min read",
    },
    {
      id: 4,
      title: "Bitcoin Reaches New All-Time High Above $75,000",
      summary:
        "Cryptocurrency markets rally as Bitcoin breaks previous records amid institutional adoption.",
      content:
        "Bitcoin (BTC) reached a new all-time high of $75,234 today, surpassing its previous record set in 2021...",
      source: "CoinDesk",
      author: "Emma Thompson",
      publishedAt: new Date(Date.now() - 8 * 60 * 60 * 1000),
      category: "Crypto",
      imageUrl:
        "https://images.unsplash.com/photo-1518544866330-4e4815de2e3c?w=400&h=200&fit=crop",
      sentiment: "positive",
      views: 45670,
      likes: 1234,
      comments: 445,
      tags: ["Bitcoin", "Cryptocurrency", "ATH"],
      readTime: "2 min read",
    },
    {
      id: 5,
      title: "Global Markets Mixed as Investors Await Inflation Data",
      summary:
        "Stock markets show mixed performance ahead of key inflation reports from major economies.",
      content:
        "Global equity markets displayed mixed performance today as investors positioned themselves ahead of crucial inflation data...",
      source: "Wall Street Journal",
      author: "Robert Kim",
      publishedAt: new Date(Date.now() - 12 * 60 * 60 * 1000),
      category: "Markets",
      imageUrl:
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=400&h=200&fit=crop",
      sentiment: "neutral",
      views: 18930,
      likes: 234,
      comments: 67,
      tags: ["Markets", "Inflation", "Global"],
      readTime: "6 min read",
    },
    {
      id: 6,
      title: "NVIDIA Announces Next-Generation AI Chips for Data Centers",
      summary:
        "NVIDIA unveils new GPU architecture promising 10x performance improvement for AI workloads.",
      content:
        "NVIDIA Corporation (NVDA) today announced its next-generation GPU architecture designed specifically for AI and machine learning...",
      source: "TechCrunch",
      author: "Lisa Wang",
      publishedAt: new Date(Date.now() - 18 * 60 * 60 * 1000),
      category: "Technology",
      imageUrl:
        "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=200&fit=crop",
      sentiment: "positive",
      views: 27840,
      likes: 678,
      comments: 123,
      tags: ["NVDA", "AI", "Technology"],
      readTime: "4 min read",
    },
  ];

  useEffect(() => {
    // Simulate loading news
    setLoading(true);
    setTimeout(() => {
      setNewsItems(mockNews);
      setLoading(false);
    }, 1500);
  }, [mockNews]);

  const filteredNews = newsItems.filter((item) => {
    const matchesSearch =
      item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.tags.some((tag) =>
        tag.toLowerCase().includes(searchTerm.toLowerCase()),
      );
    const matchesCategory =
      selectedCategory === "All" || item.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const toggleBookmark = (id) => {
    const newBookmarks = new Set(bookmarkedItems);
    if (newBookmarks.has(id)) {
      newBookmarks.delete(id);
      setSnackbar({
        open: true,
        message: "Article removed from bookmarks",
        severity: "info",
      });
    } else {
      newBookmarks.add(id);
      setSnackbar({
        open: true,
        message: "Article bookmarked",
        severity: "success",
      });
    }
    setBookmarkedItems(newBookmarks);
  };

  const handleMenuClick = (event, article) => {
    setAnchorEl(event.currentTarget);
    setSelectedArticle(article);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedArticle(null);
  };

  const shareArticle = () => {
    if (selectedArticle) {
      navigator.clipboard.writeText(
        `${selectedArticle.title} - ${window.location.origin}`,
      );
      setSnackbar({
        open: true,
        message: "Article link copied to clipboard",
        severity: "success",
      });
    }
    handleMenuClose();
  };

  const formatTimeAgo = (date) => {
    const now = new Date();
    const diff = now - date;
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor(diff / (1000 * 60));

    if (hours > 24) {
      const days = Math.floor(hours / 24);
      return `${days} day${days > 1 ? "s" : ""} ago`;
    } else if (hours > 0) {
      return `${hours} hour${hours > 1 ? "s" : ""} ago`;
    } else {
      return `${minutes} minute${minutes > 1 ? "s" : ""} ago`;
    }
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case "positive":
        return "#10b981";
      case "negative":
        return "#ef4444";
      default:
        return "#6b7280";
    }
  };

  const getSentimentIcon = (sentiment) => {
    switch (sentiment) {
      case "positive":
        return <TrendingUp size={16} />;
      case "negative":
        return <TrendingDown size={16} />;
      default:
        return <Globe size={16} />;
    }
  };

  const NewsCard = ({ article }) => (
    <Fade in={true} timeout={500}>
      <Card
        sx={{
          mb: 3,
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
        <Grid container>
          <Grid item xs={12} md={4}>
            <CardMedia
              component="img"
              height="200"
              image={article.imageUrl}
              alt={article.title}
              sx={{
                borderRadius: "12px 0 0 12px",
                objectFit: "cover",
              }}
            />
          </Grid>
          <Grid item xs={12} md={8}>
            <CardContent
              sx={{
                p: 3,
                height: "100%",
                display: "flex",
                flexDirection: "column",
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  mb: 2,
                }}
              >
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Chip
                    label={article.category}
                    size="small"
                    sx={{
                      background: "#00d4ff20",
                      color: "#00d4ff",
                      fontWeight: 600,
                    }}
                  />
                  <Chip
                    icon={getSentimentIcon(article.sentiment)}
                    label={article.sentiment}
                    size="small"
                    sx={{
                      background: `${getSentimentColor(article.sentiment)}20`,
                      color: getSentimentColor(article.sentiment),
                      fontWeight: 600,
                    }}
                  />
                </Box>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <IconButton
                    onClick={() => toggleBookmark(article.id)}
                    sx={{
                      color: bookmarkedItems.has(article.id)
                        ? "#f59e0b"
                        : "#6b7280",
                    }}
                  >
                    {bookmarkedItems.has(article.id) ? (
                      <BookmarkCheck size={20} />
                    ) : (
                      <Bookmark size={20} />
                    )}
                  </IconButton>
                  <IconButton
                    onClick={(e) => handleMenuClick(e, article)}
                    sx={{ color: "#00d4ff" }}
                  >
                    <MoreVertical size={20} />
                  </IconButton>
                </Box>
              </Box>

              <Typography
                variant="h6"
                fontWeight={700}
                color="white"
                sx={{ mb: 2, lineHeight: 1.3 }}
              >
                {article.title}
              </Typography>

              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mb: 2, flex: 1 }}
              >
                {article.summary}
              </Typography>

              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  mb: 2,
                }}
              >
                <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                  <Avatar sx={{ width: 24, height: 24, fontSize: "0.8rem" }}>
                    {article.author[0]}
                  </Avatar>
                  <Typography variant="caption" color="text.secondary">
                    {article.author} • {article.source}
                  </Typography>
                </Box>
                <Typography variant="caption" color="text.secondary">
                  {article.readTime}
                </Typography>
              </Box>

              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                    <Clock size={14} color="#6b7280" />
                    <Typography variant="caption" color="text.secondary">
                      {formatTimeAgo(article.publishedAt)}
                    </Typography>
                  </Box>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                    <Eye size={14} color="#6b7280" />
                    <Typography variant="caption" color="text.secondary">
                      {article.views.toLocaleString()}
                    </Typography>
                  </Box>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                    <ThumbsUp size={14} color="#6b7280" />
                    <Typography variant="caption" color="text.secondary">
                      {article.likes}
                    </Typography>
                  </Box>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                    <MessageCircle size={14} color="#6b7280" />
                    <Typography variant="caption" color="text.secondary">
                      {article.comments}
                    </Typography>
                  </Box>
                </Box>
                <Button
                  size="small"
                  endIcon={<ExternalLink size={16} />}
                  sx={{
                    color: "#00d4ff",
                    fontWeight: 600,
                    "&:hover": {
                      background: "rgba(0, 212, 255, 0.1)",
                    },
                  }}
                >
                  Read More
                </Button>
              </Box>

              <Box sx={{ display: "flex", gap: 1, mt: 2, flexWrap: "wrap" }}>
                {article.tags.map((tag) => (
                  <Chip
                    key={tag}
                    label={tag}
                    size="small"
                    variant="outlined"
                    sx={{
                      borderColor: "rgba(255, 255, 255, 0.2)",
                      color: "rgba(255, 255, 255, 0.7)",
                      fontSize: "0.7rem",
                    }}
                  />
                ))}
              </Box>
            </CardContent>
          </Grid>
        </Grid>
      </Card>
    </Fade>
  );

  const LoadingSkeleton = () => (
    <Card sx={{ mb: 3, background: "rgba(255, 255, 255, 0.05)" }}>
      <Grid container>
        <Grid item xs={12} md={4}>
          <Skeleton
            variant="rectangular"
            height={200}
            sx={{ bgcolor: "rgba(255, 255, 255, 0.1)" }}
          />
        </Grid>
        <Grid item xs={12} md={8}>
          <CardContent sx={{ p: 3 }}>
            <Skeleton
              variant="text"
              width="60%"
              sx={{ bgcolor: "rgba(255, 255, 255, 0.1)", mb: 1 }}
            />
            <Skeleton
              variant="text"
              width="100%"
              sx={{ bgcolor: "rgba(255, 255, 255, 0.1)", mb: 1 }}
            />
            <Skeleton
              variant="text"
              width="80%"
              sx={{ bgcolor: "rgba(255, 255, 255, 0.1)", mb: 2 }}
            />
            <Skeleton
              variant="text"
              width="40%"
              sx={{ bgcolor: "rgba(255, 255, 255, 0.1)" }}
            />
          </CardContent>
        </Grid>
      </Grid>
    </Card>
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
      <Box sx={{ maxWidth: 1200, mx: "auto", px: 3 }}>
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
                <Newspaper size={32} color="#00d4ff" />
                <Box>
                  <Typography variant="h4" fontWeight={700} color="white">
                    Financial News
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Stay updated with the latest market news and analysis
                  </Typography>
                </Box>
              </Box>
              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <Chip
                  icon={<Zap size={16} />}
                  label="Live Updates"
                  sx={{
                    background: "linear-gradient(45deg, #10b981, #059669)",
                    color: "white",
                    fontWeight: 600,
                    animation: "pulse 2s infinite",
                    "@keyframes pulse": {
                      "0%": { opacity: 1 },
                      "50%": { opacity: 0.7 },
                      "100%": { opacity: 1 },
                    },
                  }}
                />
                <IconButton
                  onClick={() => window.location.reload()}
                  sx={{ color: "#00d4ff" }}
                >
                  <RotateCcw size={24} />
                </IconButton>
              </Box>
            </Box>

            {/* Search and Filters */}
            <Grid container spacing={3} alignItems="center">
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  placeholder="Search news, companies, or topics..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Search size={20} color="#00d4ff" />
                      </InputAdornment>
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
              <Grid item xs={12} md={6}>
                <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
                  {categories.map((category) => (
                    <Chip
                      key={category}
                      label={category}
                      onClick={() => setSelectedCategory(category)}
                      sx={{
                        background:
                          selectedCategory === category
                            ? "linear-gradient(45deg, #00d4ff, #0099cc)"
                            : "rgba(255, 255, 255, 0.1)",
                        color: "white",
                        fontWeight: selectedCategory === category ? 700 : 500,
                        "&:hover": {
                          background:
                            selectedCategory === category
                              ? "linear-gradient(45deg, #0099cc, #0066aa)"
                              : "rgba(255, 255, 255, 0.2)",
                        },
                      }}
                    />
                  ))}
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Fade>

        {/* News Feed */}
        <Box>
          {loading ? (
            Array.from({ length: 3 }).map((_, index) => (
              <LoadingSkeleton key={index} />
            ))
          ) : filteredNews.length > 0 ? (
            filteredNews.map((article) => (
              <NewsCard key={article.id} article={article} />
            ))
          ) : (
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
                <Newspaper
                  size={64}
                  color="#6b7280"
                  style={{ marginBottom: 16 }}
                />
                <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
                  No news articles found
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Try adjusting your search terms or category filters
                </Typography>
              </Paper>
            </Fade>
          )}
        </Box>

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
          <MenuItem onClick={shareArticle} sx={{ color: "white" }}>
            <Share size={16} style={{ marginRight: 8 }} />
            Share Article
          </MenuItem>
          <MenuItem onClick={handleMenuClose} sx={{ color: "white" }}>
            <ExternalLink size={16} style={{ marginRight: 8 }} />
            Open in New Tab
          </MenuItem>
          <MenuItem
            onClick={() => {
              if (selectedArticle) {
                toggleBookmark(selectedArticle.id);
              }
              handleMenuClose();
            }}
            sx={{ color: "white" }}
          >
            {selectedArticle && bookmarkedItems.has(selectedArticle.id) ? (
              <>
                <BookmarkCheck size={16} style={{ marginRight: 8 }} />
                Remove Bookmark
              </>
            ) : (
              <>
                <Bookmark size={16} style={{ marginRight: 8 }} />
                Add Bookmark
              </>
            )}
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

export default NewsFeed;
