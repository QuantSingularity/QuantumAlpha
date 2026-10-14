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
  Stack,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
} from "@mui/material";
import {
  BarChart3,
  Bell,
  Bookmark,
  Brain,
  CandlestickChart,
  LayoutDashboard,
  LogOut,
  Menu as MenuIcon,
  Newspaper,
  Settings,
  TrendingUp,
} from "lucide-react";
import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { Logo, Wordmark } from "../components/common/Brand";
import { palette } from "../theme/tokens";
import { logout } from "../store/slices/authSlice";
import { setDrawerOpen } from "../store/slices/uiSlice";

const DRAWER_WIDTH = 248;

const navItems = [
  {
    path: "/dashboard",
    label: "Dashboard",
    icon: LayoutDashboard,
    exact: true,
  },
  { path: "/strategies", label: "Strategies", icon: TrendingUp },
  { path: "/ai-insights", label: "AI Insights", icon: Brain },
  { path: "/trading", label: "Trading", icon: CandlestickChart },
  { path: "/analytics", label: "Analytics", icon: BarChart3 },
  { path: "/watchlist", label: "Watchlist", icon: Bookmark },
  { path: "/news", label: "News", icon: Newspaper },
];

const secondaryItems = [
  { path: "/settings", label: "Settings", icon: Settings },
];

const MainLayout = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const isDesktop = useMediaQuery("(min-width:900px)");
  const { drawerOpen } = useSelector((state) => state.ui);
  const { user } = useSelector((state) => state.auth);

  // Open the rail by default on desktop, closed on mobile.
  useEffect(() => {
    dispatch(setDrawerOpen(isDesktop));
  }, [isDesktop, dispatch]);

  const go = (path) => {
    navigate(path);
    if (!isDesktop) dispatch(setDrawerOpen(false));
  };

  const handleLogout = () => {
    dispatch(logout());
    navigate("/login");
  };

  const isActive = (path, exact) =>
    exact ? location.pathname === path : location.pathname.startsWith(path);

  const navButton = ({ path, label, icon: Icon, exact }) => {
    const active = isActive(path, exact);
    return (
      <ListItemButton
        key={path}
        onClick={() => go(path)}
        sx={{
          borderRadius: 2,
          mx: 1.25,
          mb: 0.5,
          py: 1,
          color: active ? palette.text : palette.textDim,
          background: active ? "rgba(34,211,238,0.10)" : "transparent",
          position: "relative",
          "&::before": active
            ? {
                content: '""',
                position: "absolute",
                left: 0,
                top: "20%",
                bottom: "20%",
                width: 3,
                borderRadius: 4,
                background: palette.cyan,
              }
            : {},
          "&:hover": {
            background: "rgba(148,163,184,0.08)",
            color: palette.text,
          },
        }}
      >
        <ListItemIcon
          sx={{ minWidth: 38, color: active ? palette.cyan : "inherit" }}
        >
          <Icon size={19} />
        </ListItemIcon>
        <ListItemText
          primary={label}
          primaryTypographyProps={{
            fontSize: "0.9rem",
            fontWeight: active ? 600 : 500,
          }}
        />
      </ListItemButton>
    );
  };

  const drawerContent = (
    <Box sx={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <Box sx={{ px: 2.5, py: 2.5 }}>
        <Wordmark size={28} />
      </Box>
      <Divider sx={{ borderColor: palette.border }} />
      <List sx={{ pt: 1.5, flexGrow: 1 }}>{navItems.map(navButton)}</List>
      <Divider sx={{ borderColor: palette.border }} />
      <List sx={{ py: 1 }}>
        {secondaryItems.map(navButton)}
        <ListItemButton
          onClick={handleLogout}
          sx={{
            borderRadius: 2,
            mx: 1.25,
            py: 1,
            color: palette.rose,
            "&:hover": { background: "rgba(251,113,133,0.1)" },
          }}
        >
          <ListItemIcon sx={{ minWidth: 38, color: palette.rose }}>
            <LogOut size={19} />
          </ListItemIcon>
          <ListItemText
            primary="Log out"
            primaryTypographyProps={{ fontSize: "0.9rem", fontWeight: 500 }}
          />
        </ListItemButton>
      </List>
    </Box>
  );

  const currentLabel =
    [...navItems, ...secondaryItems].find((n) => isActive(n.path, n.exact))
      ?.label || "QuantumAlpha";

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <AppBar
        position="fixed"
        sx={{
          width: { md: drawerOpen ? `calc(100% - ${DRAWER_WIDTH}px)` : "100%" },
          ml: { md: drawerOpen ? `${DRAWER_WIDTH}px` : 0 },
          transition: "width .25s ease, margin .25s ease",
        }}
      >
        <Toolbar sx={{ gap: 1 }}>
          <IconButton
            color="inherit"
            edge="start"
            onClick={() => dispatch(setDrawerOpen(!drawerOpen))}
          >
            <MenuIcon size={20} />
          </IconButton>
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 700 }}>
            {currentLabel}
          </Typography>
          <Tooltip title="Notifications">
            <IconButton color="inherit">
              <Bell size={19} />
            </IconButton>
          </Tooltip>
          <Tooltip title="Profile">
            <IconButton onClick={() => navigate("/profile")} sx={{ p: 0.5 }}>
              <Avatar
                sx={{
                  width: 32,
                  height: 32,
                  background: "linear-gradient(135deg,#22D3EE,#8B5CF6)",
                  color: "#060A14",
                  fontSize: "0.85rem",
                  fontWeight: 700,
                }}
              >
                {user?.firstName?.[0] ||
                  user?.name?.[0] ||
                  user?.email?.[0]?.toUpperCase() ||
                  "U"}
              </Avatar>
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      <Drawer
        variant={isDesktop ? "persistent" : "temporary"}
        open={drawerOpen}
        onClose={() => dispatch(setDrawerOpen(false))}
        sx={{
          width: drawerOpen ? DRAWER_WIDTH : 0,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: DRAWER_WIDTH,
            boxSizing: "border-box",
          },
        }}
      >
        {drawerContent}
      </Drawer>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, md: 4 },
          width: { md: drawerOpen ? `calc(100% - ${DRAWER_WIDTH}px)` : "100%" },
          transition: "width .25s ease",
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
};

export default MainLayout;
