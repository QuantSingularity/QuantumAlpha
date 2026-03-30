import {
  Alert,
  Avatar,
  Badge,
  Box,
  Button,
  Chip,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemSecondaryAction,
  ListItemText,
  Menu,
  Snackbar,
  Typography,
} from "@mui/material";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  Bell,
  Check,
  CheckCircle,
  Clock,
  DollarSign,
  Settings,
  TrendingUp,
  X,
} from "lucide-react";
import { useState } from "react";

const NotificationCenter = () => {
  const [anchorEl, setAnchorEl] = useState(null);
  const [notifications, setNotifications] = useState([
    {
      id: 1,
      type: "trade",
      title: "Trade Executed",
      message:
        "Your buy order for AAPL (100 shares) has been executed at $175.23",
      timestamp: new Date(Date.now() - 5 * 60 * 1000),
      read: false,
      priority: "high",
      icon: TrendingUp,
      color: "#10b981",
    },
    {
      id: 2,
      type: "alert",
      title: "Price Alert",
      message: "TSLA has reached your target price of $245.00",
      timestamp: new Date(Date.now() - 15 * 60 * 1000),
      read: false,
      priority: "medium",
      icon: AlertTriangle,
      color: "#f59e0b",
    },
    {
      id: 3,
      type: "portfolio",
      title: "Portfolio Update",
      message: "Your portfolio value increased by 2.3% today (+$2,847)",
      timestamp: new Date(Date.now() - 30 * 60 * 1000),
      read: true,
      priority: "low",
      icon: DollarSign,
      color: "#00d4ff",
    },
    {
      id: 4,
      type: "system",
      title: "System Maintenance",
      message:
        "Scheduled maintenance will occur tonight from 2:00 AM - 4:00 AM EST",
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
      read: false,
      priority: "medium",
      icon: Settings,
      color: "#8b5cf6",
    },
    {
      id: 5,
      type: "strategy",
      title: "Strategy Performance",
      message: "AI Momentum strategy achieved 15.2% return this month",
      timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
      read: true,
      priority: "low",
      icon: Activity,
      color: "#10b981",
    },
    {
      id: 6,
      type: "risk",
      title: "Risk Alert",
      message: "Portfolio risk level has increased to Medium-High",
      timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000),
      read: false,
      priority: "high",
      icon: AlertCircle,
      color: "#ef4444",
    },
  ]);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success",
  });

  const unreadCount = notifications.filter((n) => !n.read).length;

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const markAsRead = (id) => {
    setNotifications((prev) =>
      prev.map((notification) =>
        notification.id === id ? { ...notification, read: true } : notification,
      ),
    );
    setSnackbar({
      open: true,
      message: "Notification marked as read",
      severity: "success",
    });
  };

  const markAllAsRead = () => {
    setNotifications((prev) =>
      prev.map((notification) => ({ ...notification, read: true })),
    );
    setSnackbar({
      open: true,
      message: "All notifications marked as read",
      severity: "success",
    });
  };

  const deleteNotification = (id) => {
    setNotifications((prev) =>
      prev.filter((notification) => notification.id !== id),
    );
    setSnackbar({
      open: true,
      message: "Notification deleted",
      severity: "info",
    });
  };

  const formatTimestamp = (timestamp) => {
    const now = new Date();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return "Just now";
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case "high":
        return "#ef4444";
      case "medium":
        return "#f59e0b";
      case "low":
        return "#10b981";
      default:
        return "#6b7280";
    }
  };

  const NotificationItem = ({ notification }) => {
    const Icon = notification.icon;

    return (
      <ListItem
        sx={{
          background: notification.read
            ? "transparent"
            : "rgba(0, 212, 255, 0.05)",
          borderLeft: `4px solid ${notification.read ? "transparent" : notification.color}`,
          mb: 1,
          borderRadius: 2,
          transition: "all 0.3s ease",
          "&:hover": {
            background: "rgba(255, 255, 255, 0.05)",
            transform: "translateX(4px)",
          },
        }}
      >
        <ListItemIcon>
          <Avatar
            sx={{
              bgcolor: `${notification.color}20`,
              width: 40,
              height: 40,
            }}
          >
            <Icon size={20} color={notification.color} />
          </Avatar>
        </ListItemIcon>
        <ListItemText
          primary={
            <Box
              sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}
            >
              <Typography
                variant="subtitle2"
                fontWeight={notification.read ? 400 : 600}
                color="white"
              >
                {notification.title}
              </Typography>
              <Chip
                label={notification.priority}
                size="small"
                sx={{
                  bgcolor: getPriorityColor(notification.priority),
                  color: "white",
                  fontSize: "0.7rem",
                  height: 20,
                }}
              />
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
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <Clock size={12} color="#6b7280" />
                <Typography variant="caption" color="text.secondary">
                  {formatTimestamp(notification.timestamp)}
                </Typography>
              </Box>
            </Box>
          }
        />
        <ListItemSecondaryAction>
          <Box sx={{ display: "flex", gap: 1 }}>
            {!notification.read && (
              <IconButton
                size="small"
                onClick={() => markAsRead(notification.id)}
                sx={{ color: "#10b981" }}
              >
                <Check size={16} />
              </IconButton>
            )}
            <IconButton
              size="small"
              onClick={() => deleteNotification(notification.id)}
              sx={{ color: "#ef4444" }}
            >
              <X size={16} />
            </IconButton>
          </Box>
        </ListItemSecondaryAction>
      </ListItem>
    );
  };

  return (
    <>
      <IconButton
        onClick={handleClick}
        sx={{
          color: "white",
          "&:hover": {
            background: "rgba(0, 212, 255, 0.1)",
          },
        }}
      >
        <Badge
          badgeContent={unreadCount}
          color="error"
          sx={{
            "& .MuiBadge-badge": {
              background: "linear-gradient(45deg, #ef4444, #dc2626)",
              animation: unreadCount > 0 ? "pulse 2s infinite" : "none",
              "@keyframes pulse": {
                "0%": {
                  transform: "scale(1)",
                },
                "50%": {
                  transform: "scale(1.1)",
                },
                "100%": {
                  transform: "scale(1)",
                },
              },
            },
          }}
        >
          <Bell size={24} />
        </Badge>
      </IconButton>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        PaperProps={{
          sx: {
            width: 420,
            maxHeight: 600,
            background: "rgba(0, 0, 0, 0.9)",
            backdropFilter: "blur(20px)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: 3,
            boxShadow: "0 8px 32px rgba(0, 0, 0, 0.5)",
            mt: 1,
          },
        }}
        transformOrigin={{ horizontal: "right", vertical: "top" }}
        anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
      >
        {/* Header */}
        <Box sx={{ p: 3, borderBottom: "1px solid rgba(255, 255, 255, 0.1)" }}>
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              mb: 2,
            }}
          >
            <Typography variant="h6" fontWeight={700} color="white">
              Notifications
            </Typography>
            <Chip
              label={`${unreadCount} unread`}
              size="small"
              sx={{
                background:
                  unreadCount > 0
                    ? "linear-gradient(45deg, #ef4444, #dc2626)"
                    : "#6b7280",
                color: "white",
                fontWeight: 600,
              }}
            />
          </Box>
          {unreadCount > 0 && (
            <Button
              size="small"
              onClick={markAllAsRead}
              sx={{
                color: "#00d4ff",
                fontWeight: 600,
                "&:hover": {
                  background: "rgba(0, 212, 255, 0.1)",
                },
              }}
            >
              Mark all as read
            </Button>
          )}
        </Box>

        {/* Notifications List */}
        <Box sx={{ maxHeight: 400, overflow: "auto", p: 2 }}>
          {notifications.length > 0 ? (
            <List sx={{ p: 0 }}>
              {notifications.map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                />
              ))}
            </List>
          ) : (
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
        </Box>

        {/* Footer */}
        <Box sx={{ p: 2, borderTop: "1px solid rgba(255, 255, 255, 0.1)" }}>
          <Button
            fullWidth
            variant="outlined"
            sx={{
              borderColor: "#00d4ff",
              color: "#00d4ff",
              fontWeight: 600,
              "&:hover": {
                borderColor: "#00d4ff",
                background: "rgba(0, 212, 255, 0.1)",
              },
            }}
          >
            View All Notifications
          </Button>
        </Box>
      </Menu>

      {/* Snackbar for feedback */}
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
    </>
  );
};

export default NotificationCenter;
