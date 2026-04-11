import { Box, Breadcrumbs, Link, Typography } from "@mui/material";
import { ChevronRight } from "lucide-react";
import { Link as RouterLink } from "react-router-dom";

/**
 * Page-level header with optional breadcrumb navigation
 * @param {string} title - Page title
 * @param {string} subtitle - Optional subtitle
 * @param {Array} breadcrumbs - Array of { label, path } objects
 * @param {ReactNode} actions - Optional action buttons to render on the right
 */
const Header = ({ title, subtitle, breadcrumbs = [], actions }) => {
  return (
    <Box
      sx={{
        mb: 4,
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: 2,
      }}
    >
      <Box>
        {breadcrumbs.length > 0 && (
          <Breadcrumbs separator={<ChevronRight size={14} />} sx={{ mb: 1 }}>
            {breadcrumbs.map((crumb, index) =>
              index < breadcrumbs.length - 1 ? (
                <Link
                  key={crumb.path}
                  component={RouterLink}
                  to={crumb.path}
                  underline="hover"
                  color="text.secondary"
                  variant="body2"
                >
                  {crumb.label}
                </Link>
              ) : (
                <Typography
                  key={crumb.label}
                  variant="body2"
                  color="text.primary"
                >
                  {crumb.label}
                </Typography>
              ),
            )}
          </Breadcrumbs>
        )}

        <Typography
          variant="h4"
          fontWeight={700}
          sx={{
            background: "linear-gradient(45deg, #00d4ff, #0099cc)",
            backgroundClip: "text",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}
        >
          {title}
        </Typography>

        {subtitle && (
          <Typography variant="body1" color="text.secondary" sx={{ mt: 0.5 }}>
            {subtitle}
          </Typography>
        )}
      </Box>

      {actions && (
        <Box
          sx={{
            display: "flex",
            gap: 1,
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          {actions}
        </Box>
      )}
    </Box>
  );
};

export default Header;
