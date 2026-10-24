import { Box, Button, Stack, Typography } from "@mui/material";
import { AlertTriangle, RefreshCw } from "lucide-react";
import React from "react";

/**
 * Catches render errors so a single broken component degrades to a recoverable
 * panel instead of a blank white screen. Used both globally (around the whole
 * app) and locally around data-heavy views.
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <Box
        sx={{
          minHeight: "60vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          p: 3,
        }}
      >
        <Box
          sx={{
            maxWidth: 480,
            width: "100%",
            textAlign: "center",
            p: 4,
            borderRadius: 4,
            border: "1px solid rgba(251,113,133,0.3)",
            background:
              "linear-gradient(180deg, rgba(251,113,133,0.06), transparent)",
          }}
        >
          <Box
            sx={{
              width: 56,
              height: 56,
              mx: "auto",
              mb: 2,
              borderRadius: "50%",
              display: "grid",
              placeItems: "center",
              background: "rgba(251,113,133,0.12)",
              color: "#FB7185",
            }}
          >
            <AlertTriangle size={26} />
          </Box>
          <Typography variant="h5" sx={{ mb: 1 }}>
            Something went wrong
          </Typography>
          <Typography variant="body2" sx={{ mb: 3 }}>
            Something stopped this section from rendering. You can retry, or
            reload the app to get back on track.
          </Typography>
          <Stack direction="row" spacing={1.5} justifyContent="center">
            <Button
              variant="contained"
              startIcon={<RefreshCw size={16} />}
              onClick={this.handleReset}
            >
              Try again
            </Button>
            <Button
              variant="outlined"
              onClick={() => window.location.assign("/")}
            >
              Go home
            </Button>
          </Stack>
          {process.env.NODE_ENV === "development" && this.state.error && (
            <Box
              component="pre"
              sx={{
                mt: 3,
                p: 2,
                textAlign: "left",
                fontSize: "0.72rem",
                color: "text.secondary",
                whiteSpace: "pre-wrap",
                overflow: "auto",
                maxHeight: 200,
                borderRadius: 2,
                background: "rgba(0,0,0,0.3)",
              }}
            >
              {String(this.state.error)}
              {this.state.errorInfo?.componentStack}
            </Box>
          )}
        </Box>
      </Box>
    );
  }
}

export default ErrorBoundary;
