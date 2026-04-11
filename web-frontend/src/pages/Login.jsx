import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Fade,
  IconButton,
  InputAdornment,
  Paper,
  TextField,
  Typography,
} from "@mui/material";
import {
  ArrowRight,
  Eye,
  EyeOff,
  Lock,
  Mail,
  Shield,
  TrendingUp,
  Zap,
} from "lucide-react";
import { useState } from "react";
import { useDispatch } from "react-redux";
import { Link as RouterLink, useLocation, useNavigate } from "react-router-dom";
import { loginSuccess } from "../store/slices/authSlice";
import { isValidEmail } from "../utils/validation";

const Login = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const location = useLocation();
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState("");
  const [successMessage] = useState(location.state?.message || "");
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [errors, setErrors] = useState({});

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setErrors((prev) => ({ ...prev, [e.target.name]: "" }));
    setApiError("");
  };

  const validateForm = () => {
    const newErrors = {};
    if (!formData.email.trim()) {
      newErrors.email = "Email is required";
    } else if (!isValidEmail(formData.email)) {
      newErrors.email = "Please enter a valid email address";
    }
    if (!formData.password) {
      newErrors.password = "Password is required";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    setApiError("");
    try {
      // Simulate API call — replace with real API mutation
      await new Promise((res) => setTimeout(res, 800));
      dispatch(
        loginSuccess({
          user: { email: formData.email, firstName: "User" },
          token: "mock-token-" + Date.now(),
        }),
      );
      navigate("/");
    } catch {
      setApiError("Invalid email or password. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const FeatureCard = ({ icon: Icon, title, description, delay }) => (
    <Fade in={true} timeout={1000} style={{ transitionDelay: `${delay}ms` }}>
      <Card
        sx={{
          background: "rgba(255, 255, 255, 0.05)",
          backdropFilter: "blur(10px)",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          borderRadius: 3,
          transition: "all 0.3s ease",
          "&:hover": {
            transform: "translateY(-4px)",
            boxShadow: "0 8px 25px rgba(0, 212, 255, 0.2)",
          },
        }}
      >
        <CardContent sx={{ p: 3, textAlign: "center" }}>
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              mb: 2,
              "& svg": {
                color: "#00d4ff",
              },
            }}
          >
            <Icon size={32} />
          </Box>
          <Typography
            variant="h6"
            fontWeight={600}
            color="white"
            sx={{ mb: 1 }}
          >
            {title}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {description}
          </Typography>
        </CardContent>
      </Card>
    </Fade>
  );

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background:
          "linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%)",
        display: "flex",
        alignItems: "center",
        py: 4,
      }}
    >
      <Container maxWidth="lg">
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" },
            gap: 6,
            alignItems: "center",
          }}
        >
          {/* Left Side - Branding & Features */}
          <Box>
            <Fade in={true} timeout={800}>
              <Box sx={{ mb: 6 }}>
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
                    fontSize: { xs: "2.5rem", md: "3rem" },
                  }}
                >
                  QuantumAlpha
                </Typography>
                <Typography
                  variant="h5"
                  color="text.secondary"
                  sx={{ mb: 4, fontWeight: 300 }}
                >
                  Next-generation AI trading platform powered by quantum
                  algorithms
                </Typography>
                <Typography
                  variant="body1"
                  color="text.secondary"
                  sx={{ lineHeight: 1.7 }}
                >
                  Experience the future of algorithmic trading with our advanced
                  AI models, real-time market analysis, and quantum-enhanced
                  risk management.
                </Typography>
              </Box>
            </Fade>

            {/* Feature Cards */}
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: { xs: "1fr", sm: "repeat(3, 1fr)" },
                gap: 2,
                mb: 4,
              }}
            >
              <FeatureCard
                icon={Zap}
                title="Lightning Fast"
                description="Execute trades in microseconds"
                delay={200}
              />
              <FeatureCard
                icon={TrendingUp}
                title="AI Powered"
                description="Advanced machine learning models"
                delay={400}
              />
              <FeatureCard
                icon={Shield}
                title="Secure"
                description="Bank-grade security protocols"
                delay={600}
              />
            </Box>
          </Box>

          {/* Right Side - Login Form */}
          <Fade in={true} timeout={1000}>
            <Paper
              elevation={0}
              sx={{
                p: 6,
                borderRadius: 4,
                background: "rgba(255, 255, 255, 0.05)",
                backdropFilter: "blur(20px)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",
              }}
            >
              <Box sx={{ textAlign: "center", mb: 4 }}>
                <Typography
                  variant="h4"
                  fontWeight={700}
                  color="white"
                  sx={{ mb: 1 }}
                >
                  Welcome Back
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Sign in to access your trading dashboard
                </Typography>
              </Box>

              {successMessage && (
                <Alert severity="success" sx={{ mb: 3, borderRadius: 2 }}>
                  {successMessage}
                </Alert>
              )}

              {apiError && (
                <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
                  {apiError}
                </Alert>
              )}

              <form onSubmit={handleSubmit} noValidate>
                <Box sx={{ mb: 3 }}>
                  <TextField
                    fullWidth
                    name="email"
                    type="email"
                    placeholder="Enter your email"
                    value={formData.email}
                    onChange={handleInputChange}
                    error={!!errors.email}
                    helperText={errors.email}
                    disabled={loading}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Mail size={20} color="#00d4ff" />
                        </InputAdornment>
                      ),
                    }}
                    sx={{
                      "& .MuiOutlinedInput-root": {
                        background: "rgba(255, 255, 255, 0.05)",
                        borderRadius: 2,
                        "& fieldset": {
                          borderColor: errors.email
                            ? "#ef4444"
                            : "rgba(255, 255, 255, 0.2)",
                        },
                        "&:hover fieldset": { borderColor: "#00d4ff" },
                        "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                      },
                      "& .MuiOutlinedInput-input": {
                        color: "white",
                        "&::placeholder": {
                          color: "rgba(255, 255, 255, 0.5)",
                        },
                      },
                    }}
                  />
                </Box>

                <Box sx={{ mb: 4 }}>
                  <TextField
                    fullWidth
                    name="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your password"
                    value={formData.password}
                    onChange={handleInputChange}
                    error={!!errors.password}
                    helperText={errors.password}
                    disabled={loading}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Lock size={20} color="#00d4ff" />
                        </InputAdornment>
                      ),
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            onClick={() => setShowPassword(!showPassword)}
                            edge="end"
                            sx={{ color: "rgba(255, 255, 255, 0.5)" }}
                          >
                            {showPassword ? (
                              <EyeOff size={20} />
                            ) : (
                              <Eye size={20} />
                            )}
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                    sx={{
                      "& .MuiOutlinedInput-root": {
                        background: "rgba(255, 255, 255, 0.05)",
                        borderRadius: 2,
                        "& fieldset": {
                          borderColor: errors.password
                            ? "#ef4444"
                            : "rgba(255, 255, 255, 0.2)",
                        },
                        "&:hover fieldset": { borderColor: "#00d4ff" },
                        "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                      },
                      "& .MuiOutlinedInput-input": {
                        color: "white",
                        "&::placeholder": {
                          color: "rgba(255, 255, 255, 0.5)",
                        },
                      },
                    }}
                  />
                </Box>

                <Button
                  type="submit"
                  fullWidth
                  size="large"
                  disabled={loading}
                  endIcon={
                    loading ? (
                      <CircularProgress size={20} color="inherit" />
                    ) : (
                      <ArrowRight size={20} />
                    )
                  }
                  sx={{
                    py: 1.5,
                    mb: 3,
                    fontWeight: 600,
                    fontSize: "1.1rem",
                    background: "linear-gradient(45deg, #00d4ff, #0099cc)",
                    borderRadius: 2,
                    boxShadow: "0 4px 20px rgba(0, 212, 255, 0.3)",
                    color: "white",
                    "&:hover": {
                      background: "linear-gradient(45deg, #0099cc, #0066aa)",
                      boxShadow: "0 6px 25px rgba(0, 212, 255, 0.4)",
                      transform: loading ? "none" : "translateY(-2px)",
                    },
                    "&.Mui-disabled": {
                      opacity: 0.7,
                      color: "white",
                    },
                  }}
                >
                  {loading ? "Signing In..." : "Sign In"}
                </Button>

                <Box sx={{ textAlign: "center" }}>
                  <Typography variant="body2" color="text.secondary">
                    Don&apos;t have an account?{" "}
                    <RouterLink
                      to="/register"
                      style={{
                        color: "#00d4ff",
                        textDecoration: "none",
                        fontWeight: 600,
                      }}
                    >
                      Sign up here
                    </RouterLink>
                  </Typography>
                </Box>
              </form>
            </Paper>
          </Fade>
        </Box>
      </Container>
    </Box>
  );
};

export default Login;
