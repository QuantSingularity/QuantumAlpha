import {
  Alert,
  Box,
  Button,
  ButtonGroup,
  Card,
  CardContent,
  Fade,
  FormControlLabel,
  Grid,
  Paper,
  Snackbar,
  Switch,
  Typography,
} from "@mui/material";
import {
  Check,
  Contrast,
  Minimize2,
  Monitor,
  Moon,
  Palette,
  RotateCcw,
  Sparkles,
  Sun,
  Type,
} from "lucide-react";
import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  resetTheme,
  setAccentColor,
  setFontSize,
  setPrimaryColor,
  setTheme,
  toggleAnimations,
  toggleCompactMode,
  toggleDarkMode,
  toggleHighContrast,
} from "../store/slices/themeSlice";

const ThemeCustomizer = () => {
  const dispatch = useDispatch();
  const theme = useSelector((state) => state.theme);
  const [_anchorEl, _setAnchorEl] = useState(null);
  const [_colorPickerOpen, _setColorPickerOpen] = useState(false);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success",
  });

  const themeOptions = [
    {
      value: "light",
      label: "Light",
      icon: Sun,
      description: "Clean and bright interface",
    },
    {
      value: "dark",
      label: "Dark",
      icon: Moon,
      description: "Easy on the eyes",
    },
    {
      value: "auto",
      label: "Auto",
      icon: Monitor,
      description: "Follows system preference",
    },
  ];

  const colorPresets = [
    { name: "Quantum Blue", primary: "#00d4ff", accent: "#0099cc" },
    { name: "Emerald Green", primary: "#10b981", accent: "#059669" },
    { name: "Purple Haze", primary: "#8b5cf6", accent: "#7c3aed" },
    { name: "Sunset Orange", primary: "#f59e0b", accent: "#d97706" },
    { name: "Rose Pink", primary: "#f43f5e", accent: "#e11d48" },
    { name: "Indigo Night", primary: "#6366f1", accent: "#4f46e5" },
  ];

  const fontSizes = [
    { value: "small", label: "Small", size: "14px" },
    { value: "medium", label: "Medium", size: "16px" },
    { value: "large", label: "Large", size: "18px" },
  ];

  const handleThemeChange = (newTheme) => {
    dispatch(setTheme(newTheme));
    setSnackbar({
      open: true,
      message: `Theme changed to ${newTheme}`,
      severity: "success",
    });
  };

  const handleColorPreset = (preset) => {
    dispatch(setPrimaryColor(preset.primary));
    dispatch(setAccentColor(preset.accent));
    setSnackbar({
      open: true,
      message: `Applied ${preset.name} color scheme`,
      severity: "success",
    });
  };

  const handleReset = () => {
    dispatch(resetTheme());
    setSnackbar({
      open: true,
      message: "Theme settings reset to default",
      severity: "info",
    });
  };

  const ThemePreview = ({ themeType }) => {
    const isDark = themeType === "dark";
    const bgColor = isDark ? "#0f0f23" : "#ffffff";
    const cardColor = isDark
      ? "rgba(255, 255, 255, 0.05)"
      : "rgba(0, 0, 0, 0.05)";
    const textColor = isDark ? "#ffffff" : "#000000";

    return (
      <Box
        sx={{
          width: "100%",
          height: 120,
          borderRadius: 2,
          background: bgColor,
          border: `2px solid ${theme.theme === themeType ? theme.primaryColor : "transparent"}`,
          p: 2,
          cursor: "pointer",
          transition: "all 0.3s ease",
          "&:hover": {
            transform: "scale(1.02)",
            boxShadow: `0 4px 20px ${theme.primaryColor}30`,
          },
        }}
        onClick={() => handleThemeChange(themeType)}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
          <Box
            sx={{
              width: 12,
              height: 12,
              borderRadius: "50%",
              background: theme.primaryColor,
            }}
          />
          <Box
            sx={{
              width: 20,
              height: 4,
              borderRadius: 2,
              background: cardColor,
            }}
          />
        </Box>
        <Box
          sx={{
            width: "100%",
            height: 40,
            borderRadius: 1,
            background: cardColor,
            mb: 1,
            display: "flex",
            alignItems: "center",
            px: 1,
          }}
        >
          <Box
            sx={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: textColor,
              opacity: 0.7,
              mr: 1,
            }}
          />
          <Box
            sx={{
              width: "60%",
              height: 2,
              borderRadius: 1,
              background: textColor,
              opacity: 0.5,
            }}
          />
        </Box>
        <Box sx={{ display: "flex", gap: 1 }}>
          <Box
            sx={{
              width: "30%",
              height: 20,
              borderRadius: 1,
              background: cardColor,
            }}
          />
          <Box
            sx={{
              width: "50%",
              height: 20,
              borderRadius: 1,
              background: cardColor,
            }}
          />
        </Box>
      </Box>
    );
  };

  const ColorSwatch = ({ preset, isSelected }) => (
    <Box
      sx={{
        width: 60,
        height: 60,
        borderRadius: 2,
        background: `linear-gradient(135deg, ${preset.primary}, ${preset.accent})`,
        border: `3px solid ${isSelected ? "#ffffff" : "transparent"}`,
        cursor: "pointer",
        transition: "all 0.3s ease",
        position: "relative",
        "&:hover": {
          transform: "scale(1.1)",
          boxShadow: `0 4px 20px ${preset.primary}50`,
        },
      }}
      onClick={() => handleColorPreset(preset)}
    >
      {isSelected && (
        <Box
          sx={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            color: "white",
          }}
        >
          <Check size={20} />
        </Box>
      )}
    </Box>
  );

  return (
    <Fade in={true} timeout={1000}>
      <Paper
        elevation={0}
        sx={{
          p: 4,
          borderRadius: 4,
          background: "rgba(255, 255, 255, 0.05)",
          backdropFilter: "blur(20px)",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",
        }}
      >
        {/* Header */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            mb: 4,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <Palette size={32} color={theme.primaryColor} />
            <Box>
              <Typography variant="h5" fontWeight={700} color="white">
                Theme Customizer
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Personalize your trading experience
              </Typography>
            </Box>
          </Box>
          <Button
            variant="outlined"
            startIcon={<RotateCcw size={20} />}
            onClick={handleReset}
            sx={{
              borderColor: theme.primaryColor,
              color: theme.primaryColor,
              "&:hover": {
                borderColor: theme.primaryColor,
                background: `${theme.primaryColor}20`,
              },
            }}
          >
            Reset
          </Button>
        </Box>

        <Grid container spacing={4}>
          {/* Theme Selection */}
          <Grid item xs={12} md={6}>
            <Typography
              variant="h6"
              fontWeight={600}
              color="white"
              sx={{ mb: 3 }}
            >
              Theme Mode
            </Typography>
            <Grid container spacing={2}>
              {themeOptions.map((option) => {
                const Icon = option.icon;
                return (
                  <Grid item xs={4} key={option.value}>
                    <Card
                      sx={{
                        background:
                          theme.theme === option.value
                            ? `${theme.primaryColor}20`
                            : "rgba(255, 255, 255, 0.05)",
                        border: `1px solid ${
                          theme.theme === option.value
                            ? theme.primaryColor
                            : "rgba(255, 255, 255, 0.1)"
                        }`,
                        cursor: "pointer",
                        transition: "all 0.3s ease",
                        "&:hover": {
                          transform: "translateY(-2px)",
                          boxShadow: `0 4px 20px ${theme.primaryColor}30`,
                        },
                      }}
                      onClick={() => handleThemeChange(option.value)}
                    >
                      <CardContent sx={{ textAlign: "center", p: 3 }}>
                        <Icon
                          size={32}
                          color={
                            theme.theme === option.value
                              ? theme.primaryColor
                              : "#6b7280"
                          }
                          style={{ marginBottom: 8 }}
                        />
                        <Typography
                          variant="subtitle2"
                          fontWeight={600}
                          color={
                            theme.theme === option.value
                              ? theme.primaryColor
                              : "white"
                          }
                          sx={{ mb: 1 }}
                        >
                          {option.label}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {option.description}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>

            {/* Quick Toggle */}
            <Box
              sx={{
                mt: 3,
                p: 3,
                background: "rgba(255, 255, 255, 0.05)",
                borderRadius: 2,
              }}
            >
              <FormControlLabel
                control={
                  <Switch
                    checked={theme.darkMode}
                    onChange={() => dispatch(toggleDarkMode())}
                    sx={{
                      "& .MuiSwitch-switchBase.Mui-checked": {
                        color: theme.primaryColor,
                      },
                      "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track":
                        {
                          backgroundColor: theme.primaryColor,
                        },
                    }}
                  />
                }
                label={
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    {theme.darkMode ? <Moon size={20} /> : <Sun size={20} />}
                    <Typography variant="body1" color="white" fontWeight={600}>
                      {theme.darkMode ? "Dark Mode" : "Light Mode"}
                    </Typography>
                  </Box>
                }
              />
            </Box>
          </Grid>

          {/* Color Schemes */}
          <Grid item xs={12} md={6}>
            <Typography
              variant="h6"
              fontWeight={600}
              color="white"
              sx={{ mb: 3 }}
            >
              Color Schemes
            </Typography>
            <Grid container spacing={2}>
              {colorPresets.map((preset) => (
                <Grid item xs={4} key={preset.name}>
                  <Box sx={{ textAlign: "center" }}>
                    <ColorSwatch
                      preset={preset}
                      isSelected={theme.primaryColor === preset.primary}
                    />
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ mt: 1, display: "block" }}
                    >
                      {preset.name}
                    </Typography>
                  </Box>
                </Grid>
              ))}
            </Grid>

            {/* Current Colors */}
            <Box
              sx={{
                mt: 3,
                p: 3,
                background: "rgba(255, 255, 255, 0.05)",
                borderRadius: 2,
              }}
            >
              <Typography
                variant="subtitle2"
                color="white"
                fontWeight={600}
                sx={{ mb: 2 }}
              >
                Current Colors
              </Typography>
              <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
                <Box sx={{ textAlign: "center" }}>
                  <Box
                    sx={{
                      width: 40,
                      height: 40,
                      borderRadius: 1,
                      background: theme.primaryColor,
                      mb: 1,
                    }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    Primary
                  </Typography>
                </Box>
                <Box sx={{ textAlign: "center" }}>
                  <Box
                    sx={{
                      width: 40,
                      height: 40,
                      borderRadius: 1,
                      background: theme.accentColor,
                      mb: 1,
                    }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    Accent
                  </Typography>
                </Box>
              </Box>
            </Box>
          </Grid>

          {/* Accessibility & Preferences */}
          <Grid item xs={12}>
            <Typography
              variant="h6"
              fontWeight={600}
              color="white"
              sx={{ mb: 3 }}
            >
              Accessibility & Preferences
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Card
                  sx={{
                    background: "rgba(255, 255, 255, 0.05)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 2,
                        mb: 2,
                      }}
                    >
                      <Type size={24} color={theme.primaryColor} />
                      <Typography
                        variant="subtitle1"
                        fontWeight={600}
                        color="white"
                      >
                        Font Size
                      </Typography>
                    </Box>
                    <ButtonGroup fullWidth size="small">
                      {fontSizes.map((size) => (
                        <Button
                          key={size.value}
                          variant={
                            theme.fontSize === size.value
                              ? "contained"
                              : "outlined"
                          }
                          onClick={() => dispatch(setFontSize(size.value))}
                          sx={{
                            borderColor: theme.primaryColor,
                            color:
                              theme.fontSize === size.value
                                ? "white"
                                : theme.primaryColor,
                            background:
                              theme.fontSize === size.value
                                ? theme.primaryColor
                                : "transparent",
                            "&:hover": {
                              borderColor: theme.primaryColor,
                              background:
                                theme.fontSize === size.value
                                  ? theme.accentColor
                                  : `${theme.primaryColor}20`,
                            },
                          }}
                        >
                          {size.label}
                        </Button>
                      ))}
                    </ButtonGroup>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={8}>
                <Card
                  sx={{
                    background: "rgba(255, 255, 255, 0.05)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Typography
                      variant="subtitle1"
                      fontWeight={600}
                      color="white"
                      sx={{ mb: 3 }}
                    >
                      Interface Options
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={theme.animations}
                              onChange={() => dispatch(toggleAnimations())}
                              sx={{
                                "& .MuiSwitch-switchBase.Mui-checked": {
                                  color: theme.primaryColor,
                                },
                                "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track":
                                  {
                                    backgroundColor: theme.primaryColor,
                                  },
                              }}
                            />
                          }
                          label={
                            <Box
                              sx={{
                                display: "flex",
                                alignItems: "center",
                                gap: 1,
                              }}
                            >
                              <Sparkles size={18} />
                              <Typography variant="body2" color="white">
                                Animations
                              </Typography>
                            </Box>
                          }
                        />
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={theme.compactMode}
                              onChange={() => dispatch(toggleCompactMode())}
                              sx={{
                                "& .MuiSwitch-switchBase.Mui-checked": {
                                  color: theme.primaryColor,
                                },
                                "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track":
                                  {
                                    backgroundColor: theme.primaryColor,
                                  },
                              }}
                            />
                          }
                          label={
                            <Box
                              sx={{
                                display: "flex",
                                alignItems: "center",
                                gap: 1,
                              }}
                            >
                              <Minimize2 size={18} />
                              <Typography variant="body2" color="white">
                                Compact Mode
                              </Typography>
                            </Box>
                          }
                        />
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={theme.highContrast}
                              onChange={() => dispatch(toggleHighContrast())}
                              sx={{
                                "& .MuiSwitch-switchBase.Mui-checked": {
                                  color: theme.primaryColor,
                                },
                                "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track":
                                  {
                                    backgroundColor: theme.primaryColor,
                                  },
                              }}
                            />
                          }
                          label={
                            <Box
                              sx={{
                                display: "flex",
                                alignItems: "center",
                                gap: 1,
                              }}
                            >
                              <Contrast size={18} />
                              <Typography variant="body2" color="white">
                                High Contrast
                              </Typography>
                            </Box>
                          }
                        />
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Grid>

          {/* Theme Preview */}
          <Grid item xs={12}>
            <Typography
              variant="h6"
              fontWeight={600}
              color="white"
              sx={{ mb: 3 }}
            >
              Preview
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Typography
                  variant="subtitle2"
                  color="text.secondary"
                  sx={{ mb: 1 }}
                >
                  Light Theme
                </Typography>
                <ThemePreview themeType="light" />
              </Grid>
              <Grid item xs={12} md={4}>
                <Typography
                  variant="subtitle2"
                  color="text.secondary"
                  sx={{ mb: 1 }}
                >
                  Dark Theme
                </Typography>
                <ThemePreview themeType="dark" />
              </Grid>
              <Grid item xs={12} md={4}>
                <Typography
                  variant="subtitle2"
                  color="text.secondary"
                  sx={{ mb: 1 }}
                >
                  Auto (System)
                </Typography>
                <ThemePreview themeType="auto" />
              </Grid>
            </Grid>
          </Grid>
        </Grid>

        {/* Snackbar */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={3000}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        >
          <Alert
            onClose={() => setSnackbar({ ...snackbar, open: false })}
            severity={snackbar.severity}
            sx={{
              background: "rgba(0, 0, 0, 0.9)",
              backdropFilter: "blur(20px)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              color: "white",
            }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Paper>
    </Fade>
  );
};

export default ThemeCustomizer;
