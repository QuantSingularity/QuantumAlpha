import {
  Alert,
  Avatar,
  Badge,
  Box,
  Fade,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Snackbar,
  Typography,
} from "@mui/material";
import {
  Activity,
  AlertTriangle,
  Bell,
  CheckCircle,
  Clock,
  DollarSign,
  Settings,
  TrendingUp,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";

const NotificationPanel = () => {
  const [notifications, setNotifications] = useState([
    {
      id: 1,
      type: "trade",
      title: "Trade Executed",
      message: "AAPL buy order completed",
      timestamp: new Date(Date.now() - 2 * 60 * 1000),
      read: false,
      icon: TrendingUp,
      color: "#10b981",
    },
    {
      id: 2,
      type: "alert",
      title: "Price Alert",
      message: "TSLA reached target price",
      timestamp: new Date(Date.now() - 10 * 60 * 1000),
      read: false,
      icon: AlertTriangle,
      color: "#f59e0b",
    },
    {
      id: 3,
      type: "portfolio",
      title: "Portfolio Update",
      message: "Daily gain: +2.3%",
      timestamp: new Date(Date.now() - 30 * 60 * 1000),
      read: true,
      icon: DollarSign,
      color: "#00d4ff",
    },
  ]);

  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success",
  });

  // Simulate real-time notifications
  useEffect(() => {
    const interval = setInterval(() => {
      const newNotification = {
        id: Date.now(),
        type: "system",
        title: "Market Update",
        message: "New trading opportunity detected",
        timestamp: new Date(),
        read: false,
        icon: Activity,
        color: "#8b5cf6",
      };

      setNotifications((prev) => [newNotification, ...prev.slice(0, 9)]);
      setSnackbar({
        open: true,
        message: "New notification received",
        severity: "info",
      });
    }, 30000); // Every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const markAsRead = (id) => {
    setNotifications((prev) =>
      prev.map((notification) =>
        notification.id === id ? { ...notification, read: true } : notification,
      ),
    );
  };

  const deleteNotification = (id) => {
    setNotifications((prev) =>
      prev.filter((notification) => notification.id !== id),
    );
  };

  const formatTimestamp = (timestamp) => {
    const now = new Date();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);

    if (minutes < 1) return "Just now";
    if (minutes < 60) return `${minutes}m ago`;
    return `${hours}h ago`;
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <Fade in={true} timeout={1000}>
      <Paper
        elevation={0}
        sx={{
          p: 3,
          borderRadius: 4,
          background: "rgba(255, 255, 255, 0.05)",
          backdropFilter: "blur(20px)",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",
          height: "100%",
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            mb: 3,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <Badge
              badgeContent={unreadCount}
              color="error"
              sx={{
                "& .MuiBadge-badge": {
                  background: "linear-gradient(45deg, #ef4444, #dc2626)",
                },
              }}
            >
              <Bell size={24} color="#00d4ff" />
            </Badge>
            <Typography variant="h6" fontWeight={700} color="white">
              Live Notifications
            </Typography>
          </Box>
          <IconButton size="small" sx={{ color: "#00d4ff" }}>
            <Settings size={20} />
          </IconButton>
        </Box>

        <List sx={{ p: 0, maxHeight: 400, overflow: "auto" }}>
          {notifications.map((notification, index) => {
            const Icon = notification.icon;

            return (
              <Fade
                in={true}
                timeout={500}
                style={{ transitionDelay: `${index * 100}ms` }}
                key={notification.id}
              >
                <ListItem
                  sx={{
                    background: notification.read
                      ? "transparent"
                      : "rgba(0, 212, 255, 0.05)",
                    borderLeft: `3px solid ${notification.read ? "transparent" : notification.color}`,
                    mb: 1,
                    borderRadius: 2,
                    transition: "all 0.3s ease",
                    cursor: "pointer",
                    "&:hover": {
                      background: "rgba(255, 255, 255, 0.05)",
                      transform: "translateX(4px)",
                    },
                  }}
                  onClick={() => markAsRead(notification.id)}
                >
                  <ListItemIcon>
                    <Avatar
                      sx={{
                        bgcolor: `${notification.color}20`,
                        width: 36,
                        height: 36,
                      }}
                    >
                      <Icon size={18} color={notification.color} />
                    </Avatar>
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                        }}
                      >
                        <Typography
                          variant="subtitle2"
                          fontWeight={notification.read ? 400 : 600}
                          color="white"
                        >
                          {notification.title}
                        </Typography>
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteNotification(notification.id);
                          }}
                          sx={{ color: "#ef4444", opacity: 0.7 }}
                        >
                          <X size={14} />
                        </IconButton>
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{ mb: 0.5 }}
                        >
                          {notification.message}
                        </Typography>
                        <Box
                          sx={{ display: "flex", alignItems: "center", gap: 1 }}
                        >
                          <Clock size={10} color="#6b7280" />
                          <Typography variant="caption" color="text.secondary">
                            {formatTimestamp(notification.timestamp)}
                          </Typography>
                        </Box>
                      </Box>
                    }
                  />
                </ListItem>
              </Fade>
            );
          })}
        </List>

        {notifications.length === 0 && (
          <Box sx={{ textAlign: "center", py: 4 }}>
            <CheckCircle
              size={48}
              color="#6b7280"
              style={{ marginBottom: 16 }}
            />
            <Typography variant="body1" color="text.secondary">
              No notifications
            </Typography>
            <Typography variant="body2" color="text.secondary">
              You're all caught up!
            </Typography>
          </Box>
        )}

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

export default NotificationPanel;
