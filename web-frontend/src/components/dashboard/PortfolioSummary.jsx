import { Alert, Box, Skeleton, Typography } from "@mui/material";

const PortfolioSummary = ({
  portfolioValue,
  dailyChange,
  percentChange,
  isLoading = false,
  error = null,
}) => {
  if (isLoading) {
    return (
      <>
        <Skeleton variant="text" width="60%" height={40} />
        <Skeleton variant="text" width="40%" height={60} />
        <Skeleton variant="text" width="30%" height={30} />
      </>
    );
  }

  if (error) {
    return <Alert severity="error">Error loading portfolio data</Alert>;
  }

  return (
    <>
      <Typography variant="h4" gutterBottom>
        Portfolio Value
      </Typography>
      <Typography variant="h3" color="primary" sx={{ fontWeight: 600 }}>
        ${portfolioValue.toLocaleString()}
      </Typography>
      <Box sx={{ display: "flex", alignItems: "center", mt: 1 }}>
        <Typography
          variant="h6"
          color={dailyChange >= 0 ? "primary" : "error"}
          sx={{ fontWeight: 500 }}
        >
          {dailyChange >= 0 ? "+" : ""}
          {dailyChange.toLocaleString()} ({percentChange}%)
        </Typography>
        <Typography variant="body2" sx={{ ml: 1, opacity: 0.8 }}>
          Today
        </Typography>
      </Box>
    </>
  );
};

export default PortfolioSummary;
