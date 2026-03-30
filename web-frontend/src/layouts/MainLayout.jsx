import {
  AccountCircle as AccountCircleIcon,
  Assessment as AssessmentIcon,
  Dashboard as DashboardIcon,
  ExitToApp as ExitToAppIcon,
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  TrendingUp as TrendingUpIcon,
} from "@mui/icons-material";
import {
  AppBar,
  Box,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  useTheme,
} from "@mui/material";
import { useDispatch, useSelector } from "react-redux";
import { Outlet, useNavigate } from "react-router-dom";
import NotificationPanel from "../components/common/NotificationPanel";
import { toggleDrawer } from "../store/slices/uiSlice";

const MainLayout = () => {
  const theme = useTheme();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { drawerOpen } = useSelector((state) => state.ui);

  const handleDrawerToggle = () => {
    dispatch(toggleDrawer());
  };

  const handleNavigation = (path) => {
    navigate(path);
  };

  const drawerWidth = 240;

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}
      >
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
          <IconButton color="inherit">
            <NotificationsIcon />
          </IconButton>
          <IconButton color="inherit">
            <AccountCircleIcon />
          </IconButton>
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
        <Box sx={{ overflow: "auto", mt: 2 }}>
          <List>
            <ListItem button onClick={() => handleNavigation("/")}>
              <ListItemIcon>
                <DashboardIcon
                  color={location.pathname === "/" ? "primary" : "inherit"}
                />
              </ListItemIcon>
              <ListItemText primary="Dashboard" />
            </ListItem>
            <ListItem button onClick={() => handleNavigation("/strategies")}>
              <ListItemIcon>
                <TrendingUpIcon
                  color={
                    location.pathname.includes("/strategies")
                      ? "primary"
                      : "inherit"
                  }
                />
              </ListItemIcon>
              <ListItemText primary="Strategies" />
            </ListItem>
            <ListItem button onClick={() => handleNavigation("/analytics")}>
              <ListItemIcon>
                <AssessmentIcon
                  color={
                    location.pathname === "/analytics" ? "primary" : "inherit"
                  }
                />
              </ListItemIcon>
              <ListItemText primary="Analytics" />
            </ListItem>
          </List>
          <Divider />
          <List>
            <ListItem button onClick={() => handleNavigation("/settings")}>
              <ListItemIcon>
                <SettingsIcon
                  color={
                    location.pathname === "/settings" ? "primary" : "inherit"
                  }
                />
              </ListItemIcon>
              <ListItemText primary="Settings" />
            </ListItem>
            <ListItem button>
              <ListItemIcon>
                <ExitToAppIcon />
              </ListItemIcon>
              <ListItemText primary="Logout" />
            </ListItem>
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
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
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
