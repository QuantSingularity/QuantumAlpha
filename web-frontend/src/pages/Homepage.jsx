import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  Divider,
  Fade,
  Grid,
  Paper,
  Typography,
} from "@mui/material";
import {
  Activity,
  ArrowRight,
  BarChart3,
  Brain,
  ChevronRight,
  DollarSign,
  Globe,
  Lock,
  Shield,
  TrendingUp,
  Zap,
} from "lucide-react";
import { useSelector } from "react-redux";
import { Link as RouterLink, useNavigate } from "react-router-dom";

// Mock live stats for the hero
const liveStats = [
  { label: "Assets Under Management", value: "$4.8B+", color: "#00d4ff" },
  { label: "Active Traders", value: "128K+", color: "#10b981" },
  { label: "Avg. Annual Return", value: "34.2%", color: "#f59e0b" },
  { label: "Uptime", value: "99.99%", color: "#8b5cf6" },
];

const features = [
  {
    icon: Brain,
    title: "AI-Powered Strategies",
    description:
      "Deep learning models trained on decades of market data generate alpha in any market condition.",
    color: "#00d4ff",
  },
  {
    icon: Zap,
    title: "Microsecond Execution",
    description:
      "Co-located servers and optimised order routing ensure your trades execute at the best possible price.",
    color: "#f59e0b",
  },
  {
    icon: Shield,
    title: "Quantum Risk Engine",
    description:
      "Real-time portfolio risk analysis with VaR, CVaR and stress-testing powered by quantum algorithms.",
    color: "#10b981",
  },
  {
    icon: BarChart3,
    title: "Advanced Analytics",
    description:
      "Interactive charts, factor attribution and custom reports give you full transparency into performance.",
    color: "#8b5cf6",
  },
  {
    icon: Globe,
    title: "Global Markets",
    description:
      "Trade equities, ETFs, forex, crypto and derivatives across 60+ exchanges worldwide, 24/7.",
    color: "#ef4444",
  },
  {
    icon: Lock,
    title: "Bank-Grade Security",
    description:
      "SOC 2 Type II certified infrastructure with MFA, hardware key support and end-to-end encryption.",
    color: "#06b6d4",
  },
];

const testimonials = [
  {
    name: "Sarah Chen",
    role: "Quant Fund Manager",
    text: "QuantumAlpha transformed our execution workflow. We reduced slippage by 47% in the first month.",
    avatar: "SC",
    return: "+41% YTD",
  },
  {
    name: "Marcus Webb",
    role: "Proprietary Trader",
    text: "The AI strategy builder is lightyears ahead of anything else on the market. My win rate jumped from 58% to 74%.",
    avatar: "MW",
    return: "+67% YTD",
  },
  {
    name: "Priya Nair",
    role: "Hedge Fund CTO",
    text: "Onboarding was seamless and the API is beautifully documented. Our team was live in under a week.",
    avatar: "PN",
    return: "+29% YTD",
  },
];

const pricingPlans = [
  {
    name: "Starter",
    price: "$29",
    period: "/month",
    description:
      "Perfect for individual traders getting started with algo trading.",
    features: [
      "Up to 3 active strategies",
      "Real-time market data",
      "Basic analytics dashboard",
      "Email support",
      "Paper trading mode",
    ],
    color: "#00d4ff",
    popular: false,
  },
  {
    name: "Pro",
    price: "$99",
    period: "/month",
    description:
      "For serious traders who need advanced tools and higher limits.",
    features: [
      "Unlimited strategies",
      "AI strategy builder",
      "Advanced risk analytics",
      "WebSocket streaming API",
      "Priority support",
      "Custom indicators",
    ],
    color: "#10b981",
    popular: true,
  },
  {
    name: "Institutional",
    price: "Custom",
    period: "",
    description: "Tailored solutions for hedge funds and trading firms.",
    features: [
      "Everything in Pro",
      "Dedicated infrastructure",
      "White-label options",
      "Co-location services",
      "Dedicated account manager",
      "SLA guarantee",
    ],
    color: "#8b5cf6",
    popular: false,
  },
];

