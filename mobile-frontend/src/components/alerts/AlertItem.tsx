import React from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
} from "react-native";
import Icon from "react-native-vector-icons/MaterialCommunityIcons";
import { useTheme } from "../../context/ThemeContext";

// AlertItem accepts the shape returned by alertService (read/timestamp)
// as well as the full Alert type (isRead/createdAt) for flexibility
interface AlertItemData {
  id: string;
  type: string;
  title: string;
  message: string;
  priority?: string;
  // service returns "read" and "timestamp"; types use "isRead" and "createdAt"
  read?: boolean;
  isRead?: boolean;
  timestamp?: string;
  createdAt?: string;
}

interface AlertItemProps {
  alert: AlertItemData;
  onPress?: () => void;
  onDismiss?: (id: string) => void;
}

const AlertItem: React.FC<AlertItemProps> = ({ alert, onPress, onDismiss }) => {
  const { theme } = useTheme();
  const [dismissed, setDismissed] = React.useState(false);
  const slideAnim = React.useRef(new Animated.Value(0)).current;
  const opacityAnim = React.useRef(new Animated.Value(1)).current;

  // Support both field naming conventions
  const isRead = alert.isRead ?? alert.read ?? false;
  const timestamp = alert.createdAt ?? alert.timestamp;

  const getAlertIcon = (type: string) => {
    switch (type?.toUpperCase()) {
      case "TRADE_SIGNAL":
      case "TRADE":
        return "swap-horizontal";
      case "RISK_WARNING":
      case "WARNING":
        return "alert";
      case "MARKET_UPDATE":
        return "chart-line";
      case "TRADE_EXECUTED":
        return "check-circle";
      case "SYSTEM_UPDATE":
      case "SYSTEM":
        return "cog";
      case "PERFORMANCE_UPDATE":
        return "trending-up";
      case "PRICE":
        return "chart-line";
      case "NEWS":
        return "newspaper";
      case "ERROR":
        return "alert-circle";
      default:
        return "bell";
    }
  };

  const getAlertColor = (priority?: string) => {
    switch (priority?.toLowerCase()) {
      case "critical":
      case "high":
        return theme.error;
      case "medium":
        return theme.warning;
      case "low":
        return theme.success;
      default:
        return theme.primary;
    }
  };

  const handleDismiss = () => {
    if (onDismiss && alert.id) {
      Animated.parallel([
        Animated.timing(slideAnim, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }),
        Animated.timing(opacityAnim, {
          toValue: 0,
          duration: 300,
          useNativeDriver: true,
        }),
      ]).start(() => {
        setDismissed(true);
        onDismiss(alert.id);
      });
    }
  };

  if (dismissed) return null;

  const alertColor = getAlertColor(alert.priority);
  const slideTranslate = slideAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0, 300],
  });

  return (
    <Animated.View
      style={[
        styles.container,
        {
          backgroundColor: theme.card,
          borderLeftColor: alertColor,
          opacity: opacityAnim,
          transform: [{ translateX: slideTranslate }],
        },
      ]}
    >
      <TouchableOpacity
        style={styles.content}
        onPress={onPress}
        activeOpacity={0.7}
      >
        <View
          style={[styles.iconContainer, { backgroundColor: alertColor + "20" }]}
        >
          <Icon name={getAlertIcon(alert.type)} size={24} color={alertColor} />
        </View>

        <View style={styles.textContainer}>
          <View style={styles.titleRow}>
            <Text
              style={[
                styles.title,
                {
                  color: theme.text,
                  fontWeight: isRead ? "400" : "600",
                },
              ]}
              numberOfLines={1}
            >
              {alert.title}
            </Text>
            {!isRead && (
              <View
                style={[styles.unreadDot, { backgroundColor: theme.primary }]}
              />
            )}
          </View>
          <Text
            style={[styles.message, { color: theme.textSecondary }]}
            numberOfLines={2}
          >
            {alert.message}
          </Text>
          {timestamp && (
            <Text style={[styles.timestamp, { color: theme.text + "80" }]}>
              {new Date(timestamp).toLocaleString()}
            </Text>
          )}
        </View>

        {onDismiss && (
          <TouchableOpacity
            testID="dismiss-button"
            style={styles.dismissButton}
            onPress={handleDismiss}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Icon name="close" size={20} color={theme.text + "99"} />
          </TouchableOpacity>
        )}
      </TouchableOpacity>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
    marginVertical: 6,
    borderRadius: 12,
    borderLeftWidth: 4,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 3,
  },
  content: {
    flexDirection: "row",
    alignItems: "center",
    padding: 14,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },
  textContainer: {
    flex: 1,
    marginRight: 8,
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 3,
  },
  title: {
    fontSize: 15,
    flex: 1,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginLeft: 6,
  },
  message: {
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 4,
  },
  timestamp: {
    fontSize: 11,
    marginTop: 2,
  },
  dismissButton: {
    padding: 4,
  },
});

export default AlertItem;
