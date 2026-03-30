import { Alert, AlertTitle } from "@mui/material";
import React from "react";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error to an error reporting service
    console.error("Error caught by ErrorBoundary:", error, errorInfo);
    this.setState({ errorInfo });
  }

  render() {
    if (this.state.hasError) {
      // Render fallback UI
      return (
        <Alert
          severity="error"
          variant="filled"
          sx={{
            my: 2,
            boxShadow: 3,
            "& .MuiAlert-message": {
              width: "100%",
            },
          }}
        >
          <AlertTitle>Something went wrong</AlertTitle>
          <p>We're sorry, but there was an error loading this component.</p>
          <p>
            Please try refreshing the page or contact support if the issue
            persists.
          </p>
          {process.env.NODE_ENV === "development" && (
            <details style={{ whiteSpace: "pre-wrap", marginTop: "10px" }}>
              {this.state.error?.toString()}
              <br />
              {this.state.errorInfo?.componentStack}
            </details>
          )}
        </Alert>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
