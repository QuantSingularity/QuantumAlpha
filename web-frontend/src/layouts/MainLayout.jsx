import {
  Assessment as AssessmentIcon,
  Bookmark as BookmarkIcon,
  Dashboard as DashboardIcon,
  ExitToApp as ExitToAppIcon,
  Menu as MenuIcon,
  Newspaper as NewspaperIcon,
  Person as PersonIcon,
  Settings as SettingsIcon,
  TrendingUp as TrendingUpIcon,
} from "@mui/icons-material";
import {
  AppBar,
  Avatar,
  Box,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import { useDispatch, useSelector } from "react-redux";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import NotificationCenter from "../components/common/NotificationCenter";
import NotificationPanel from "../components/common/NotificationPanel";
import { logout } from "../store/slices/authSlice";
import { toggleDrawer } from "../store/slices/uiSlice";

const MainLayout = () => {
  const theme = useTheme();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const { drawerOpen } = useSelector((state) => state.ui);
  const { user } = useSelector((state) => state.auth);

  const handleDrawerToggle = () => {
    dispatch(toggleDrawer());
  };

  const handleNavigation = (path) => {
    navigate(path);
  };

  const handleLogout = () => {
    dispatch(logout());
    navigate("/login");
  };

  const drawerWidth = 240;

  const navItems = [
    { path: "/", label: "Dashboard", icon: DashboardIcon, exact: true },
    { path: "/strategies", label: "Strategies", icon: TrendingUpIcon },
    { path: "/analytics", label: "Analytics", icon: AssessmentIcon },
    { path: "/watchlist", label: "Watchlist", icon: BookmarkIcon },
    { path: "/news", label: "News Feed", icon: NewspaperIcon },
  ];

  const isActive = (path, exact) => {
    if (exact) return location.pathname === path;
    return location.pathname.startsWith(path);
  };

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      {/* App Bar */}
      <AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            QuantumAlpha Trading Platform
          </Typography>
          <NotificationCenter />
          <Tooltip title="Profile">
            <IconButton
              color="inherit"
              onClick={() => handleNavigation("/profile")}
            >
              <Avatar
                sx={{
                  width: 32,
                  height: 32,
                  bgcolor: "primary.main",
                  fontSize: "0.875rem",
                }}
              >
                {user?.firstName?.[0] || user?.email?.[0]?.toUpperCase() || "U"}
              </Avatar>
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      {/* Side Drawer */}
      <Drawer
        variant="persistent"
        anchor="left"
        open={drawerOpen}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: drawerWidth,
            boxSizing: "border-box",
            backgroundColor: "background.paper",
          },
        }}
      >
        <Toolbar />
        <Box
          sx={{
            overflow: "auto",
            mt: 2,
            display: "flex",
            flexDirection: "column",
            height: "100%",
          }}
        >
          <List>
            {navItems.map(({ path, label, icon: Icon, exact }) => (
              <ListItemButton
                key={path}
                onClick={() => handleNavigation(path)}
                selected={isActive(path, exact)}
                sx={{
                  borderRadius: 2,
                  mx: 1,
                  mb: 0.5,
                  "&.Mui-selected": {
                    background:
                      "linear-gradient(45deg, rgba(0,212,255,0.15), rgba(0,153,204,0.1))",
                    borderLeft: "3px solid #00d4ff",
                    "& .MuiListItemIcon-root": { color: "primary.main" },
                  },
                }}
              >
                <ListItemIcon>
                  <Icon />
                </ListItemIcon>
                <ListItemText primary={label} />
              </ListItemButton>
            ))}
          </List>
          <Divider sx={{ my: 1 }} />
          <List>
            <ListItemButton
              onClick={() => handleNavigation("/settings")}
              selected={isActive("/settings", true)}
              sx={{
                borderRadius: 2,
                mx: 1,
                mb: 0.5,
                "&.Mui-selected": {
                  background:
                    "linear-gradient(45deg, rgba(0,212,255,0.15), rgba(0,153,204,0.1))",
                  borderLeft: "3px solid #00d4ff",
                  "& .MuiListItemIcon-root": { color: "primary.main" },
                },
              }}
            >
              <ListItemIcon>
                <SettingsIcon />
              </ListItemIcon>
              <ListItemText primary="Settings" />
            </ListItemButton>
            <ListItemButton
              onClick={() => handleNavigation("/profile")}
              selected={isActive("/profile", true)}
              sx={{
                borderRadius: 2,
                mx: 1,
                mb: 0.5,
                "&.Mui-selected": {
                  background:
                    "linear-gradient(45deg, rgba(0,212,255,0.15), rgba(0,153,204,0.1))",
                  borderLeft: "3px solid #00d4ff",
                  "& .MuiListItemIcon-root": { color: "primary.main" },
                },
              }}
            >
              <ListItemIcon>
                <PersonIcon />
              </ListItemIcon>
              <ListItemText primary="Profile" />
            </ListItemButton>
            <ListItemButton
              onClick={handleLogout}
              sx={{ borderRadius: 2, mx: 1, mb: 0.5, color: "error.main" }}
            >
              <ListItemIcon sx={{ color: "error.main" }}>
                <ExitToAppIcon />
              </ListItemIcon>
              <ListItemText primary="Logout" />
            </ListItemButton>
          </List>
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          backgroundColor: "background.default",
          marginLeft: drawerOpen ? `${drawerWidth}px` : 0,
          transition: theme.transitions.create("margin", {
            easing: drawerOpen
              ? theme.transitions.easing.easeOut
              : theme.transitions.easing.sharp,
            duration: drawerOpen
              ? theme.transitions.duration.enteringScreen
              : theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>

      {/* Notification Panel */}
      <NotificationPanel />
    </Box>
  );
};

export default MainLayout;
