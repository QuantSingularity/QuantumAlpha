import { Box, Button, Container, Paper, Typography } from "@mui/material";
import { ArrowLeft, Home, Search } from "lucide-react";
import { useNavigate } from "react-router-dom";

const NotFound = () => {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: (theme) =>
          `linear-gradient(135deg, ${theme.palette.primary.dark} 0%, ${theme.palette.secondary.dark} 100%)`,
      }}
    >
      <Container maxWidth="md">
        <Paper
          elevation={24}
          sx={{
            p: 6,
            borderRadius: 3,
            textAlign: "center",
            backdropFilter: "blur(10px)",
          }}
        >
          {/* 404 Number */}
          <Typography
            variant="h1"
            sx={{
              fontSize: { xs: "6rem", md: "10rem" },
              fontWeight: "bold",
              background: "linear-gradient(45deg, #00f2fe 30%, #4facfe 90%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              mb: 2,
            }}
          >
            404
          </Typography>

          {/* Icon */}
          <Box sx={{ mb: 3 }}>
            <Search
              size={80}
              style={{
                color: "#00f2fe",
                opacity: 0.7,
              }}
            />
          </Box>

          {/* Title */}
          <Typography
            variant="h4"
            gutterBottom
            fontWeight="bold"
            sx={{ mb: 2 }}
          >
            Page Not Found
          </Typography>

          {/* Description */}
          <Typography
            variant="body1"
            color="text.secondary"
            sx={{ mb: 4, maxWidth: 500, mx: "auto" }}
          >
            The page you are looking for doesn't exist or has been moved. Please
            check the URL or return to the homepage.
          </Typography>

          {/* Action Buttons */}
          <Box
            sx={{
              display: "flex",
              gap: 2,
              justifyContent: "center",
              flexWrap: "wrap",
            }}
          >
            <Button
              variant="contained"
              size="large"
              startIcon={<Home size={20} />}
              onClick={() => navigate("/")}
              sx={{
                px: 4,
                py: 1.5,
                background: "linear-gradient(45deg, #00f2fe 30%, #4facfe 90%)",
                fontWeight: 600,
              }}
            >
              Go Home
            </Button>
            <Button
              variant="outlined"
              size="large"
              startIcon={<ArrowLeft size={20} />}
              onClick={() => navigate(-1)}
              sx={{
                px: 4,
                py: 1.5,
              }}
            >
              Go Back
            </Button>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
};

export default NotFound;
