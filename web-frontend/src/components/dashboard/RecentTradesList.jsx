import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  useTheme,
} from "@mui/material";

const RecentTradesList = ({ trades }) => {
  const _theme = useTheme();

  return (
    <Box sx={{ overflowY: "auto", maxHeight: 300 }}>
      {trades.map((trade) => (
        <Card
          key={trade.id}
          sx={{
            mb: 2,
            backgroundColor: "background.paper",
            transition: "transform 0.2s ease, box-shadow 0.2s ease",
            "&:hover": {
              transform: "translateY(-2px)",
              boxShadow: "0 6px 12px rgba(0,0,0,0.2)",
            },
          }}
        >
          <CardContent sx={{ py: 1.5 }}>
            <Grid container alignItems="center">
              <Grid item xs={8}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {trade.symbol}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {trade.timestamp}
                </Typography>
              </Grid>
              <Grid item xs={4} sx={{ textAlign: "right" }}>
                <Typography
                  variant="body1"
                  color={trade.type === "BUY" ? "primary" : "error"}
                  fontWeight="bold"
                >
                  {trade.type}
                </Typography>
                <Typography variant="body2">
                  {trade.quantity} @ ${trade.price}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      ))}
    </Box>
  );
};

export default RecentTradesList;
