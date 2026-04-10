import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Animated,
  TextInput,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import Icon from "react-native-vector-icons/MaterialCommunityIcons";
import { useTheme } from "../../context/ThemeContext";
import { useAlert } from "../../context/AlertContext";
import { alertService } from "../../services/alertService";

// Extracted to its own component so hooks are called at component level (not inside renderItem)
const AlertListItem = React.memo(
  ({ item, index, theme, onMarkAsRead, onDelete }) => {
    const itemFadeAnim = useRef(new Animated.Value(0)).current;
    const itemTranslateX = useRef(new Animated.Value(-50)).current;

    useEffect(() => {
      Animated.parallel([
        Animated.timing(itemFadeAnim, {
          toValue: 1,
          duration: 500,
          delay: Math.min(index * 50, 400),
          useNativeDriver: true,
        }),
        Animated.timing(itemTranslateX, {
          toValue: 0,
          duration: 500,
          delay: Math.min(index * 50, 400),
          useNativeDriver: true,
        }),
      ]).start();
    }, []);

    const getPriorityColor = () => {
      switch (item.priority) {
        case "high":
        case "critical":
          return theme.error;
        case "medium":
          return theme.warning;
        case "low":
        default:
          return theme.info;
      }
    };

    const getTypeIcon = () => {
      switch (item.type) {
        case "TRADE_SIGNAL":
          return "signal";
        case "RISK_WARNING":
          return "alert";
        case "MARKET_UPDATE":
          return "chart-line";
        case "TRADE_EXECUTED":
          return "check-circle";
        case "SYSTEM_UPDATE":
          return "cog";
        case "PERFORMANCE_UPDATE":
          return "trending-up";
        default:
          return "bell";
      }
    };

    const priorityColor = getPriorityColor();

    return (
      <Animated.View
        style={[
          styles.alertItemContainer,
          {
            opacity: itemFadeAnim,
            transform: [{ translateX: itemTranslateX }],
          },
        ]}
      >
        <TouchableOpacity
          style={[
            styles.alertItem,
            {
              backgroundColor: theme.card,
              opacity: item.read ? 0.75 : 1,
            },
          ]}
          onPress={() => {
            if (!item.read) {
              onMarkAsRead(item.id);
            }
          }}
          activeOpacity={0.8}
        >
          <View
            style={[
              styles.priorityIndicator,
              { backgroundColor: priorityColor },
            ]}
          />

          <View style={styles.alertIconContainer}>
            <View
              style={[
                styles.alertIcon,
                { backgroundColor: priorityColor + "20" },
              ]}
            >
              <Icon name={getTypeIcon()} size={20} color={priorityColor} />
            </View>
          </View>

          <View style={styles.alertContent}>
            <View style={styles.alertHeader}>
              <Text
                style={[
                  styles.alertTitle,
                  {
                    color: theme.text,
                    fontWeight: item.read ? "normal" : "bold",
                  },
                ]}
                numberOfLines={1}
              >
                {item.title}
              </Text>
              {!item.read && (
                <View
                  style={[styles.unreadDot, { backgroundColor: theme.primary }]}
                />
              )}
            </View>

            <Text
              style={[styles.alertMessage, { color: theme.text + "CC" }]}
              numberOfLines={2}
            >
              {item.message}
            </Text>

            <View style={styles.alertFooter}>
              <Text style={[styles.alertTime, { color: theme.text + "99" }]}>
                {new Date(item.timestamp).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
                {" · "}
                {new Date(item.timestamp).toLocaleDateString()}
              </Text>

              <TouchableOpacity
                style={styles.deleteButton}
                onPress={() => onDelete(item.id)}
                hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
              >
                <Icon
                  name="delete-outline"
                  size={18}
                  color={theme.text + "99"}
                />
              </TouchableOpacity>
            </View>
          </View>
        </TouchableOpacity>
      </Animated.View>
    );
  },
);

const AlertsScreen = () => {
  const navigation = useNavigation();
  const { theme } = useTheme();
  const { markAllAsRead } = useAlert();

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [filteredAlerts, setFilteredAlerts] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");

  const fadeAnim = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(50)).current;

  useEffect(() => {
    loadAlerts();

    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(translateY, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start();

    // Only subscribe to real-time alerts — do NOT also run a setInterval that
    // calls simulateNewAlert(), because that already notifies subscribers,
    // which would cause every alert to be added twice.
    const alertListener = alertService.subscribeToAlerts((newAlert) => {
      setAlerts((prev) => [newAlert, ...prev]);
    });

    return () => {
      alertListener.unsubscribe();
    };
  }, []);

  useEffect(() => {
    filterAlerts();
  }, [alerts, searchQuery, activeFilter]);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const response = await alertService.getAllAlerts();
      setAlerts(response.alerts);
    } catch (error) {
      console.error("Error loading alerts:", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadAlerts();
  };

  const filterAlerts = () => {
    let filtered = [...alerts];

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (alert) =>
          alert.title.toLowerCase().includes(q) ||
          alert.message.toLowerCase().includes(q),
      );
    }

    if (activeFilter !== "all") {
      filtered = filtered.filter((alert) => alert.type === activeFilter);
    }

    setFilteredAlerts(filtered);
  };

  const handleMarkAsRead = useCallback(async (alertId) => {
    try {
      await alertService.markAsRead(alertId);
      setAlerts((prev) =>
        prev.map((alert) =>
          alert.id === alertId ? { ...alert, read: true } : alert,
        ),
      );
    } catch (error) {
      console.error("Error marking alert as read:", error);
    }
  }, []);

  const handleMarkAllAsRead = async () => {
    try {
      await alertService.markAllAsRead();
      setAlerts((prev) => prev.map((alert) => ({ ...alert, read: true })));
      markAllAsRead();
    } catch (error) {
      console.error("Error marking all alerts as read:", error);
    }
  };

  const handleDeleteAlert = useCallback(async (alertId) => {
    try {
      await alertService.deleteAlert(alertId);
      setAlerts((prev) => prev.filter((alert) => alert.id !== alertId));
    } catch (error) {
      console.error("Error deleting alert:", error);
    }
  }, []);

  const renderAlertItem = useCallback(
    ({ item, index }) => (
      <AlertListItem
        item={item}
        index={index}
        theme={theme}
        onMarkAsRead={handleMarkAsRead}
        onDelete={handleDeleteAlert}
      />
    ),
    [theme, handleMarkAsRead, handleDeleteAlert],
  );

  const renderFilterButton = (filter, label, iconName) => {
    const isActive = activeFilter === filter;

    return (
      <TouchableOpacity
        key={filter}
        style={[
          styles.filterButton,
          {
            backgroundColor: isActive ? theme.primary : theme.card,
            borderColor: isActive ? theme.primary : theme.border,
          },
        ]}
        onPress={() => setActiveFilter(filter)}
      >
        <Icon
          name={iconName}
          size={14}
          color={isActive ? "#FFFFFF" : theme.text}
        />
        <Text
          style={[
            styles.filterButtonText,
            { color: isActive ? "#FFFFFF" : theme.text },
          ]}
        >
          {label}
        </Text>
      </TouchableOpacity>
    );
  };

  if (loading && !refreshing) {
    return (
      <View
        style={[styles.loadingContainer, { backgroundColor: theme.background }]}
      >
        <ActivityIndicator size="large" color={theme.primary} />
        <Text style={[styles.loadingText, { color: theme.text }]}>
          Loading alerts...
        </Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <Animated.View
        style={[
          styles.header,
          {
            backgroundColor: theme.card,
            opacity: fadeAnim,
            transform: [{ translateY }],
          },
        ]}
      >
        <View
          style={[
            styles.searchContainer,
            { backgroundColor: theme.background },
          ]}
        >
          <Icon name="magnify" size={20} color={theme.text + "99"} />
          <TextInput
            style={[styles.searchInput, { color: theme.text }]}
            placeholder="Search alerts..."
            placeholderTextColor={theme.text + "99"}
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
          {searchQuery ? (
            <TouchableOpacity onPress={() => setSearchQuery("")}>
              <Icon name="close" size={20} color={theme.text + "99"} />
            </TouchableOpacity>
          ) : null}
        </View>

        <View style={styles.filterContainer}>
          {renderFilterButton("all", "All", "bell")}
          {renderFilterButton("TRADE_SIGNAL", "Signals", "signal")}
          {renderFilterButton("RISK_WARNING", "Warnings", "alert")}
          {renderFilterButton("MARKET_UPDATE", "Market", "chart-line")}
          {renderFilterButton("TRADE_EXECUTED", "Trades", "check-circle")}
        </View>
      </Animated.View>

      <View style={styles.listContainer}>
        <View style={styles.listHeader}>
          <Text style={[styles.listTitle, { color: theme.text }]}>
            {filteredAlerts.length}{" "}
            {filteredAlerts.length === 1 ? "Alert" : "Alerts"}
          </Text>

          <TouchableOpacity
            style={styles.markAllButton}
            onPress={handleMarkAllAsRead}
          >
            <Icon name="check-all" size={18} color={theme.primary} />
            <Text style={[styles.markAllText, { color: theme.primary }]}>
              Mark all as read
            </Text>
          </TouchableOpacity>
        </View>

        <FlatList
          data={filteredAlerts}
          renderItem={renderAlertItem}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={theme.primary}
              colors={[theme.primary]}
            />
          }
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Icon name="bell-off" size={60} color={theme.text + "60"} />
              <Text style={[styles.emptyText, { color: theme.text }]}>
                No alerts found
              </Text>
              <Text style={[styles.emptySubtext, { color: theme.text + "99" }]}>
                {searchQuery || activeFilter !== "all"
                  ? "Try changing your filters"
                  : "New alerts will appear here"}
              </Text>
            </View>
          }
          removeClippedSubviews={true}
          maxToRenderPerBatch={10}
          windowSize={10}
          initialNumToRender={8}
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  loadingContainer: { flex: 1, justifyContent: "center", alignItems: "center" },
  loadingText: { marginTop: 10, fontSize: 16 },
  header: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(0,0,0,0.1)",
  },
  searchContainer: {
    flexDirection: "row",
    alignItems: "center",
    borderRadius: 10,
    paddingHorizontal: 12,
    height: 42,
  },
  searchInput: { flex: 1, marginLeft: 8, fontSize: 16 },
  filterContainer: { flexDirection: "row", marginTop: 12, flexWrap: "wrap" },
  filterButton: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
    marginBottom: 6,
    borderWidth: 1,
  },
  filterButtonText: { fontSize: 12, fontWeight: "500", marginLeft: 4 },
  listContainer: { flex: 1 },
  listHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  listTitle: { fontSize: 16, fontWeight: "500" },
  markAllButton: { flexDirection: "row", alignItems: "center" },
  markAllText: { fontSize: 14, marginLeft: 4 },
  listContent: { padding: 16, paddingTop: 0 },
  alertItemContainer: { marginBottom: 12 },
  alertItem: {
    borderRadius: 12,
    overflow: "hidden",
    flexDirection: "row",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  priorityIndicator: { width: 4, height: "100%" },
  alertIconContainer: {
    padding: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  alertIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  alertContent: { flex: 1, padding: 12, paddingLeft: 8 },
  alertHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  alertTitle: { fontSize: 15, flex: 1 },
  unreadDot: { width: 8, height: 8, borderRadius: 4, marginLeft: 8 },
  alertMessage: { fontSize: 13, marginTop: 4, lineHeight: 18 },
  alertFooter: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 8,
  },
  alertTime: { fontSize: 11 },
  deleteButton: { padding: 4 },
  emptyContainer: {
    alignItems: "center",
    justifyContent: "center",
    padding: 40,
  },
  emptyText: { fontSize: 18, fontWeight: "bold", marginTop: 16 },
  emptySubtext: { fontSize: 14, marginTop: 8, textAlign: "center" },
});

export default AlertsScreen;
