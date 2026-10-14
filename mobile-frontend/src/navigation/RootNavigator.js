import React from "react";
import { createStackNavigator } from "@react-navigation/stack";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { createDrawerNavigator } from "@react-navigation/drawer";
import Icon from "react-native-vector-icons/MaterialCommunityIcons";

// Auth Screens
import HomeScreen from "../screens/home/HomeScreen";
import LoginScreen from "../screens/auth/LoginScreen";
import RegisterScreen from "../screens/auth/RegisterScreen";
import ForgotPasswordScreen from "../screens/auth/ForgotPasswordScreen";

// Main Screens
import DashboardScreen from "../screens/dashboard/DashboardScreen";
import PortfolioScreen from "../screens/portfolio/PortfolioScreen";
import StrategyScreen from "../screens/strategy/StrategyScreen";
import StrategyDetailScreen from "../screens/strategy/StrategyDetailScreen";
import TradeScreen from "../screens/trade/TradeScreen";
import AIInsightsScreen from "../screens/ai/AIInsightsScreen";
import AlertsScreen from "../screens/alerts/AlertsScreen";
import ProfileScreen from "../screens/profile/ProfileScreen";
import SettingsScreen from "../screens/settings/SettingsScreen";

// Other Screens
import NotificationsScreen from "../screens/notifications/NotificationsScreen";
import HelpScreen from "../screens/help/HelpScreen";

import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();
const Drawer = createDrawerNavigator();

const AuthStack = () => {
  const { theme } = useTheme();

  return (
    <Stack.Navigator
      initialRouteName="Home"
      screenOptions={{
        headerShown: false,
        cardStyle: { backgroundColor: theme.background },
      }}
    >
      <Stack.Screen name="Home" component={HomeScreen} />
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Register" component={RegisterScreen} />
      <Stack.Screen name="ForgotPassword" component={ForgotPasswordScreen} />
    </Stack.Navigator>
  );
};

const MainTabs = () => {
  const { theme, isDarkMode } = useTheme();

  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: theme.primary,
        tabBarInactiveTintColor: isDarkMode ? "#888888" : "#555555",
        tabBarStyle: {
          backgroundColor: theme.card,
          borderTopColor: theme.border,
          paddingBottom: 5,
          paddingTop: 5,
          height: 60,
        },
        headerShown: false,
      }}
    >
      <Tab.Screen
        name="DashboardTab"
        component={DashboardStack}
        options={{
          tabBarLabel: "Dashboard",
          tabBarIcon: ({ color, size }) => (
            <Icon name="view-dashboard" color={color} size={size} />
          ),
        }}
      />
      <Tab.Screen
        name="PortfolioTab"
        component={PortfolioStack}
        options={{
          tabBarLabel: "Portfolio",
          tabBarIcon: ({ color, size }) => (
            <Icon name="chart-line" color={color} size={size} />
          ),
        }}
      />
      <Tab.Screen
        name="StrategyTab"
        component={StrategyStack}
        options={{
          tabBarLabel: "Strategies",
          tabBarIcon: ({ color, size }) => (
            <Icon name="strategy" color={color} size={size} />
          ),
        }}
      />
      <Tab.Screen
        name="TradeTab"
        component={TradeStack}
        options={{
          tabBarLabel: "Trade",
          tabBarIcon: ({ color, size }) => (
            <Icon name="swap-horizontal" color={color} size={size} />
          ),
        }}
      />
      <Tab.Screen
        name="AlertsTab"
        component={AlertsStack}
        options={{
          tabBarLabel: "Alerts",
          tabBarIcon: ({ color, size }) => (
            <Icon name="bell" color={color} size={size} />
          ),
        }}
      />
    </Tab.Navigator>
  );
};

const DashboardStack = () => {
  const { theme } = useTheme();

  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: theme.card,
        },
        headerTintColor: theme.text,
        headerTitleStyle: {
          fontWeight: "bold",
        },
        cardStyle: { backgroundColor: theme.background },
      }}
    >
      <Stack.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{ title: "QuantumAlpha" }}
      />
      <Stack.Screen name="Notifications" component={NotificationsScreen} />
    </Stack.Navigator>
  );
};

