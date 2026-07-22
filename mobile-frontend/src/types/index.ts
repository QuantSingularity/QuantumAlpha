// User Types
export interface User {
  id: string;
  email: string;
  username: string;
  firstName: string;
  lastName: string;
  avatar?: string;
  phone?: string;
  dateOfBirth?: string;
  country?: string;
  timezone?: string;
  language: string;
  currency: string;
  isVerified: boolean;
  twoFactorEnabled: boolean;
  biometricEnabled: boolean;
  createdAt: string;
  updatedAt: string;
  lastLoginAt?: string;
  preferences: UserPreferences;
  subscription: Subscription;
}

export interface UserPreferences {
  theme: "light" | "dark" | "auto";
  notifications: NotificationSettings;
  trading: TradingPreferences;
  privacy: PrivacySettings;
}

export interface NotificationSettings {
  pushEnabled: boolean;
  emailEnabled: boolean;
  smsEnabled: boolean;
  priceAlerts: boolean;
  tradeExecutions: boolean;
  portfolioUpdates: boolean;
  newsUpdates: boolean;
  marketHours: boolean;
}

export interface TradingPreferences {
  defaultOrderType: OrderType;
  defaultTimeInForce: TimeInForce;
  confirmationRequired: boolean;
  riskWarnings: boolean;
  advancedFeatures: boolean;
}

export interface PrivacySettings {
  profileVisibility: "public" | "private" | "friends";
  tradingActivityVisible: boolean;
  portfolioVisible: boolean;
  analyticsEnabled: boolean;
}

export interface Subscription {
  plan: "free" | "basic" | "premium" | "professional";
  status: "active" | "inactive" | "cancelled" | "expired";
  startDate: string;
  endDate?: string;
  features: string[];
}

// Authentication Types
export interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegisterData {
  email: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
  username: string;
  agreeToTerms: boolean;
}

// Portfolio Types
export interface Portfolio {
  id: string;
  userId: string;
  name: string;
  totalValue: number;
  dailyChange: number;
  dailyChangePercent: number;
  totalReturn: number;
  totalReturnPercent: number;
  cash: number;
  positions: Position[];
  performance: PerformanceData[];
  riskMetrics: RiskMetrics;
  createdAt: string;
  updatedAt: string;
}

export interface Position {
  id: string;
  symbol: string;
  name: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  marketValue: number;
  unrealizedPnL: number;
  unrealizedPnLPercent: number;
  realizedPnL: number;
  dayChange: number;
  dayChangePercent: number;
  weight: number;
  sector?: string;
  assetType: AssetType;
  openDate: string;
}

export interface PerformanceData {
  date: string;
  value: number;
  return: number;
  returnPercent: number;
  benchmark?: number;
  benchmarkReturn?: number;
}

export interface RiskMetrics {
  sharpeRatio: number;
  volatility: number;
  maxDrawdown: number;
  beta: number;
  alpha: number;
  var95: number; // Value at Risk 95%
  expectedShortfall: number;
}

// Trading Types
export type OrderType = "market" | "limit" | "stop" | "stop_limit";
export type OrderSide = "buy" | "sell";
export type TimeInForce = "GTC" | "IOC" | "FOK" | "DAY";
export type OrderStatus =
  "pending" | "filled" | "partially_filled" | "cancelled" | "rejected";
export type AssetType =
  "stock" | "crypto" | "forex" | "commodity" | "index" | "etf";

export interface Order {
  id: string;
  userId: string;
  symbol: string;
  side: OrderSide;
  type: OrderType;
  quantity: number;
  price?: number;
  stopPrice?: number;
  timeInForce: TimeInForce;
  status: OrderStatus;
  filledQuantity: number;
  averageFillPrice: number;
  commission: number;
  createdAt: string;
  updatedAt: string;
  executedAt?: string;
}

export interface Trade {
  id: string;
  orderId: string;
  symbol: string;
  side: OrderSide;
  quantity: number;
  price: number;
  commission: number;
  executedAt: string;
}

// Market Data Types
export interface Asset {
  symbol: string;
  name: string;
  type: AssetType;
  exchange: string;
  currency: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap?: number;
  high52Week?: number;
  low52Week?: number;
  dividendYield?: number;
  peRatio?: number;
  sector?: string;
  industry?: string;
  description?: string;
  logo?: string;
  website?: string;
  isActive: boolean;
  isTradable: boolean;
}

export interface Quote {
  symbol: string;
  price: number;
  bid: number;
  ask: number;
  bidSize: number;
  askSize: number;
  spread: number;
  timestamp: string;
}

export interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketData {
  symbol: string;
  quote: Quote;
  candles: Candle[];
  indicators?: TechnicalIndicators;
}

export interface TechnicalIndicators {
  sma20?: number;
  sma50?: number;
  sma200?: number;
  ema12?: number;
  ema26?: number;
  rsi?: number;
  macd?: {
    macd: number;
    signal: number;
    histogram: number;
  };
  bollinger?: {
    upper: number;
    middle: number;
    lower: number;
  };
}

// Strategy Types
export interface Strategy {
  id: string;
  name: string;
  description: string;
  type: "algorithmic" | "manual" | "copy_trading";
  status: "active" | "inactive" | "paused";
  performance: StrategyPerformance;
  parameters: StrategyParameters;
  assets: string[];
  riskLevel: "low" | "medium" | "high";
  minInvestment: number;
  maxInvestment?: number;
  fees: StrategyFees;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  followers?: number;
  rating?: number;
  tags: string[];
}

export interface StrategyPerformance {
  totalReturn: number;
  totalReturnPercent: number;
  annualizedReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  profitFactor: number;
  trades: number;
  avgTradeDuration: number;
  history: PerformanceData[];
}

export interface StrategyParameters {
  [key: string]: any;
}

export interface StrategyFees {
  managementFee: number; // Annual percentage
  performanceFee: number; // Percentage of profits
  entryFee?: number;
  exitFee?: number;
}

// Alert Types
export interface Alert {
  id: string;
  userId: string;
  type: AlertType;
  title: string;
  message: string;
  symbol?: string;
  condition?: AlertCondition;
  isRead: boolean;
  isActive: boolean;
  priority: "low" | "medium" | "high" | "critical";
  createdAt: string;
  triggeredAt?: string;
  expiresAt?: string;
}

export type AlertType =
  | "price_alert"
  | "trade_executed"
  | "strategy_update"
  | "portfolio_update"
  | "news_update"
  | "system_maintenance"
  | "security_alert"
  | "promotion";

export interface AlertCondition {
  operator: "above" | "below" | "crosses_above" | "crosses_below" | "equals";
  value: number;
  indicator?: string;
}

// News Types
export interface NewsArticle {
  id: string;
  title: string;
  summary: string;
  content: string;
  author: string;
  source: string;
  url: string;
  imageUrl?: string;
  publishedAt: string;
  category: string;
  tags: string[];
  sentiment?: "positive" | "negative" | "neutral";
  relevantSymbols: string[];
  isBookmarked?: boolean;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  errors?: string[];
  pagination?: PaginationInfo;
}

export interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface ApiError {
  code: string;
  message: string;
  details?: any;
}

// Navigation Types
export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
};

export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  ForgotPassword: undefined;
  VerifyEmail: { email: string };
  ResetPassword: { token: string };
};

export type MainTabParamList = {
  DashboardTab: undefined;
  PortfolioTab: undefined;
  StrategyTab: undefined;
  TradeTab: undefined;
  AlertsTab: undefined;
};

export type DashboardStackParamList = {
  Dashboard: undefined;
  Notifications: undefined;
  MarketOverview: undefined;
  AssetDetail: { symbol: string };
};

export type PortfolioStackParamList = {
  Portfolio: undefined;
  TransactionHistory: undefined;
  RiskAnalysis: undefined;
};

export type StrategyStackParamList = {
  Strategies: undefined;
  StrategyDetail: { id: string; name?: string };
  CreateStrategy: undefined;
};

export type TradeStackParamList = {
  Trade: undefined;
  OrderHistory: undefined;
  Watchlist: undefined;
};

export type AlertsStackParamList = {
  Alerts: undefined;
  CreateAlert: undefined;
  AlertDetail: { id: string };
};

// Form Types
export interface FormField {
  name: string;
  label: string;
  type:
    "text" | "email" | "password" | "number" | "select" | "checkbox" | "radio";
  placeholder?: string;
  required?: boolean;
  validation?: ValidationRule[];
  options?: SelectOption[];
}

export interface ValidationRule {
  type: "required" | "email" | "minLength" | "maxLength" | "pattern" | "custom";
  value?: any;
  message: string;
}

export interface SelectOption {
  label: string;
  value: any;
}

// Theme Types
export interface Theme {
  primary: string;
  secondary: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  border: string;
  error: string;
  warning: string;
  success: string;
  info: string;
  shadow: string;
}

export interface ThemeContextType {
  theme: Theme;
  isDarkMode: boolean;
  toggleTheme: () => void;
  setTheme: (theme: "light" | "dark" | "auto") => void;
}

// Utility Types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

export type Nullable<T> = T | null;

export type AsyncState<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
};
