import {
  Alert,
  Avatar,
  Badge,
  Box,
  Button,
  Card,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Fade,
  FormControl,
  FormControlLabel,
  Grid,
  IconButton,
  InputLabel,
  List,
  ListItem,
  ListItemIcon,
  ListItemSecondaryAction,
  ListItemText,
  MenuItem,
  Paper,
  Select,
  Slider,
  Snackbar,
  Switch,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import {
  AlertTriangle,
  Bell,
  Edit,
  Key,
  Mail,
  RefreshCw,
  Save,
  Shield,
  Smartphone,
  Trash2,
  User,
} from "lucide-react";
import { useState } from "react";

const Settings = () => {
  const [selectedTab, setSelectedTab] = useState(0);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success",
  });
  const [_showPassword, _setShowPassword] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState({
    open: false,
    title: "",
    message: "",
    action: null,
  });

  // Settings state
  const [settings, setSettings] = useState({
    // Profile settings
    profile: {
      firstName: "John",
      lastName: "Doe",
      email: "john.doe@example.com",
      phone: "+1 (555) 123-4567",
      timezone: "America/New_York",
      language: "en",
      avatar: null,
    },
    // Security settings
    security: {
      twoFactorEnabled: true,
      biometricEnabled: false,
      sessionTimeout: 30,
      loginNotifications: true,
      apiKeysEnabled: true,
    },
    // Notification settings
    notifications: {
      email: {
        tradeExecutions: true,
        portfolioAlerts: true,
        systemUpdates: false,
        marketNews: true,
        weeklyReports: true,
      },
      push: {
        tradeExecutions: true,
        portfolioAlerts: true,
        priceAlerts: false,
        systemMaintenance: true,
      },
      sms: {
        criticalAlerts: true,
        loginAttempts: true,
        largeTransactions: false,
      },
    },
    // Trading settings
    trading: {
      defaultOrderType: "limit",
      confirmOrders: true,
      riskLevel: "medium",
      maxPositionSize: 10,
      stopLossDefault: 5,
      takeProfitDefault: 15,
      autoRebalance: false,
      paperTrading: false,
    },
    // Display settings
    display: {
      theme: "dark",
      currency: "USD",
      dateFormat: "MM/DD/YYYY",
      timeFormat: "12h",
      chartType: "candlestick",
      showAdvancedMetrics: true,
      compactView: false,
      animationsEnabled: true,
    },
  });

  const handleTabChange = (_event, newValue) => {
    setSelectedTab(newValue);
  };

  const handleSettingChange = (category, setting, value) => {
    setSettings((prev) => ({
      ...prev,
      [category]: {
        ...prev[category],
        [setting]: value,
      },
    }));
  };

  const handleNestedSettingChange = (category, subcategory, setting, value) => {
    setSettings((prev) => ({
      ...prev,
      [category]: {
        ...prev[category],
        [subcategory]: {
          ...prev[category][subcategory],
          [setting]: value,
        },
      },
    }));
  };

  const handleSaveSettings = () => {
    // Simulate API call
    setTimeout(() => {
      setSnackbar({
        open: true,
        message: "Settings saved successfully!",
        severity: "success",
      });
    }, 500);
  };

  const handleResetSettings = () => {
    setConfirmDialog({
      open: true,
      title: "Reset Settings",
      message:
        "Are you sure you want to reset all settings to default? This action cannot be undone.",
      action: () => {
        // Reset to default settings logic here
        setSnackbar({
          open: true,
          message: "Settings reset to default!",
          severity: "info",
        });
        setConfirmDialog({ open: false, title: "", message: "", action: null });
      },
    });
  };

  const ProfileSettings = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={4}>
        <Card
          sx={{
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
            textAlign: "center",
            p: 3,
          }}
        >
          <Badge
            overlap="circular"
            anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
            badgeContent={
              <IconButton
                size="small"
                sx={{ bgcolor: "#00d4ff", color: "white" }}
              >
                <Edit size={16} />
              </IconButton>
            }
          >
            <Avatar
              sx={{
                width: 120,
                height: 120,
                mx: "auto",
                mb: 2,
                bgcolor: "#00d4ff",
                fontSize: "2rem",
                fontWeight: 700,
              }}
            >
              {settings.profile.firstName[0]}
              {settings.profile.lastName[0]}
            </Avatar>
          </Badge>
          <Typography
            variant="h5"
            fontWeight={700}
            color="white"
            sx={{ mb: 1 }}
          >
            {settings.profile.firstName} {settings.profile.lastName}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Premium Member
          </Typography>
          <Button
            variant="outlined"
            fullWidth
            startIcon={<User size={16} />}
            sx={{
              borderColor: "#00d4ff",
              color: "#00d4ff",
              "&:hover": {
                borderColor: "#00d4ff",
                background: "rgba(0, 212, 255, 0.1)",
              },
            }}
          >
            Change Avatar
          </Button>
        </Card>
      </Grid>

      <Grid item xs={12} md={8}>
        <Card
          sx={{
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
            p: 3,
          }}
        >
          <Typography
            variant="h6"
            fontWeight={700}
            color="white"
            sx={{ mb: 3 }}
          >
            Personal Information
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="First Name"
                value={settings.profile.firstName}
                onChange={(e) =>
                  handleSettingChange("profile", "firstName", e.target.value)
                }
                sx={{
                  "& .MuiOutlinedInput-root": {
                    color: "white",
                    "& fieldset": { borderColor: "rgba(255, 255, 255, 0.3)" },
                    "&:hover fieldset": { borderColor: "#00d4ff" },
                    "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                  },
                  "& .MuiInputLabel-root": {
                    color: "rgba(255, 255, 255, 0.7)",
                  },
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Last Name"
                value={settings.profile.lastName}
                onChange={(e) =>
                  handleSettingChange("profile", "lastName", e.target.value)
                }
                sx={{
                  "& .MuiOutlinedInput-root": {
                    color: "white",
                    "& fieldset": { borderColor: "rgba(255, 255, 255, 0.3)" },
                    "&:hover fieldset": { borderColor: "#00d4ff" },
                    "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                  },
                  "& .MuiInputLabel-root": {
                    color: "rgba(255, 255, 255, 0.7)",
                  },
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Email Address"
                type="email"
                value={settings.profile.email}
                onChange={(e) =>
                  handleSettingChange("profile", "email", e.target.value)
                }
                sx={{
                  "& .MuiOutlinedInput-root": {
                    color: "white",
                    "& fieldset": { borderColor: "rgba(255, 255, 255, 0.3)" },
                    "&:hover fieldset": { borderColor: "#00d4ff" },
                    "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                  },
                  "& .MuiInputLabel-root": {
                    color: "rgba(255, 255, 255, 0.7)",
                  },
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Phone Number"
                value={settings.profile.phone}
                onChange={(e) =>
                  handleSettingChange("profile", "phone", e.target.value)
                }
                sx={{
                  "& .MuiOutlinedInput-root": {
                    color: "white",
                    "& fieldset": { borderColor: "rgba(255, 255, 255, 0.3)" },
                    "&:hover fieldset": { borderColor: "#00d4ff" },
                    "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                  },
                  "& .MuiInputLabel-root": {
                    color: "rgba(255, 255, 255, 0.7)",
                  },
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel sx={{ color: "rgba(255, 255, 255, 0.7)" }}>
                  Timezone
                </InputLabel>
                <Select
                  value={settings.profile.timezone}
                  onChange={(e) =>
                    handleSettingChange("profile", "timezone", e.target.value)
                  }
                  sx={{
                    color: "white",
                    "& .MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(255, 255, 255, 0.3)",
                    },
                    "&:hover .MuiOutlinedInput-notchedOutline": {
                      borderColor: "#00d4ff",
                    },
                    "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                      borderColor: "#00d4ff",
                    },
                  }}
                >
                  <MenuItem value="America/New_York">Eastern Time</MenuItem>
                  <MenuItem value="America/Chicago">Central Time</MenuItem>
                  <MenuItem value="America/Denver">Mountain Time</MenuItem>
                  <MenuItem value="America/Los_Angeles">Pacific Time</MenuItem>
                  <MenuItem value="Europe/London">London</MenuItem>
                  <MenuItem value="Asia/Tokyo">Tokyo</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel sx={{ color: "rgba(255, 255, 255, 0.7)" }}>
                  Language
                </InputLabel>
                <Select
                  value={settings.profile.language}
                  onChange={(e) =>
                    handleSettingChange("profile", "language", e.target.value)
                  }
                  sx={{
                    color: "white",
                    "& .MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(255, 255, 255, 0.3)",
                    },
                    "&:hover .MuiOutlinedInput-notchedOutline": {
                      borderColor: "#00d4ff",
                    },
                    "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                      borderColor: "#00d4ff",
                    },
                  }}
                >
                  <MenuItem value="en">English</MenuItem>
                  <MenuItem value="es">Spanish</MenuItem>
                  <MenuItem value="fr">French</MenuItem>
                  <MenuItem value="de">German</MenuItem>
                  <MenuItem value="ja">Japanese</MenuItem>
                  <MenuItem value="zh">Chinese</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Card>
      </Grid>
    </Grid>
  );

  const SecuritySettings = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card
          sx={{
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
            p: 3,
          }}
        >
          <Typography
            variant="h6"
            fontWeight={700}
            color="white"
            sx={{ mb: 3 }}
          >
            Authentication
          </Typography>
          <List>
            <ListItem>
              <ListItemIcon>
                <Shield size={20} color="#10b981" />
              </ListItemIcon>
              <ListItemText
                primary="Two-Factor Authentication"
                secondary="Add an extra layer of security"
                primaryTypographyProps={{ color: "white" }}
                secondaryTypographyProps={{ color: "text.secondary" }}
              />
              <ListItemSecondaryAction>
                <Switch
                  checked={settings.security.twoFactorEnabled}
                  onChange={(e) =>
                    handleSettingChange(
                      "security",
                      "twoFactorEnabled",
                      e.target.checked,
                    )
                  }
                  color="primary"
                />
              </ListItemSecondaryAction>
            </ListItem>
            <Divider sx={{ bgcolor: "rgba(255, 255, 255, 0.1)" }} />
            <ListItem>
              <ListItemIcon>
                <Smartphone size={20} color="#00d4ff" />
              </ListItemIcon>
              <ListItemText
                primary="Biometric Login"
                secondary="Use fingerprint or face ID"
                primaryTypographyProps={{ color: "white" }}
                secondaryTypographyProps={{ color: "text.secondary" }}
              />
              <ListItemSecondaryAction>
                <Switch
                  checked={settings.security.biometricEnabled}
                  onChange={(e) =>
                    handleSettingChange(
                      "security",
                      "biometricEnabled",
                      e.target.checked,
                    )
                  }
                  color="primary"
                />
              </ListItemSecondaryAction>
            </ListItem>
            <Divider sx={{ bgcolor: "rgba(255, 255, 255, 0.1)" }} />
            <ListItem>
              <ListItemIcon>
                <Bell size={20} color="#f59e0b" />
              </ListItemIcon>
              <ListItemText
                primary="Login Notifications"
                secondary="Get notified of new logins"
                primaryTypographyProps={{ color: "white" }}
                secondaryTypographyProps={{ color: "text.secondary" }}
              />
              <ListItemSecondaryAction>
                <Switch
                  checked={settings.security.loginNotifications}
                  onChange={(e) =>
                    handleSettingChange(
                      "security",
                      "loginNotifications",
                      e.target.checked,
                    )
                  }
                  color="primary"
                />
              </ListItemSecondaryAction>
            </ListItem>
          </List>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card
          sx={{
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
            p: 3,
          }}
        >
          <Typography
            variant="h6"
            fontWeight={700}
            color="white"
            sx={{ mb: 3 }}
          >
            Session & Security
          </Typography>
          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Session Timeout: {settings.security.sessionTimeout} minutes
            </Typography>
            <Slider
              value={settings.security.sessionTimeout}
              onChange={(_e, value) =>
                handleSettingChange("security", "sessionTimeout", value)
              }
              min={5}
              max={120}
              step={5}
              marks={[
                { value: 5, label: "5m" },
                { value: 30, label: "30m" },
                { value: 60, label: "1h" },
                { value: 120, label: "2h" },
              ]}
              sx={{
                color: "#00d4ff",
                "& .MuiSlider-thumb": {
                  backgroundColor: "#00d4ff",
                },
                "& .MuiSlider-track": {
                  backgroundColor: "#00d4ff",
                },
                "& .MuiSlider-rail": {
                  backgroundColor: "rgba(255, 255, 255, 0.3)",
                },
              }}
            />
          </Box>
          <Divider sx={{ bgcolor: "rgba(255, 255, 255, 0.1)", my: 2 }} />
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<Key size={16} />}
              sx={{
                borderColor: "#00d4ff",
                color: "#00d4ff",
                "&:hover": {
                  borderColor: "#00d4ff",
                  background: "rgba(0, 212, 255, 0.1)",
                },
              }}
            >
              Change Password
            </Button>
            <Button
              variant="outlined"
              startIcon={<RefreshCw size={16} />}
              sx={{
                borderColor: "#f59e0b",
                color: "#f59e0b",
                "&:hover": {
                  borderColor: "#f59e0b",
                  background: "rgba(245, 158, 11, 0.1)",
                },
              }}
            >
              Revoke All Sessions
            </Button>
            <Button
              variant="outlined"
              startIcon={<Trash2 size={16} />}
              sx={{
                borderColor: "#ef4444",
                color: "#ef4444",
                "&:hover": {
                  borderColor: "#ef4444",
                  background: "rgba(239, 68, 68, 0.1)",
                },
              }}
            >
              Delete Account
            </Button>
          </Box>
        </Card>
      </Grid>
    </Grid>
  );

  const NotificationSettings = () => (
    <Grid container spacing={3}>
      {/* Email Notifications */}
      <Grid item xs={12} md={4}>
        <Card
          sx={{
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
            p: 3,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", mb: 3 }}>
            <Mail size={20} color="#00d4ff" />
            <Typography
              variant="h6"
              fontWeight={700}
              color="white"
              sx={{ ml: 1 }}
            >
              Email Notifications
            </Typography>
          </Box>
          <List dense>
            {Object.entries(settings.notifications.email).map(
              ([key, value]) => (
                <ListItem key={key} sx={{ px: 0 }}>
                  <ListItemText
                    primary={key
                      .replace(/([A-Z])/g, " $1")
                      .replace(/^./, (str) => str.toUpperCase())}
                    primaryTypographyProps={{
                      color: "white",
                      fontSize: "0.875rem",
                    }}
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      size="small"
                      checked={value}
                      onChange={(e) =>
                        handleNestedSettingChange(
                          "notifications",
                          "email",
                          key,
                          e.target.checked,
                        )
                      }
                      color="primary"
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              ),
            )}
          </List>
        </Card>
      </Grid>

      {/* Push Notifications */}
      <Grid item xs={12} md={4}>
        <Card
          sx={{
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
            p: 3,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", mb: 3 }}>
            <Bell size={20} color="#10b981" />
            <Typography
              variant="h6"
              fontWeight={700}
              color="white"
              sx={{ ml: 1 }}
            >
              Push Notifications
            </Typography>
          </Box>
          <List dense>
            {Object.entries(settings.notifications.push).map(([key, value]) => (
              <ListItem key={key} sx={{ px: 0 }}>
                <ListItemText
                  primary={key
                    .replace(/([A-Z])/g, " $1")
                    .replace(/^./, (str) => str.toUpperCase())}
                  primaryTypographyProps={{
                    color: "white",
                    fontSize: "0.875rem",
                  }}
                />
                <ListItemSecondaryAction>
                  <Switch
                    size="small"
                    checked={value}
                    onChange={(e) =>
                      handleNestedSettingChange(
                        "notifications",
                        "push",
                        key,
                        e.target.checked,
                      )
                    }
                    color="primary"
                  />
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        </Card>
      </Grid>

      {/* SMS Notifications */}
      <Grid item xs={12} md={4}>
        <Card
          sx={{
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
            p: 3,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", mb: 3 }}>
            <Smartphone size={20} color="#f59e0b" />
            <Typography
              variant="h6"
              fontWeight={700}
              color="white"
              sx={{ ml: 1 }}
            >
              SMS Notifications
            </Typography>
          </Box>
          <List dense>
            {Object.entries(settings.notifications.sms).map(([key, value]) => (
              <ListItem key={key} sx={{ px: 0 }}>
                <ListItemText
                  primary={key
                    .replace(/([A-Z])/g, " $1")
                    .replace(/^./, (str) => str.toUpperCase())}
                  primaryTypographyProps={{
                    color: "white",
                    fontSize: "0.875rem",
                  }}
                />
                <ListItemSecondaryAction>
                  <Switch
                    size="small"
                    checked={value}
                    onChange={(e) =>
                      handleNestedSettingChange(
                        "notifications",
                        "sms",
                        key,
                        e.target.checked,
                      )
                    }
                    color="primary"
                  />
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        </Card>
      </Grid>
    </Grid>
  );

  const TradingSettings = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card
          sx={{
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
            p: 3,
          }}
        >
          <Typography
            variant="h6"
            fontWeight={700}
            color="white"
            sx={{ mb: 3 }}
          >
            Order Defaults
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel sx={{ color: "rgba(255, 255, 255, 0.7)" }}>
                  Default Order Type
                </InputLabel>
                <Select
                  value={settings.trading.defaultOrderType}
                  onChange={(e) =>
                    handleSettingChange(
                      "trading",
                      "defaultOrderType",
                      e.target.value,
                    )
                  }
                  sx={{
                    color: "white",
                    "& .MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(255, 255, 255, 0.3)",
                    },
                    "&:hover .MuiOutlinedInput-notchedOutline": {
                      borderColor: "#00d4ff",
                    },
                    "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                      borderColor: "#00d4ff",
                    },
                  }}
                >
                  <MenuItem value="market">Market Order</MenuItem>
                  <MenuItem value="limit">Limit Order</MenuItem>
                  <MenuItem value="stop">Stop Order</MenuItem>
                  <MenuItem value="stop-limit">Stop-Limit Order</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.trading.confirmOrders}
                    onChange={(e) =>
                      handleSettingChange(
                        "trading",
                        "confirmOrders",
                        e.target.checked,
                      )
                    }
                    color="primary"
                  />
                }
                label="Confirm orders before execution"
                sx={{ color: "white" }}
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Maximum Position Size: {settings.trading.maxPositionSize}%
              </Typography>
              <Slider
                value={settings.trading.maxPositionSize}
                onChange={(_e, value) =>
                  handleSettingChange("trading", "maxPositionSize", value)
                }
                min={1}
                max={50}
                step={1}
                marks={[
                  { value: 1, label: "1%" },
                  { value: 10, label: "10%" },
                  { value: 25, label: "25%" },
                  { value: 50, label: "50%" },
                ]}
                sx={{
                  color: "#00d4ff",
                  "& .MuiSlider-thumb": { backgroundColor: "#00d4ff" },
                  "& .MuiSlider-track": { backgroundColor: "#00d4ff" },
                  "& .MuiSlider-rail": {
                    backgroundColor: "rgba(255, 255, 255, 0.3)",
                  },
                }}
              />
            </Grid>
          </Grid>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card
          sx={{
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
            p: 3,
          }}
        >
          <Typography
            variant="h6"
            fontWeight={700}
            color="white"
            sx={{ mb: 3 }}
          >
            Risk Management
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel sx={{ color: "rgba(255, 255, 255, 0.7)" }}>
                  Risk Level
                </InputLabel>
                <Select
                  value={settings.trading.riskLevel}
                  onChange={(e) =>
                    handleSettingChange("trading", "riskLevel", e.target.value)
                  }
                  sx={{
                    color: "white",
                    "& .MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(255, 255, 255, 0.3)",
                    },
                    "&:hover .MuiOutlinedInput-notchedOutline": {
                      borderColor: "#00d4ff",
                    },
                    "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                      borderColor: "#00d4ff",
                    },
                  }}
                >
                  <MenuItem value="conservative">Conservative</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="aggressive">Aggressive</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="number"
                label="Default Stop Loss (%)"
                value={settings.trading.stopLossDefault}
                onChange={(e) =>
                  handleSettingChange(
                    "trading",
                    "stopLossDefault",
                    parseInt(e.target.value, 10),
                  )
                }
                inputProps={{ min: 1, max: 50 }}
                sx={{
                  "& .MuiOutlinedInput-root": {
                    color: "white",
                    "& fieldset": { borderColor: "rgba(255, 255, 255, 0.3)" },
                    "&:hover fieldset": { borderColor: "#00d4ff" },
                    "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                  },
                  "& .MuiInputLabel-root": {
                    color: "rgba(255, 255, 255, 0.7)",
                  },
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="number"
                label="Default Take Profit (%)"
                value={settings.trading.takeProfitDefault}
                onChange={(e) =>
                  handleSettingChange(
                    "trading",
                    "takeProfitDefault",
                    parseInt(e.target.value, 10),
                  )
                }
                inputProps={{ min: 1, max: 100 }}
                sx={{
                  "& .MuiOutlinedInput-root": {
                    color: "white",
                    "& fieldset": { borderColor: "rgba(255, 255, 255, 0.3)" },
                    "&:hover fieldset": { borderColor: "#00d4ff" },
                    "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                  },
                  "& .MuiInputLabel-root": {
                    color: "rgba(255, 255, 255, 0.7)",
                  },
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.trading.autoRebalance}
                    onChange={(e) =>
                      handleSettingChange(
                        "trading",
                        "autoRebalance",
                        e.target.checked,
                      )
                    }
                    color="primary"
                  />
                }
                label="Enable automatic portfolio rebalancing"
                sx={{ color: "white" }}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.trading.paperTrading}
                    onChange={(e) =>
                      handleSettingChange(
                        "trading",
                        "paperTrading",
                        e.target.checked,
                      )
                    }
                    color="primary"
                  />
                }
                label="Paper trading mode"
                sx={{ color: "white" }}
              />
            </Grid>
          </Grid>
        </Card>
      </Grid>
    </Grid>
  );

  const DisplaySettings = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card
          sx={{
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
            p: 3,
          }}
        >
          <Typography
            variant="h6"
            fontWeight={700}
            color="white"
            sx={{ mb: 3 }}
          >
            Appearance
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel sx={{ color: "rgba(255, 255, 255, 0.7)" }}>
                  Theme
                </InputLabel>
                <Select
                  value={settings.display.theme}
                  onChange={(e) =>
                    handleSettingChange("display", "theme", e.target.value)
                  }
                  sx={{
                    color: "white",
                    "& .MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(255, 255, 255, 0.3)",
                    },
                    "&:hover .MuiOutlinedInput-notchedOutline": {
                      borderColor: "#00d4ff",
                    },
                    "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                      borderColor: "#00d4ff",
                    },
                  }}
                >
                  <MenuItem value="dark">Dark</MenuItem>
                  <MenuItem value="light">Light</MenuItem>
                  <MenuItem value="auto">Auto</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel sx={{ color: "rgba(255, 255, 255, 0.7)" }}>
                  Currency
                </InputLabel>
                <Select
                  value={settings.display.currency}
                  onChange={(e) =>
                    handleSettingChange("display", "currency", e.target.value)
                  }
                  sx={{
                    color: "white",
                    "& .MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(255, 255, 255, 0.3)",
                    },
                    "&:hover .MuiOutlinedInput-notchedOutline": {
                      borderColor: "#00d4ff",
                    },
                    "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                      borderColor: "#00d4ff",
                    },
                  }}
                >
                  <MenuItem value="USD">USD ($)</MenuItem>
                  <MenuItem value="EUR">EUR (€)</MenuItem>
                  <MenuItem value="GBP">GBP (£)</MenuItem>
                  <MenuItem value="JPY">JPY (¥)</MenuItem>
                  <MenuItem value="CAD">CAD (C$)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel sx={{ color: "rgba(255, 255, 255, 0.7)" }}>
                  Date Format
                </InputLabel>
                <Select
                  value={settings.display.dateFormat}
                  onChange={(e) =>
                    handleSettingChange("display", "dateFormat", e.target.value)
                  }
                  sx={{
                    color: "white",
                    "& .MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(255, 255, 255, 0.3)",
                    },
                    "&:hover .MuiOutlinedInput-notchedOutline": {
                      borderColor: "#00d4ff",
                    },
                    "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                      borderColor: "#00d4ff",
                    },
                  }}
                >
                  <MenuItem value="MM/DD/YYYY">MM/DD/YYYY</MenuItem>
                  <MenuItem value="DD/MM/YYYY">DD/MM/YYYY</MenuItem>
                  <MenuItem value="YYYY-MM-DD">YYYY-MM-DD</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel sx={{ color: "rgba(255, 255, 255, 0.7)" }}>
                  Time Format
                </InputLabel>
                <Select
                  value={settings.display.timeFormat}
                  onChange={(e) =>
                    handleSettingChange("display", "timeFormat", e.target.value)
                  }
                  sx={{
                    color: "white",
                    "& .MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(255, 255, 255, 0.3)",
                    },
                    "&:hover .MuiOutlinedInput-notchedOutline": {
                      borderColor: "#00d4ff",
                    },
                    "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                      borderColor: "#00d4ff",
                    },
                  }}
                >
                  <MenuItem value="12h">12 Hour</MenuItem>
                  <MenuItem value="24h">24 Hour</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card
          sx={{
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
            p: 3,
          }}
        >
          <Typography
            variant="h6"
            fontWeight={700}
            color="white"
            sx={{ mb: 3 }}
          >
            Interface
          </Typography>
          <List>
            <ListItem>
              <ListItemText
                primary="Show Advanced Metrics"
                secondary="Display detailed analytics and metrics"
                primaryTypographyProps={{ color: "white" }}
                secondaryTypographyProps={{ color: "text.secondary" }}
              />
              <ListItemSecondaryAction>
                <Switch
                  checked={settings.display.showAdvancedMetrics}
                  onChange={(e) =>
                    handleSettingChange(
                      "display",
                      "showAdvancedMetrics",
                      e.target.checked,
                    )
                  }
                  color="primary"
                />
              </ListItemSecondaryAction>
            </ListItem>
            <Divider sx={{ bgcolor: "rgba(255, 255, 255, 0.1)" }} />
            <ListItem>
              <ListItemText
                primary="Compact View"
                secondary="Use smaller spacing and components"
                primaryTypographyProps={{ color: "white" }}
                secondaryTypographyProps={{ color: "text.secondary" }}
              />
              <ListItemSecondaryAction>
                <Switch
                  checked={settings.display.compactView}
                  onChange={(e) =>
                    handleSettingChange(
                      "display",
                      "compactView",
                      e.target.checked,
                    )
                  }
                  color="primary"
                />
              </ListItemSecondaryAction>
            </ListItem>
            <Divider sx={{ bgcolor: "rgba(255, 255, 255, 0.1)" }} />
            <ListItem>
              <ListItemText
                primary="Enable Animations"
                secondary="Use smooth transitions and animations"
                primaryTypographyProps={{ color: "white" }}
                secondaryTypographyProps={{ color: "text.secondary" }}
              />
              <ListItemSecondaryAction>
                <Switch
                  checked={settings.display.animationsEnabled}
                  onChange={(e) =>
                    handleSettingChange(
                      "display",
                      "animationsEnabled",
                      e.target.checked,
                    )
                  }
                  color="primary"
                />
              </ListItemSecondaryAction>
            </ListItem>
          </List>
        </Card>
      </Grid>
    </Grid>
  );

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background:
          "linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%)",
        py: 4,
      }}
    >
      <Container maxWidth="xl">
        {/* Header */}
        <Fade in={true} timeout={800}>
          <Box sx={{ mb: 4 }}>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                mb: 2,
              }}
            >
              <Typography
                variant="h3"
                fontWeight={800}
                sx={{
                  background: "linear-gradient(45deg, #00d4ff, #8b5cf6)",
                  backgroundClip: "text",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                Settings
              </Typography>
              <Box sx={{ display: "flex", gap: 2 }}>
                <Button
                  variant="outlined"
                  startIcon={<RefreshCw size={20} />}
                  onClick={handleResetSettings}
                  sx={{
                    borderColor: "#f59e0b",
                    color: "#f59e0b",
                    "&:hover": {
                      borderColor: "#f59e0b",
                      background: "rgba(245, 158, 11, 0.1)",
                    },
                  }}
                >
                  Reset
                </Button>
                <Button
                  variant="contained"
                  startIcon={<Save size={20} />}
                  onClick={handleSaveSettings}
                  sx={{
                    background: "linear-gradient(45deg, #00d4ff, #0099cc)",
                    boxShadow: "0 4px 20px rgba(0, 212, 255, 0.3)",
                    "&:hover": {
                      background: "linear-gradient(45deg, #0099cc, #0066aa)",
                      boxShadow: "0 6px 25px rgba(0, 212, 255, 0.4)",
                    },
                  }}
                >
                  Save Changes
                </Button>
              </Box>
            </Box>
            <Typography variant="h6" color="text.secondary">
              Customize your trading platform experience
            </Typography>
          </Box>
        </Fade>

        {/* Tabs */}
        <Paper
          sx={{
            mb: 4,
            background: "rgba(255, 255, 255, 0.05)",
            backdropFilter: "blur(10px)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
          }}
        >
          <Tabs
            value={selectedTab}
            onChange={handleTabChange}
            variant="scrollable"
            scrollButtons="auto"
            sx={{
              "& .MuiTab-root": {
                color: "rgba(255, 255, 255, 0.7)",
                fontWeight: 600,
                "&.Mui-selected": {
                  color: "#00d4ff",
                },
              },
              "& .MuiTabs-indicator": {
                backgroundColor: "#00d4ff",
              },
            }}
          >
            <Tab label="Profile" />
            <Tab label="Security" />
            <Tab label="Notifications" />
            <Tab label="Trading" />
            <Tab label="Display" />
          </Tabs>
        </Paper>

        {/* Tab Content */}
        {selectedTab === 0 && <ProfileSettings />}
        {selectedTab === 1 && <SecuritySettings />}
        {selectedTab === 2 && <NotificationSettings />}
        {selectedTab === 3 && <TradingSettings />}
        {selectedTab === 4 && <DisplaySettings />}

        {/* Confirmation Dialog */}
        <Dialog
          open={confirmDialog.open}
          onClose={() =>
            setConfirmDialog({
              open: false,
              title: "",
              message: "",
              action: null,
            })
          }
          PaperProps={{
            sx: {
              background: "rgba(15, 15, 35, 0.95)",
              backdropFilter: "blur(20px)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: 3,
            },
          }}
        >
          <DialogTitle
            sx={{
              color: "white",
              display: "flex",
              alignItems: "center",
              gap: 1,
            }}
          >
            <AlertTriangle size={20} color="#f59e0b" />
            {confirmDialog.title}
          </DialogTitle>
          <DialogContent>
            <Typography color="text.secondary">
              {confirmDialog.message}
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button
              onClick={() =>
                setConfirmDialog({
                  open: false,
                  title: "",
                  message: "",
                  action: null,
                })
              }
              sx={{ color: "rgba(255, 255, 255, 0.7)" }}
            >
              Cancel
            </Button>
            <Button
              onClick={confirmDialog.action}
              variant="contained"
              sx={{
                background: "#ef4444",
                "&:hover": { background: "#dc2626" },
              }}
            >
              Confirm
            </Button>
          </DialogActions>
        </Dialog>

        {/* Snackbar */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={4000}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
        >
          <Alert
            severity={snackbar.severity}
            onClose={() => setSnackbar({ ...snackbar, open: false })}
            sx={{
              background: "rgba(0, 0, 0, 0.8)",
              color: "white",
              "& .MuiAlert-icon": { color: "inherit" },
            }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Container>
    </Box>
  );
};

export default Settings;