const PortfolioStack = () => {
  const { theme } = useTheme();

  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: theme.card,
        },
        headerTintColor: theme.text,
        headerTitleStyle: {
          fontWeight: "bold",
        },
        cardStyle: { backgroundColor: theme.background },
      }}
    >
      <Stack.Screen name="Portfolio" component={PortfolioScreen} />
    </Stack.Navigator>
  );
};

const StrategyStack = () => {
  const { theme } = useTheme();

  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: theme.card,
        },
        headerTintColor: theme.text,
        headerTitleStyle: {
          fontWeight: "bold",
        },
        cardStyle: { backgroundColor: theme.background },
      }}
    >
      <Stack.Screen name="Strategies" component={StrategyScreen} />
      <Stack.Screen
        name="StrategyDetail"
        component={StrategyDetailScreen}
        options={({ route }) => ({
          title: route.params?.name || "Strategy Details",
        })}
      />
    </Stack.Navigator>
  );
};

const TradeStack = () => {
  const { theme } = useTheme();

  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: theme.card,
        },
        headerTintColor: theme.text,
        headerTitleStyle: {
          fontWeight: "bold",
        },
        cardStyle: { backgroundColor: theme.background },
      }}
    >
      <Stack.Screen name="Trade" component={TradeScreen} />
    </Stack.Navigator>
  );
};

const AlertsStack = () => {
  const { theme } = useTheme();

  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: theme.card,
        },
        headerTintColor: theme.text,
        headerTitleStyle: {
          fontWeight: "bold",
        },
        cardStyle: { backgroundColor: theme.background },
      }}
    >
      <Stack.Screen name="Alerts" component={AlertsScreen} />
    </Stack.Navigator>
  );
};

const DrawerNavigator = () => {
  const { theme } = useTheme();
  const { logout } = useAuth();

  return (
    <Drawer.Navigator
      screenOptions={{
        headerShown: false,
        drawerStyle: {
          backgroundColor: theme.card,
          width: 280,
        },
        drawerLabelStyle: {
          color: theme.text,
        },
        drawerActiveTintColor: theme.primary,
        drawerInactiveTintColor: theme.text,
      }}
    >
      <Drawer.Screen
        name="MainTabs"
        component={MainTabs}
        options={{
          title: "Home",
          drawerIcon: ({ color, size }) => (
            <Icon name="home" color={color} size={size} />
          ),
        }}
      />
      <Drawer.Screen
        name="AIInsightsScreen"
        component={AIInsightsScreen}
        options={{
          title: "AI Insights",
          headerShown: true,
          headerStyle: { backgroundColor: theme.card },
          headerTintColor: theme.text,
          drawerIcon: ({ color, size }) => (
            <Icon name="brain" color={color} size={size} />
          ),
        }}
      />
      <Drawer.Screen
        name="ProfileScreen"
        component={ProfileScreen}
        options={{
          title: "Profile",
          drawerIcon: ({ color, size }) => (
            <Icon name="account" color={color} size={size} />
          ),
        }}
      />
      <Drawer.Screen
        name="SettingsScreen"
        component={SettingsScreen}
        options={{
          title: "Settings",
          drawerIcon: ({ color, size }) => (
            <Icon name="cog" color={color} size={size} />
          ),
        }}
      />
      <Drawer.Screen
        name="HelpScreen"
        component={HelpScreen}
        options={{
          title: "Help & Support",
          drawerIcon: ({ color, size }) => (
            <Icon name="help-circle" color={color} size={size} />
          ),
        }}
      />
    </Drawer.Navigator>
  );
};

const RootNavigator = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    // You could return a splash screen here
    return null;
  }

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {isAuthenticated ? (
        <Stack.Screen name="Main" component={DrawerNavigator} />
      ) : (
        <Stack.Screen name="Auth" component={AuthStack} />
      )}
    </Stack.Navigator>
  );
};

export default RootNavigator;
