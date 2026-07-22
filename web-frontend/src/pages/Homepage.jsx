import {
  Box,
  Button,
  Chip,
  Container,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import {
  ArrowRight,
  BrainCircuit,
  Gauge,
  LineChart,
  Lock,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useSelector } from "react-redux";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { Wordmark } from "../components/common/Brand";
import { gradients, palette } from "../theme/tokens";

// A calmer, higher-contrast backdrop for the homepage - a single soft glow
// instead of the animated node/graph lattice, so headline and body text stay
// easy to read at a glance.
const heroBackground = `radial-gradient(1100px 560px at 50% -12%, ${palette.cyan}14, transparent 62%), radial-gradient(900px 480px at 100% 0%, ${palette.violet}10, transparent 60%), linear-gradient(180deg, ${palette.abyss} 0%, ${palette.void} 100%)`;
const ctaBackground = `linear-gradient(135deg, ${palette.surfaceRaised} 0%, ${palette.surface} 100%)`;

const ticker = [
  { s: "AAPL", p: "175.50", c: "+1.33%", up: true },
  { s: "MSFT", p: "420.15", c: "+1.39%", up: true },
  { s: "NVDA", p: "892.45", c: "+3.02%", up: true },
  { s: "TSLA", p: "245.60", c: "-3.31%", up: false },
  { s: "GOOGL", p: "142.80", c: "-0.83%", up: false },
  { s: "AMZN", p: "185.40", c: "+1.76%", up: true },
];

const features = [
  {
    icon: BrainCircuit,
    title: "Adaptive AI strategies",
    body: "Models retrain on live order flow and regime shifts, so your edge adapts instead of decaying.",
    accent: palette.cyan,
  },
  {
    icon: ShieldCheck,
    title: "Real-time risk engine",
    body: "VaR, CVaR, and stress scenarios recompute on every fill, with guardrails that act before you breach a limit.",
    accent: palette.violet,
  },
  {
    icon: Gauge,
    title: "Microsecond execution",
    body: "Smart order routing splits across venues to minimise slippage and capture the best available price.",
    accent: palette.mint,
  },
  {
    icon: LineChart,
    title: "Quant-grade analytics",
    body: "Attribution, factor exposure, and drawdown analysis presented the way a desk actually reads them.",
    accent: palette.amber,
  },
];

const stats = [
  { v: "$4.8B+", l: "Notional routed" },
  { v: "128K", l: "Active accounts" },
  { v: "99.99%", l: "Uptime" },
  { v: "11ms", l: "Median fill" },
];

const steps = [
  {
    n: "01",
    t: "Create your account",
    d: "Open a workspace in under two minutes. No desk required.",
  },
  {
    n: "02",
    t: "Connect & configure",
    d: "Pick strategies, set risk limits, and choose your universe.",
  },
  {
    n: "03",
    t: "Trade with an edge",
    d: "Let the engine execute while you monitor from one terminal.",
  },
];

const Homepage = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useSelector((state) => state.auth);

  const primaryCta = () =>
    navigate(isAuthenticated ? "/dashboard" : "/register");

  return (
    <Box sx={{ minHeight: "100vh", background: heroBackground }}>
      {/* ── Top nav ─────────────────────────────────────────────── */}
      <Box
        sx={{
          position: "sticky",
          top: 0,
          zIndex: 10,
          backdropFilter: "blur(12px)",
          background: "rgba(6,10,20,0.6)",
          borderBottom: `1px solid ${palette.border}`,
        }}
      >
        <Container maxWidth="lg">
          <Stack
            direction="row"
            alignItems="center"
            justifyContent="space-between"
            sx={{ py: 1.8 }}
          >
            <Wordmark size={32} />
            <Stack direction="row" spacing={1.5} alignItems="center">
              {isAuthenticated ? (
                <Button
                  variant="contained"
                  endIcon={<ArrowRight size={16} />}
                  onClick={() => navigate("/dashboard")}
                >
                  Go to dashboard
                </Button>
              ) : (
                <>
                  <Button
                    component={RouterLink}
                    to="/login"
                    sx={{ color: "text.secondary" }}
                  >
                    Sign in
                  </Button>
                  <Button
                    variant="contained"
                    component={RouterLink}
                    to="/register"
                  >
                    Get started
                  </Button>
                </>
              )}
            </Stack>
          </Stack>
        </Container>
      </Box>

      {/* ── Hero ────────────────────────────────────────────────── */}
      <Box sx={{ position: "relative", overflow: "hidden" }}>
        <Container
          maxWidth="lg"
          sx={{
            position: "relative",
            pt: { xs: 8, md: 14 },
            pb: { xs: 8, md: 12 },
          }}
        >
          <Box sx={{ maxWidth: 820, mx: "auto", textAlign: "center" }}>
            <Chip
              icon={<Sparkles size={15} />}
              label="Quantum-enhanced execution, now in public beta"
              sx={{
                mb: 3,
                px: 0.5,
                color: "text.primary",
                border: `1px solid ${palette.border}`,
                background: "rgba(34,211,238,0.06)",
                "& .MuiChip-icon": { color: palette.cyan },
              }}
            />
            <Typography
              variant="h1"
              sx={{ fontSize: { xs: "2.6rem", md: "4rem" }, mb: 2.5 }}
            >
              Trade with a{" "}
              <Box
                component="span"
                sx={{
                  background: gradients.brand,
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                quantum edge
              </Box>
            </Typography>
            <Typography
              variant="h6"
              sx={{
                color: "text.secondary",
                fontWeight: 400,
                maxWidth: 640,
                mx: "auto",
                mb: 4,
              }}
            >
              QuantumAlpha pairs adaptive AI strategies with a real-time risk
              engine and institutional execution - in a single terminal built
              for people who take markets seriously.
            </Typography>
            <Stack
              direction={{ xs: "column", sm: "row" }}
              spacing={2}
              justifyContent="center"
              sx={{ mb: 2 }}
            >
              <Button
                size="large"
                variant="contained"
                endIcon={<ArrowRight size={18} />}
                onClick={primaryCta}
                sx={{ px: 4, py: 1.4 }}
              >
                {isAuthenticated ? "Open dashboard" : "Start free"}
              </Button>
              <Button
                size="large"
                variant="outlined"
                component={RouterLink}
                to="/login"
                sx={{ px: 4, py: 1.4 }}
              >
                Sign in
              </Button>
            </Stack>
            <Stack
              direction="row"
              spacing={1}
              justifyContent="center"
              alignItems="center"
              sx={{ color: "text.secondary" }}
            >
              <Lock size={14} />
              <Typography variant="caption">
                Bank-grade encryption · No card required
              </Typography>
            </Stack>
          </Box>

          {/* Live ticker strip */}
          <Box
            sx={{
              mt: { xs: 6, md: 9 },
              border: `1px solid ${palette.border}`,
              borderRadius: 3,
              overflow: "hidden",
              background: palette.surfaceGlass,
              backdropFilter: "blur(8px)",
            }}
          >
            <Stack
              direction="row"
              divider={
                <Box sx={{ width: "1px", background: palette.border }} />
              }
              sx={{ overflowX: "auto" }}
            >
              {ticker.map((t) => (
                <Stack
                  key={t.s}
                  sx={{ px: 3, py: 2, minWidth: 150, flex: "1 0 auto" }}
                >
                  <Typography
                    variant="caption"
                    sx={{ color: "text.secondary" }}
                  >
                    {t.s}
                  </Typography>
                  <Typography
                    sx={{ fontFamily: "var(--qa-mono)", fontWeight: 700 }}
                    style={{ fontFamily: '"JetBrains Mono", monospace' }}
                  >
                    ${t.p}
                  </Typography>
                  <Typography
                    variant="caption"
                    sx={{
                      fontFamily: '"JetBrains Mono", monospace',
                      color: t.up ? palette.mint : palette.rose,
                      fontWeight: 700,
                    }}
                  >
                    {t.c}
                  </Typography>
                </Stack>
              ))}
            </Stack>
          </Box>
        </Container>
      </Box>

      {/* ── Features ────────────────────────────────────────────── */}
      <Container maxWidth="lg" sx={{ py: { xs: 8, md: 12 } }}>
        <Typography variant="overline">The platform</Typography>
        <Typography variant="h3" sx={{ mb: 1, mt: 0.5 }}>
          Everything a desk needs, nothing it doesn&apos;t
        </Typography>
        <Typography
          variant="body1"
          sx={{ color: "text.secondary", maxWidth: 560, mb: 5 }}
        >
          Four systems working as one - research, risk, routing, and reporting -
          so you can stay in flow instead of stitching tools together.
        </Typography>
        <Grid container spacing={3}>
          {features.map((f) => (
            <Grid item xs={12} sm={6} md={3} key={f.title}>
              <Box
                sx={{
                  height: "100%",
                  p: 3,
                  borderRadius: 3,
                  border: `1px solid ${palette.border}`,
                  background: palette.surface,
                  position: "relative",
                  overflow: "hidden",
                  transition: "transform .2s ease, border-color .2s ease",
                  "&:hover": {
                    transform: "translateY(-4px)",
                    borderColor: `${f.accent}66`,
                  },
                  "&::before": {
                    content: '""',
                    position: "absolute",
                    insetInline: 0,
                    top: 0,
                    height: "2px",
                    background: `linear-gradient(90deg, transparent, ${f.accent}, transparent)`,
                  },
                }}
              >
                <Box
                  sx={{
                    width: 44,
                    height: 44,
                    borderRadius: 2,
                    display: "grid",
                    placeItems: "center",
                    mb: 2,
                    color: f.accent,
                    background: `${f.accent}14`,
                  }}
                >
                  <f.icon size={22} />
                </Box>
                <Typography variant="h6" sx={{ mb: 1 }}>
                  {f.title}
                </Typography>
                <Typography variant="body2">{f.body}</Typography>
              </Box>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* ── Stats band ──────────────────────────────────────────── */}
      <Box
        sx={{
          borderBlock: `1px solid ${palette.border}`,
          background: "rgba(15,22,38,0.5)",
        }}
      >
        <Container maxWidth="lg" sx={{ py: 6 }}>
          <Grid container spacing={3}>
            {stats.map((s) => (
              <Grid item xs={6} md={3} key={s.l} sx={{ textAlign: "center" }}>
                <Typography
                  sx={{
                    fontFamily: '"JetBrains Mono", monospace',
                    fontWeight: 700,
                    fontSize: { xs: "1.8rem", md: "2.4rem" },
                    background: gradients.brand,
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                  }}
                >
                  {s.v}
                </Typography>
                <Typography variant="caption" sx={{ color: "text.secondary" }}>
                  {s.l}
                </Typography>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* ── How it works ────────────────────────────────────────── */}
      <Container maxWidth="lg" sx={{ py: { xs: 8, md: 12 } }}>
        <Typography variant="overline">Get started</Typography>
        <Typography variant="h3" sx={{ mb: 5, mt: 0.5 }}>
          Live in three steps
        </Typography>
        <Grid container spacing={3}>
          {steps.map((s) => (
            <Grid item xs={12} md={4} key={s.n}>
              <Box
                sx={{
                  p: 3,
                  borderRadius: 3,
                  border: `1px solid ${palette.border}`,
                  background: palette.surface,
                  height: "100%",
                }}
              >
                <Typography
                  sx={{
                    fontFamily: '"JetBrains Mono", monospace',
                    fontSize: "2rem",
                    fontWeight: 700,
                    color: palette.cyan,
                    opacity: 0.85,
                    mb: 1,
                  }}
                >
                  {s.n}
                </Typography>
                <Typography variant="h6" sx={{ mb: 0.5 }}>
                  {s.t}
                </Typography>
                <Typography variant="body2">{s.d}</Typography>
              </Box>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* ── CTA ─────────────────────────────────────────────────── */}
      <Container maxWidth="lg" sx={{ pb: { xs: 8, md: 14 } }}>
        <Box
          sx={{
            position: "relative",
            overflow: "hidden",
            borderRadius: 5,
            p: { xs: 4, md: 8 },
            textAlign: "center",
            border: `1px solid ${palette.border}`,
            background: ctaBackground,
          }}
        >
          <Box sx={{ position: "relative" }}>
            <Typography variant="h3" sx={{ mb: 1.5 }}>
              Ready to find your alpha?
            </Typography>
            <Typography
              variant="body1"
              sx={{
                color: "text.secondary",
                maxWidth: 520,
                mx: "auto",
                mb: 3.5,
              }}
            >
              Join thousands of traders running smarter strategies on
              QuantumAlpha. Set up your terminal in minutes.
            </Typography>
            <Button
              size="large"
              variant="contained"
              endIcon={<ArrowRight size={18} />}
              onClick={primaryCta}
              sx={{ px: 4, py: 1.4 }}
            >
              {isAuthenticated ? "Open dashboard" : "Create free account"}
            </Button>
          </Box>
        </Box>
      </Container>

      {/* ── Footer ──────────────────────────────────────────────── */}
      <Box sx={{ borderTop: `1px solid ${palette.border}` }}>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Stack
            direction={{ xs: "column", sm: "row" }}
            alignItems="center"
            justifyContent="space-between"
            spacing={2}
          >
            <Wordmark size={26} />
            <Typography variant="caption" sx={{ color: "text.secondary" }}>
              © {new Date().getFullYear()} QuantumAlpha. For demonstration
              purposes only - not investment advice.
            </Typography>
          </Stack>
        </Container>
      </Box>
    </Box>
  );
};

export default Homepage;
