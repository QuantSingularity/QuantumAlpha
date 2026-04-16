import {
  Alert,
  Box,
  CircularProgress,
  Container,
  Typography,
} from "@mui/material";
import { useEffect, useRef, useState } from "react";
import { useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import { handleOAuthCallback } from "../auth/oauth";
import { loginSuccess } from "../store/slices/authSlice";

/**
 * OAuthCallback — handles the redirect from the OAuth authorization server.
 * Reads `code` and `state` from the URL search params, exchanges them for
 * tokens via PKCE, then stores the result and redirects to the dashboard.
 */
const OAuthCallback = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [error, setError] = useState(null);
  // Guard against React StrictMode double-invoking the effect
  const processed = useRef(false);

  useEffect(() => {
    if (processed.current) return;
    processed.current = true;

    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const state = params.get("state");
    const errorParam = params.get("error");

    if (errorParam) {
      setError(
        `Authorization denied: ${params.get("error_description") || errorParam}`,
      );
      return;
    }

    if (!code || !state) {
      setError("Missing authorization code or state parameter.");
      return;
    }

    handleOAuthCallback(code, state)
      .then(({ accessToken }) => {
        dispatch(
          loginSuccess({
            user: { email: "oauth-user@example.com", firstName: "User" },
            token: accessToken,
          }),
        );
        navigate("/dashboard", { replace: true });
      })
      .catch((err) => {
        console.error("OAuth callback error:", err);
        setError(err.message || "Authentication failed. Please try again.");
      });
  }, [dispatch, navigate]);

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background:
          "linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Container maxWidth="sm" sx={{ textAlign: "center" }}>
        {error ? (
          <>
            <Alert
              severity="error"
              variant="filled"
              sx={{ mb: 3, borderRadius: 2 }}
            >
              {error}
            </Alert>
            <Typography
              variant="body1"
              color="text.secondary"
              onClick={() => navigate("/login")}
              sx={{
                cursor: "pointer",
                textDecoration: "underline",
                color: "#00d4ff",
              }}
            >
              Return to Login
            </Typography>
          </>
        ) : (
          <>
            <CircularProgress size={52} sx={{ color: "#00d4ff", mb: 3 }} />
            <Typography
              variant="h5"
              fontWeight={700}
              color="white"
              sx={{ mb: 1 }}
            >
              Completing Sign In…
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Please wait while we verify your credentials.
            </Typography>
          </>
        )}
      </Container>
    </Box>
  );
};

export default OAuthCallback;
