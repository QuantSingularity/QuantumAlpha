import {
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  Divider,
  Fade,
  Grid,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemSecondaryAction,
  ListItemText,
  Paper,
  Switch,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import {
  Activity,
  Bell,
  Calendar,
  Camera,
  DollarSign,
  Edit,
  Globe,
  Lock,
  Mail,
  MapPin,
  Phone,
  Save,
  Shield,
  Smartphone,
  User,
} from "lucide-react";
import { useState } from "react";

const Profile = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [editMode, setEditMode] = useState(false);
  const [_showPassword, _setShowPassword] = useState(false);
  const [profileData, setProfileData] = useState({
    firstName: "John",
    lastName: "Doe",
    email: "john.doe@example.com",
    phone: "+1 (555) 123-4567",
    address: "123 Wall Street, New York, NY 10005",
    dateOfBirth: "1990-05-15",
    occupation: "Financial Analyst",
    riskTolerance: "Medium",
    investmentExperience: "Intermediate",
    preferredCurrency: "USD",
    timezone: "EST (UTC-5)",
    twoFactorEnabled: true,
    emailNotifications: true,
    smsNotifications: false,
    pushNotifications: true,
    marketAlerts: true,
    tradingAlerts: true,
    newsAlerts: false,
  });

  const handleInputChange = (field, value) => {
    setProfileData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSave = () => {
    setEditMode(false);
    // Here you would typically save to backend
    console.log("Saving profile data:", profileData);
  };

  const TabPanel = ({ children, value, index }) => (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );

  const StatCard = ({ icon: Icon, title, value, color }) => (
    <Card
      sx={{
        background: `linear-gradient(135deg, ${color}15, ${color}05)`,
        border: `1px solid ${color}30`,
        borderRadius: 3,
        transition: "all 0.3s ease",
        "&:hover": {
          transform: "translateY(-2px)",
          boxShadow: `0 8px 25px ${color}25`,
        },
      }}
    >
      <CardContent sx={{ p: 3, textAlign: "center" }}>
        <Icon size={32} color={color} style={{ marginBottom: 16 }} />
        <Typography variant="h4" fontWeight={700} color={color} sx={{ mb: 1 }}>
          {value}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {title}
        </Typography>
      </CardContent>
    </Card>
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
        {/* Header Section */}
        <Fade in={true} timeout={800}>
          <Paper
            elevation={0}
            sx={{
              p: 4,
              mb: 4,
              borderRadius: 4,
              background: "rgba(255, 255, 255, 0.05)",
              backdropFilter: "blur(20px)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",
            }}
          >
            <Grid container spacing={3} alignItems="center">
              <Grid item>
                <Box sx={{ position: "relative" }}>
                  <Avatar
                    sx={{
                      width: 120,
                      height: 120,
                      background: "linear-gradient(45deg, #00d4ff, #0099cc)",
                      fontSize: "2rem",
                      fontWeight: 700,
                    }}
                  >
                    {profileData.firstName[0]}
                    {profileData.lastName[0]}
                  </Avatar>
                  <IconButton
                    sx={{
                      position: "absolute",
                      bottom: 0,
                      right: 0,
                      background: "#00d4ff",
                      color: "white",
                      "&:hover": { background: "#0099cc" },
                    }}
                    size="small"
                  >
                    <Camera size={16} />
                  </IconButton>
                </Box>
              </Grid>
              <Grid item xs>
                <Typography
                  variant="h3"
                  fontWeight={700}
                  color="white"
                  sx={{ mb: 1 }}
                >
                  {profileData.firstName} {profileData.lastName}
                </Typography>
                <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
                  {profileData.occupation}
                </Typography>
                <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
                  <Chip
                    label={`Risk: ${profileData.riskTolerance}`}
                    sx={{ background: "#f59e0b", color: "white" }}
                  />
                  <Chip
                    label={`Experience: ${profileData.investmentExperience}`}
                    sx={{ background: "#10b981", color: "white" }}
                  />
                  <Chip
                    label={
                      profileData.twoFactorEnabled
                        ? "2FA Enabled"
                        : "2FA Disabled"
                    }
                    sx={{
                      background: profileData.twoFactorEnabled
                        ? "#10b981"
                        : "#ef4444",
                      color: "white",
                    }}
                  />
                </Box>
              </Grid>
              <Grid item>
                <Button
                  variant={editMode ? "contained" : "outlined"}
                  startIcon={editMode ? <Save size={20} /> : <Edit size={20} />}
                  onClick={editMode ? handleSave : () => setEditMode(true)}
                  sx={{
                    px: 3,
                    py: 1.5,
                    fontWeight: 600,
                    borderColor: "#00d4ff",
                    color: editMode ? "white" : "#00d4ff",
                    background: editMode
                      ? "linear-gradient(45deg, #00d4ff, #0099cc)"
                      : "transparent",
                    "&:hover": {
                      borderColor: "#00d4ff",
                      background: editMode
                        ? "linear-gradient(45deg, #0099cc, #0066aa)"
                        : "rgba(0, 212, 255, 0.1)",
                    },
                  }}
                >
                  {editMode ? "Save Changes" : "Edit Profile"}
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Fade>

        {/* Stats Cards */}
        <Fade in={true} timeout={1000}>
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                icon={DollarSign}
                title="Portfolio Value"
                value="$125,847"
                color="#00d4ff"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                icon={Activity}
                title="Active Trades"
                value="23"
                color="#10b981"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                icon={Shield}
                title="Security Score"
                value="98%"
                color="#8b5cf6"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                icon={Calendar}
                title="Member Since"
                value="2022"
                color="#f59e0b"
              />
            </Grid>
          </Grid>
        </Fade>

        {/* Main Content */}
        <Fade in={true} timeout={1200}>
          <Paper
            elevation={0}
            sx={{
              borderRadius: 4,
              background: "rgba(255, 255, 255, 0.05)",
              backdropFilter: "blur(20px)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",
              overflow: "hidden",
            }}
          >
            <Tabs
              value={activeTab}
              onChange={(_e, newValue) => setActiveTab(newValue)}
              sx={{
                borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
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
              <Tab label="Personal Information" />
              <Tab label="Security Settings" />
              <Tab label="Notifications" />
              <Tab label="Trading Preferences" />
            </Tabs>

            {/* Personal Information Tab */}
            <TabPanel value={activeTab} index={0}>
              <Box sx={{ p: 4 }}>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="First Name"
                      value={profileData.firstName}
                      onChange={(e) =>
                        handleInputChange("firstName", e.target.value)
                      }
                      disabled={!editMode}
                      InputProps={{
                        startAdornment: (
                          <User
                            size={20}
                            color="#00d4ff"
                            style={{ marginRight: 8 }}
                          />
                        ),
                      }}
                      sx={{
                        "& .MuiOutlinedInput-root": {
                          background: "rgba(255, 255, 255, 0.05)",
                          "& fieldset": {
                            borderColor: "rgba(255, 255, 255, 0.2)",
                          },
                          "&:hover fieldset": { borderColor: "#00d4ff" },
                          "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                        },
                        "& .MuiInputLabel-root": {
                          color: "rgba(255, 255, 255, 0.7)",
                        },
                        "& .MuiOutlinedInput-input": { color: "white" },
                      }}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Last Name"
                      value={profileData.lastName}
                      onChange={(e) =>
                        handleInputChange("lastName", e.target.value)
                      }
                      disabled={!editMode}
                      InputProps={{
                        startAdornment: (
                          <User
                            size={20}
                            color="#00d4ff"
                            style={{ marginRight: 8 }}
                          />
                        ),
                      }}
                      sx={{
                        "& .MuiOutlinedInput-root": {
                          background: "rgba(255, 255, 255, 0.05)",
                          "& fieldset": {
                            borderColor: "rgba(255, 255, 255, 0.2)",
                          },
                          "&:hover fieldset": { borderColor: "#00d4ff" },
                          "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                        },
                        "& .MuiInputLabel-root": {
                          color: "rgba(255, 255, 255, 0.7)",
                        },
                        "& .MuiOutlinedInput-input": { color: "white" },
                      }}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Email"
                      value={profileData.email}
                      onChange={(e) =>
                        handleInputChange("email", e.target.value)
                      }
                      disabled={!editMode}
                      InputProps={{
                        startAdornment: (
                          <Mail
                            size={20}
                            color="#00d4ff"
                            style={{ marginRight: 8 }}
                          />
                        ),
                      }}
                      sx={{
                        "& .MuiOutlinedInput-root": {
                          background: "rgba(255, 255, 255, 0.05)",
                          "& fieldset": {
                            borderColor: "rgba(255, 255, 255, 0.2)",
                          },
                          "&:hover fieldset": { borderColor: "#00d4ff" },
                          "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                        },
                        "& .MuiInputLabel-root": {
                          color: "rgba(255, 255, 255, 0.7)",
                        },
                        "& .MuiOutlinedInput-input": { color: "white" },
                      }}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Phone"
                      value={profileData.phone}
                      onChange={(e) =>
                        handleInputChange("phone", e.target.value)
                      }
                      disabled={!editMode}
                      InputProps={{
                        startAdornment: (
                          <Phone
                            size={20}
                            color="#00d4ff"
                            style={{ marginRight: 8 }}
                          />
                        ),
                      }}
                      sx={{
                        "& .MuiOutlinedInput-root": {
                          background: "rgba(255, 255, 255, 0.05)",
                          "& fieldset": {
                            borderColor: "rgba(255, 255, 255, 0.2)",
                          },
                          "&:hover fieldset": { borderColor: "#00d4ff" },
                          "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                        },
                        "& .MuiInputLabel-root": {
                          color: "rgba(255, 255, 255, 0.7)",
                        },
                        "& .MuiOutlinedInput-input": { color: "white" },
                      }}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Address"
                      value={profileData.address}
                      onChange={(e) =>
                        handleInputChange("address", e.target.value)
                      }
                      disabled={!editMode}
                      InputProps={{
                        startAdornment: (
                          <MapPin
                            size={20}
                            color="#00d4ff"
                            style={{ marginRight: 8 }}
                          />
                        ),
                      }}
                      sx={{
                        "& .MuiOutlinedInput-root": {
                          background: "rgba(255, 255, 255, 0.05)",
                          "& fieldset": {
                            borderColor: "rgba(255, 255, 255, 0.2)",
                          },
                          "&:hover fieldset": { borderColor: "#00d4ff" },
                          "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                        },
                        "& .MuiInputLabel-root": {
                          color: "rgba(255, 255, 255, 0.7)",
                        },
                        "& .MuiOutlinedInput-input": { color: "white" },
                      }}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Date of Birth"
                      type="date"
                      value={profileData.dateOfBirth}
                      onChange={(e) =>
                        handleInputChange("dateOfBirth", e.target.value)
                      }
                      disabled={!editMode}
                      InputLabelProps={{ shrink: true }}
                      InputProps={{
                        startAdornment: (
                          <Calendar
                            size={20}
                            color="#00d4ff"
                            style={{ marginRight: 8 }}
                          />
                        ),
                      }}
                      sx={{
                        "& .MuiOutlinedInput-root": {
                          background: "rgba(255, 255, 255, 0.05)",
                          "& fieldset": {
                            borderColor: "rgba(255, 255, 255, 0.2)",
                          },
                          "&:hover fieldset": { borderColor: "#00d4ff" },
                          "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                        },
                        "& .MuiInputLabel-root": {
                          color: "rgba(255, 255, 255, 0.7)",
                        },
                        "& .MuiOutlinedInput-input": { color: "white" },
                      }}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Occupation"
                      value={profileData.occupation}
                      onChange={(e) =>
                        handleInputChange("occupation", e.target.value)
                      }
                      disabled={!editMode}
                      sx={{
                        "& .MuiOutlinedInput-root": {
                          background: "rgba(255, 255, 255, 0.05)",
                          "& fieldset": {
                            borderColor: "rgba(255, 255, 255, 0.2)",
                          },
                          "&:hover fieldset": { borderColor: "#00d4ff" },
                          "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                        },
                        "& .MuiInputLabel-root": {
                          color: "rgba(255, 255, 255, 0.7)",
                        },
                        "& .MuiOutlinedInput-input": { color: "white" },
                      }}
                    />
                  </Grid>
                </Grid>
              </Box>
            </TabPanel>

            {/* Security Settings Tab */}
            <TabPanel value={activeTab} index={1}>
              <Box sx={{ p: 4 }}>
                <List>
                  <ListItem>
                    <ListItemIcon>
                      <Lock color="#00d4ff" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Two-Factor Authentication"
                      secondary="Add an extra layer of security to your account"
                      primaryTypographyProps={{ color: "white" }}
                      secondaryTypographyProps={{ color: "text.secondary" }}
                    />
                    <ListItemSecondaryAction>
                      <Switch
                        checked={profileData.twoFactorEnabled}
                        onChange={(e) =>
                          handleInputChange(
                            "twoFactorEnabled",
                            e.target.checked,
                          )
                        }
                        sx={{
                          "& .MuiSwitch-switchBase.Mui-checked": {
                            color: "#00d4ff",
                          },
                          "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track":
                            {
                              backgroundColor: "#00d4ff",
                            },
                        }}
                      />
                    </ListItemSecondaryAction>
                  </ListItem>
                  <Divider
                    sx={{ backgroundColor: "rgba(255, 255, 255, 0.1)" }}
                  />
                  <ListItem>
                    <ListItemIcon>
                      <Smartphone color="#00d4ff" />
                    </ListItemIcon>
                    <ListItemText
                      primary="SMS Verification"
                      secondary="Receive verification codes via SMS"
                      primaryTypographyProps={{ color: "white" }}
                      secondaryTypographyProps={{ color: "text.secondary" }}
                    />
                    <ListItemSecondaryAction>
                      <Button
                        variant="outlined"
                        size="small"
                        sx={{ borderColor: "#00d4ff", color: "#00d4ff" }}
                      >
                        Setup
                      </Button>
                    </ListItemSecondaryAction>
                  </ListItem>
                  <Divider
                    sx={{ backgroundColor: "rgba(255, 255, 255, 0.1)" }}
                  />
                  <ListItem>
                    <ListItemIcon>
                      <Shield color="#00d4ff" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Login Sessions"
                      secondary="Manage your active login sessions"
                      primaryTypographyProps={{ color: "white" }}
                      secondaryTypographyProps={{ color: "text.secondary" }}
                    />
                    <ListItemSecondaryAction>
                      <Button
                        variant="outlined"
                        size="small"
                        sx={{ borderColor: "#00d4ff", color: "#00d4ff" }}
                      >
                        View All
                      </Button>
                    </ListItemSecondaryAction>
                  </ListItem>
                </List>
              </Box>
            </TabPanel>

            {/* Notifications Tab */}
            <TabPanel value={activeTab} index={2}>
              <Box sx={{ p: 4 }}>
                <List>
                  <ListItem>
                    <ListItemIcon>
                      <Mail color="#00d4ff" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Email Notifications"
                      secondary="Receive updates via email"
                      primaryTypographyProps={{ color: "white" }}
                      secondaryTypographyProps={{ color: "text.secondary" }}
                    />
                    <ListItemSecondaryAction>
                      <Switch
                        checked={profileData.emailNotifications}
                        onChange={(e) =>
                          handleInputChange(
                            "emailNotifications",
                            e.target.checked,
                          )
                        }
                        sx={{
                          "& .MuiSwitch-switchBase.Mui-checked": {
                            color: "#00d4ff",
                          },
                          "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track":
                            {
                              backgroundColor: "#00d4ff",
                            },
                        }}
                      />
                    </ListItemSecondaryAction>
                  </ListItem>
                  <Divider
                    sx={{ backgroundColor: "rgba(255, 255, 255, 0.1)" }}
                  />
                  <ListItem>
                    <ListItemIcon>
                      <Smartphone color="#00d4ff" />
                    </ListItemIcon>
                    <ListItemText
                      primary="SMS Notifications"
                      secondary="Receive updates via SMS"
                      primaryTypographyProps={{ color: "white" }}
                      secondaryTypographyProps={{ color: "text.secondary" }}
                    />
                    <ListItemSecondaryAction>
                      <Switch
                        checked={profileData.smsNotifications}
                        onChange={(e) =>
                          handleInputChange(
                            "smsNotifications",
                            e.target.checked,
                          )
                        }
                        sx={{
                          "& .MuiSwitch-switchBase.Mui-checked": {
                            color: "#00d4ff",
                          },
                          "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track":
                            {
                              backgroundColor: "#00d4ff",
                            },
                        }}
                      />
                    </ListItemSecondaryAction>
                  </ListItem>
                  <Divider
                    sx={{ backgroundColor: "rgba(255, 255, 255, 0.1)" }}
                  />
                  <ListItem>
                    <ListItemIcon>
                      <Bell color="#00d4ff" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Push Notifications"
                      secondary="Receive push notifications in browser"
                      primaryTypographyProps={{ color: "white" }}
                      secondaryTypographyProps={{ color: "text.secondary" }}
                    />
                    <ListItemSecondaryAction>
                      <Switch
                        checked={profileData.pushNotifications}
                        onChange={(e) =>
                          handleInputChange(
                            "pushNotifications",
                            e.target.checked,
                          )
                        }
                        sx={{
                          "& .MuiSwitch-switchBase.Mui-checked": {
                            color: "#00d4ff",
                          },
                          "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track":
                            {
                              backgroundColor: "#00d4ff",
                            },
                        }}
                      />
                    </ListItemSecondaryAction>
                  </ListItem>
                  <Divider
                    sx={{ backgroundColor: "rgba(255, 255, 255, 0.1)" }}
                  />
                  <ListItem>
                    <ListItemIcon>
                      <Activity color="#00d4ff" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Trading Alerts"
                      secondary="Get notified about trade executions and opportunities"
                      primaryTypographyProps={{ color: "white" }}
                      secondaryTypographyProps={{ color: "text.secondary" }}
                    />
                    <ListItemSecondaryAction>
                      <Switch
                        checked={profileData.tradingAlerts}
                        onChange={(e) =>
                          handleInputChange("tradingAlerts", e.target.checked)
                        }
                        sx={{
                          "& .MuiSwitch-switchBase.Mui-checked": {
                            color: "#00d4ff",
                          },
                          "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track":
                            {
                              backgroundColor: "#00d4ff",
                            },
                        }}
                      />
                    </ListItemSecondaryAction>
                  </ListItem>
                </List>
              </Box>
            </TabPanel>

            {/* Trading Preferences Tab */}
            <TabPanel value={activeTab} index={3}>
              <Box sx={{ p: 4 }}>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      select
                      label="Risk Tolerance"
                      value={profileData.riskTolerance}
                      onChange={(e) =>
                        handleInputChange("riskTolerance", e.target.value)
                      }
                      SelectProps={{ native: true }}
                      sx={{
                        "& .MuiOutlinedInput-root": {
                          background: "rgba(255, 255, 255, 0.05)",
                          "& fieldset": {
                            borderColor: "rgba(255, 255, 255, 0.2)",
                          },
                          "&:hover fieldset": { borderColor: "#00d4ff" },
                          "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                        },
                        "& .MuiInputLabel-root": {
                          color: "rgba(255, 255, 255, 0.7)",
                        },
                        "& .MuiOutlinedInput-input": { color: "white" },
                      }}
                    >
                      <option value="Low">Low</option>
                      <option value="Medium">Medium</option>
                      <option value="High">High</option>
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      select
                      label="Investment Experience"
                      value={profileData.investmentExperience}
                      onChange={(e) =>
                        handleInputChange(
                          "investmentExperience",
                          e.target.value,
                        )
                      }
                      SelectProps={{ native: true }}
                      sx={{
                        "& .MuiOutlinedInput-root": {
                          background: "rgba(255, 255, 255, 0.05)",
                          "& fieldset": {
                            borderColor: "rgba(255, 255, 255, 0.2)",
                          },
                          "&:hover fieldset": { borderColor: "#00d4ff" },
                          "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                        },
                        "& .MuiInputLabel-root": {
                          color: "rgba(255, 255, 255, 0.7)",
                        },
                        "& .MuiOutlinedInput-input": { color: "white" },
                      }}
                    >
                      <option value="Beginner">Beginner</option>
                      <option value="Intermediate">Intermediate</option>
                      <option value="Advanced">Advanced</option>
                      <option value="Expert">Expert</option>
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      select
                      label="Preferred Currency"
                      value={profileData.preferredCurrency}
                      onChange={(e) =>
                        handleInputChange("preferredCurrency", e.target.value)
                      }
                      SelectProps={{ native: true }}
                      InputProps={{
                        startAdornment: (
                          <DollarSign
                            size={20}
                            color="#00d4ff"
                            style={{ marginRight: 8 }}
                          />
                        ),
                      }}
                      sx={{
                        "& .MuiOutlinedInput-root": {
                          background: "rgba(255, 255, 255, 0.05)",
                          "& fieldset": {
                            borderColor: "rgba(255, 255, 255, 0.2)",
                          },
                          "&:hover fieldset": { borderColor: "#00d4ff" },
                          "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                        },
                        "& .MuiInputLabel-root": {
                          color: "rgba(255, 255, 255, 0.7)",
                        },
                        "& .MuiOutlinedInput-input": { color: "white" },
                      }}
                    >
                      <option value="USD">USD - US Dollar</option>
                      <option value="EUR">EUR - Euro</option>
                      <option value="GBP">GBP - British Pound</option>
                      <option value="JPY">JPY - Japanese Yen</option>
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      select
                      label="Timezone"
                      value={profileData.timezone}
                      onChange={(e) =>
                        handleInputChange("timezone", e.target.value)
                      }
                      SelectProps={{ native: true }}
                      InputProps={{
                        startAdornment: (
                          <Globe
                            size={20}
                            color="#00d4ff"
                            style={{ marginRight: 8 }}
                          />
                        ),
                      }}
                      sx={{
                        "& .MuiOutlinedInput-root": {
                          background: "rgba(255, 255, 255, 0.05)",
                          "& fieldset": {
                            borderColor: "rgba(255, 255, 255, 0.2)",
                          },
                          "&:hover fieldset": { borderColor: "#00d4ff" },
                          "&.Mui-focused fieldset": { borderColor: "#00d4ff" },
                        },
                        "& .MuiInputLabel-root": {
                          color: "rgba(255, 255, 255, 0.7)",
                        },
                        "& .MuiOutlinedInput-input": { color: "white" },
                      }}
                    >
                      <option value="EST (UTC-5)">EST (UTC-5)</option>
                      <option value="PST (UTC-8)">PST (UTC-8)</option>
                      <option value="GMT (UTC+0)">GMT (UTC+0)</option>
                      <option value="CET (UTC+1)">CET (UTC+1)</option>
                    </TextField>
                  </Grid>
                </Grid>
              </Box>
            </TabPanel>
          </Paper>
        </Fade>
      </Container>
    </Box>
  );
};

export default Profile;