const Homepage = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useSelector((state) => state.auth);

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background:
          "linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%)",
        color: "white",
      }}
    >
      {/* ── Nav Bar ─────────────────────────────────────────────────── */}
      <Box
        component="nav"
        sx={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          zIndex: 1000,
          backdropFilter: "blur(20px)",
          borderBottom: "1px solid rgba(255,255,255,0.08)",
          background: "rgba(15,15,35,0.85)",
        }}
      >
        <Container maxWidth="lg">
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              py: 2,
            }}
          >
            <Typography
              variant="h5"
              fontWeight={800}
              sx={{
                background: "linear-gradient(45deg, #00d4ff, #ff00ff)",
                backgroundClip: "text",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                cursor: "pointer",
              }}
              onClick={() => navigate("/")}
            >
              QuantumAlpha
            </Typography>

            <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
              {isAuthenticated ? (
                <Button
                  variant="contained"
                  endIcon={<ArrowRight size={16} />}
                  onClick={() => navigate("/dashboard")}
                  sx={{
                    background: "linear-gradient(45deg, #00d4ff, #0099cc)",
                    fontWeight: 600,
                    px: 3,
                    borderRadius: 2,
                  }}
                >
                  Go to Dashboard
                </Button>
              ) : (
                <>
                  <Button
                    component={RouterLink}
                    to="/login"
                    sx={{ color: "rgba(255,255,255,0.8)", fontWeight: 500 }}
                  >
                    Sign In
                  </Button>
                  <Button
                    component={RouterLink}
                    to="/register"
                    variant="contained"
                    sx={{
                      background: "linear-gradient(45deg, #00d4ff, #0099cc)",
                      fontWeight: 600,
                      px: 3,
                      borderRadius: 2,
                    }}
                  >
                    Get Started
                  </Button>
                </>
              )}
            </Box>
          </Box>
        </Container>
      </Box>

      {/* ── Hero ────────────────────────────────────────────────────── */}
      <Box sx={{ pt: { xs: 14, md: 18 }, pb: 10 }}>
        <Container maxWidth="lg">
          <Fade in timeout={800}>
            <Box sx={{ textAlign: "center", mb: 8 }}>
              <Chip
                label="🚀 Now with Quantum AI v3.0"
                sx={{
                  mb: 3,
                  background: "rgba(0,212,255,0.15)",
                  color: "#00d4ff",
                  border: "1px solid rgba(0,212,255,0.3)",
                  fontWeight: 600,
                  fontSize: "0.85rem",
                }}
              />
              <Typography
                variant="h1"
                fontWeight={800}
                sx={{
                  background:
                    "linear-gradient(45deg, #00d4ff, #ff00ff, #00ff88)",
                  backgroundClip: "text",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  mb: 3,
                  fontSize: { xs: "2.8rem", md: "4.5rem" },
                  lineHeight: 1.1,
                }}
              >
                The Future of
                <br />
                Algorithmic Trading
              </Typography>
              <Typography
                variant="h5"
                color="text.secondary"
                sx={{
                  maxWidth: 680,
                  mx: "auto",
                  mb: 5,
                  lineHeight: 1.6,
                  fontWeight: 300,
                }}
              >
                Harness quantum-enhanced AI strategies, microsecond execution,
                and institutional-grade risk management — all in one platform.
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
                  component={RouterLink}
                  to={isAuthenticated ? "/dashboard" : "/register"}
                  variant="contained"
                  size="large"
                  endIcon={<ArrowRight size={20} />}
                  sx={{
                    px: 5,
                    py: 1.8,
                    fontWeight: 700,
                    fontSize: "1.1rem",
                    background: "linear-gradient(45deg, #00d4ff, #0099cc)",
                    boxShadow: "0 4px 25px rgba(0,212,255,0.4)",
                    borderRadius: 3,
                    "&:hover": {
                      boxShadow: "0 6px 35px rgba(0,212,255,0.55)",
                      transform: "translateY(-2px)",
                    },
                  }}
                >
                  {isAuthenticated ? "Open Dashboard" : "Start Trading Free"}
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  sx={{
                    px: 5,
                    py: 1.8,
                    fontWeight: 600,
                    fontSize: "1.1rem",
                    borderColor: "rgba(255,255,255,0.3)",
                    color: "white",
                    borderRadius: 3,
                    "&:hover": {
                      borderColor: "#00d4ff",
                      background: "rgba(0,212,255,0.08)",
                    },
                  }}
                  onClick={() =>
                    document
                      .getElementById("features")
                      ?.scrollIntoView({ behavior: "smooth" })
                  }
                >
                  Explore Features
                </Button>
              </Box>
            </Box>
          </Fade>

          {/* Live Stats Bar */}
          <Fade in timeout={1200}>
            <Paper
              sx={{
                p: 4,
                borderRadius: 4,
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.1)",
                backdropFilter: "blur(10px)",
              }}
            >
              <Grid container spacing={3} justifyContent="center">
                {liveStats.map((stat) => (
                  <Grid
                    item
                    xs={6}
                    md={3}
                    key={stat.label}
                    sx={{ textAlign: "center" }}
                  >
                    <Typography
                      variant="h3"
                      fontWeight={800}
                      sx={{
                        color: stat.color,
                        mb: 0.5,
                        fontSize: { xs: "1.8rem", md: "2.2rem" },
                      }}
                    >
                      {stat.value}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {stat.label}
                    </Typography>
                  </Grid>
                ))}
              </Grid>
            </Paper>
          </Fade>
        </Container>
      </Box>

      {/* ── Features ────────────────────────────────────────────────── */}
      <Box id="features" sx={{ py: 12, background: "rgba(0,0,0,0.3)" }}>
        <Container maxWidth="lg">
          <Box sx={{ textAlign: "center", mb: 8 }}>
            <Typography
              variant="h2"
              fontWeight={800}
              color="white"
              sx={{ mb: 2 }}
            >
              Everything You Need to
              <Box
                component="span"
                sx={{
                  background: "linear-gradient(45deg, #00d4ff, #0099cc)",
                  backgroundClip: "text",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  ml: 1.5,
                }}
              >
                Trade Smarter
              </Box>
            </Typography>
            <Typography
              variant="h6"
              color="text.secondary"
              sx={{ maxWidth: 540, mx: "auto", fontWeight: 300 }}
            >
              A complete suite of institutional-grade tools designed for modern
              algorithmic traders.
            </Typography>
          </Box>

          <Grid container spacing={3}>
            {features.map((feature) => (
              <Grid item xs={12} sm={6} md={4} key={feature.title}>
                <Fade in timeout={1000}>
                  <Card
                    sx={{
                      height: "100%",
                      background: "rgba(255,255,255,0.04)",
                      border: `1px solid ${feature.color}25`,
                      borderRadius: 3,
                      transition: "all 0.3s ease",
                      cursor: "default",
                      "&:hover": {
                        background: `rgba(${feature.color === "#00d4ff" ? "0,212,255" : feature.color === "#f59e0b" ? "245,158,11" : feature.color === "#10b981" ? "16,185,129" : feature.color === "#8b5cf6" ? "139,92,246" : feature.color === "#ef4444" ? "239,68,68" : "6,182,212"},0.08)`,
                        borderColor: feature.color,
                        transform: "translateY(-6px)",
                        boxShadow: `0 12px 30px ${feature.color}20`,
                      },
                    }}
                  >
                    <CardContent sx={{ p: 4 }}>
                      <Box
                        sx={{
                          width: 56,
                          height: 56,
                          borderRadius: 2,
                          background: `${feature.color}15`,
                          border: `1px solid ${feature.color}30`,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          mb: 3,
                        }}
                      >
                        <feature.icon size={28} color={feature.color} />
                      </Box>
                      <Typography
                        variant="h6"
                        fontWeight={700}
                        color="white"
                        sx={{ mb: 1.5 }}
                      >
                        {feature.title}
                      </Typography>
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{ lineHeight: 1.7 }}
                      >
                        {feature.description}
                      </Typography>
                    </CardContent>
                  </Card>
                </Fade>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* ── Performance Showcase ─────────────────────────────────────── */}
      <Box sx={{ py: 12 }}>
        <Container maxWidth="lg">
          <Grid container spacing={6} alignItems="center">
            <Grid item xs={12} md={5}>
              <Typography
                variant="h2"
                fontWeight={800}
                color="white"
                sx={{ mb: 3 }}
              >
                Proven
                <Box
                  component="span"
                  sx={{
                    display: "block",
                    background: "linear-gradient(45deg, #10b981, #00d4ff)",
                    backgroundClip: "text",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                  }}
                >
                  Performance
                </Box>
              </Typography>
              <Typography
                variant="body1"
                color="text.secondary"
                sx={{ mb: 4, lineHeight: 1.8 }}
              >
                Our AI strategies have consistently outperformed market
                benchmarks across all volatility regimes. Backtested on 20+
                years of tick-level data.
              </Typography>
              {[
                { label: "Sharpe Ratio", value: "2.4×", color: "#00d4ff" },
                { label: "Max Drawdown", value: "< 8%", color: "#10b981" },
                { label: "Win Rate", value: "73.5%", color: "#f59e0b" },
                {
                  label: "Alpha vs S&P 500",
                  value: "+22.8%",
                  color: "#8b5cf6",
                },
              ].map((metric) => (
                <Box
                  key={metric.label}
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    py: 1.5,
                    borderBottom: "1px solid rgba(255,255,255,0.07)",
                  }}
                >
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                    <TrendingUp size={16} color={metric.color} />
                    <Typography variant="body1" color="text.secondary">
                      {metric.label}
                    </Typography>
                  </Box>
                  <Typography
                    variant="h6"
                    fontWeight={700}
                    sx={{ color: metric.color }}
                  >
                    {metric.value}
                  </Typography>
                </Box>
              ))}
            </Grid>
            <Grid item xs={12} md={7}>
              <Paper
                sx={{
                  p: 4,
                  borderRadius: 4,
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.1)",
                }}
              >
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    mb: 3,
                  }}
                >
                  <Typography variant="h6" fontWeight={700} color="white">
                    Strategy Returns (Last 12 Months)
                  </Typography>
                  <Chip
                    label="Live"
                    size="small"
                    sx={{
                      background: "#10b981",
                      color: "white",
                      fontWeight: 600,
                    }}
                    icon={<Activity size={12} />}
                  />
                </Box>
                {[
                  { name: "AI Momentum Pro", ret: 24.8, color: "#00d4ff" },
                  { name: "Quantum Alpha", ret: 38.2, color: "#10b981" },
                  { name: "Sentiment Trader", ret: 18.5, color: "#f59e0b" },
                  { name: "Mean Reversion", ret: 14.1, color: "#8b5cf6" },
                  { name: "Conservative Growth", ret: 9.3, color: "#06b6d4" },
                ].map((strat) => (
                  <Box key={strat.name} sx={{ mb: 2.5 }}>
                    <Box
                      sx={{
                        display: "flex",
                        justifyContent: "space-between",
                        mb: 0.8,
                      }}
                    >
                      <Typography variant="body2" color="text.secondary">
                        {strat.name}
                      </Typography>
                      <Typography
                        variant="body2"
                        fontWeight={700}
                        sx={{ color: strat.color }}
                      >
                        +{strat.ret}%
                      </Typography>
                    </Box>
                    <Box
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        background: "rgba(255,255,255,0.08)",
                        overflow: "hidden",
                      }}
                    >
                      <Box
                        sx={{
                          height: "100%",
                          width: `${(strat.ret / 40) * 100}%`,
                          borderRadius: 4,
                          background: `linear-gradient(90deg, ${strat.color}80, ${strat.color})`,
                          transition: "width 1s ease",
                        }}
                      />
                    </Box>
                  </Box>
                ))}
              </Paper>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* ── Testimonials ─────────────────────────────────────────────── */}
      <Box sx={{ py: 12, background: "rgba(0,0,0,0.3)" }}>
        <Container maxWidth="lg">
          <Box sx={{ textAlign: "center", mb: 8 }}>
            <Typography
              variant="h2"
              fontWeight={800}
              color="white"
              sx={{ mb: 2 }}
            >
              Trusted by Top Traders
            </Typography>
            <Typography variant="h6" color="text.secondary" fontWeight={300}>
              Join 128,000+ traders who've transformed their strategies.
            </Typography>
          </Box>
          <Grid container spacing={3}>
            {testimonials.map((t) => (
              <Grid item xs={12} md={4} key={t.name}>
                <Card
                  sx={{
                    height: "100%",
                    background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: 3,
                    transition: "all 0.3s ease",
                    "&:hover": {
                      background: "rgba(255,255,255,0.07)",
                      transform: "translateY(-4px)",
                    },
                  }}
                >
                  <CardContent sx={{ p: 4 }}>
                    <Typography
                      variant="body1"
                      color="text.secondary"
                      sx={{ mb: 3, fontStyle: "italic", lineHeight: 1.7 }}
                    >
                      &ldquo;{t.text}&rdquo;
                    </Typography>
                    <Divider
                      sx={{ mb: 3, borderColor: "rgba(255,255,255,0.08)" }}
                    />
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                      }}
                    >
                      <Box
                        sx={{ display: "flex", alignItems: "center", gap: 2 }}
                      >
                        <Box
                          sx={{
                            width: 44,
                            height: 44,
                            borderRadius: "50%",
                            background:
                              "linear-gradient(45deg, #00d4ff, #0099cc)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontWeight: 700,
                            fontSize: "0.85rem",
                            color: "white",
                          }}
                        >
                          {t.avatar}
                        </Box>
                        <Box>
                          <Typography
                            variant="subtitle2"
                            fontWeight={700}
                            color="white"
                          >
                            {t.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {t.role}
                          </Typography>
                        </Box>
                      </Box>
                      <Chip
                        label={t.return}
                        size="small"
                        sx={{
                          background: "#10b98130",
                          color: "#10b981",
                          fontWeight: 700,
                          border: "1px solid #10b98150",
                        }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* ── Pricing ──────────────────────────────────────────────────── */}
      <Box sx={{ py: 12 }}>
        <Container maxWidth="lg">
          <Box sx={{ textAlign: "center", mb: 8 }}>
            <Typography
              variant="h2"
              fontWeight={800}
              color="white"
              sx={{ mb: 2 }}
            >
              Simple, Transparent Pricing
            </Typography>
            <Typography variant="h6" color="text.secondary" fontWeight={300}>
              Start free for 14 days. No credit card required.
            </Typography>
          </Box>
          <Grid container spacing={3} justifyContent="center">
            {pricingPlans.map((plan) => (
              <Grid item xs={12} md={4} key={plan.name}>
                <Card
                  sx={{
                    height: "100%",
                    background: plan.popular
                      ? `linear-gradient(135deg, ${plan.color}20, ${plan.color}08)`
                      : "rgba(255,255,255,0.04)",
                    border: `1px solid ${plan.popular ? plan.color : "rgba(255,255,255,0.1)"}`,
                    borderRadius: 3,
                    position: "relative",
                    overflow: "visible",
                  }}
                >
                  {plan.popular && (
                    <Chip
                      label="Most Popular"
                      size="small"
                      sx={{
                        position: "absolute",
                        top: -14,
                        left: "50%",
                        transform: "translateX(-50%)",
                        background: `linear-gradient(45deg, ${plan.color}, ${plan.color}cc)`,
                        color: "white",
                        fontWeight: 700,
                        px: 1,
                      }}
                    />
                  )}
                  <CardContent sx={{ p: 4 }}>
                    <Typography
                      variant="h6"
                      fontWeight={700}
                      color="white"
                      sx={{ mb: 1 }}
                    >
                      {plan.name}
                    </Typography>
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "baseline",
                        gap: 0.5,
                        mb: 2,
                      }}
                    >
                      <Typography
                        variant="h3"
                        fontWeight={800}
                        sx={{ color: plan.color }}
                      >
                        {plan.price}
                      </Typography>
                      <Typography variant="body1" color="text.secondary">
                        {plan.period}
                      </Typography>
                    </Box>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ mb: 3, lineHeight: 1.6 }}
                    >
                      {plan.description}
                    </Typography>
                    <Divider
                      sx={{ mb: 3, borderColor: "rgba(255,255,255,0.08)" }}
                    />
                    <Box
                      sx={{
                        display: "flex",
                        flexDirection: "column",
                        gap: 1.5,
                        mb: 4,
                      }}
                    >
                      {plan.features.map((feat) => (
                        <Box
                          key={feat}
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            gap: 1.5,
                          }}
                        >
                          <ChevronRight size={16} color={plan.color} />
                          <Typography variant="body2" color="text.secondary">
                            {feat}
                          </Typography>
                        </Box>
                      ))}
                    </Box>
                    <Button
                      fullWidth
                      variant={plan.popular ? "contained" : "outlined"}
                      component={RouterLink}
                      to="/register"
                      sx={{
                        py: 1.5,
                        fontWeight: 600,
                        borderRadius: 2,
                        ...(plan.popular
                          ? {
                              background: `linear-gradient(45deg, ${plan.color}, ${plan.color}cc)`,
                              "&:hover": {
                                background: `linear-gradient(45deg, ${plan.color}cc, ${plan.color}99)`,
                              },
                            }
                          : {
                              borderColor: plan.color,
                              color: plan.color,
                              "&:hover": {
                                borderColor: plan.color,
                                background: `${plan.color}10`,
                              },
                            }),
                      }}
                    >
                      {plan.price === "Custom"
                        ? "Contact Sales"
                        : "Get Started"}
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* ── CTA Banner ───────────────────────────────────────────────── */}
      <Box sx={{ py: 12, background: "rgba(0,0,0,0.4)" }}>
        <Container maxWidth="md">
          <Paper
            sx={{
              p: { xs: 5, md: 8 },
              borderRadius: 4,
              background:
                "linear-gradient(135deg, rgba(0,212,255,0.1), rgba(0,153,204,0.05))",
              border: "1px solid rgba(0,212,255,0.25)",
              textAlign: "center",
            }}
          >
            <DollarSign
              size={52}
              color="#00d4ff"
              style={{ marginBottom: 16 }}
            />
            <Typography
              variant="h3"
              fontWeight={800}
              color="white"
              sx={{ mb: 2 }}
            >
              Ready to Trade Smarter?
            </Typography>
            <Typography
              variant="h6"
              color="text.secondary"
              sx={{ mb: 5, fontWeight: 300 }}
            >
              Join 128,000+ traders already using QuantumAlpha. Start your
              14-day free trial today.
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
                component={RouterLink}
                to="/register"
                variant="contained"
                size="large"
                endIcon={<ArrowRight size={20} />}
                sx={{
                  px: 5,
                  py: 1.8,
                  fontWeight: 700,
                  fontSize: "1.05rem",
                  background: "linear-gradient(45deg, #00d4ff, #0099cc)",
                  boxShadow: "0 4px 25px rgba(0,212,255,0.4)",
                  borderRadius: 3,
                  "&:hover": {
                    boxShadow: "0 6px 35px rgba(0,212,255,0.55)",
                    transform: "translateY(-2px)",
                  },
                }}
              >
                Create Free Account
              </Button>
              <Button
                component={RouterLink}
                to="/login"
                variant="outlined"
                size="large"
                sx={{
                  px: 5,
                  py: 1.8,
                  fontWeight: 600,
                  fontSize: "1.05rem",
                  borderColor: "rgba(255,255,255,0.3)",
                  color: "white",
                  borderRadius: 3,
                  "&:hover": {
                    borderColor: "#00d4ff",
                    background: "rgba(0,212,255,0.08)",
                  },
                }}
              >
                Sign In
              </Button>
            </Box>
          </Paper>
        </Container>
      </Box>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <Box
        component="footer"
        sx={{
          py: 5,
          borderTop: "1px solid rgba(255,255,255,0.08)",
          textAlign: "center",
        }}
      >
        <Typography variant="body2" color="text.secondary">
          © {new Date().getFullYear()} QuantumAlpha Trading Platform. All rights
          reserved. &nbsp;|&nbsp; Past performance is not indicative of future
          results. Trading involves risk.
        </Typography>
      </Box>
    </Box>
  );
};

export default Homepage;
