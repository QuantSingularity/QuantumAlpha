import { useSelector } from "react-redux";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import Analytics from "./pages/Analytics";
import Dashboard from "./pages/Dashboard";
import ForgotPassword from "./pages/ForgotPassword";
import Homepage from "./pages/Homepage";
import Login from "./pages/Login";
import NewsFeed from "./pages/NewsFeed";
import NotFound from "./pages/NotFound";
import OAuthCallback from "./pages/OAuthCallback";
import Profile from "./pages/Profile";
import Register from "./pages/Register";
import Settings from "./pages/Settings";
import AIInsights from "./pages/AIInsights";
import Strategies from "./pages/Strategies";
import StrategyDetails from "./pages/StrategyDetails";
import Trading from "./pages/Trading";
import Watchlist from "./pages/Watchlist";

// Gate that remembers where the user was headed so login can return them there.
const RequireAuth = ({ children }) => {
  const { isAuthenticated } = useSelector((state) => state.auth);
  const location = useLocation();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return children;
};

const App = () => {
  const { isAuthenticated } = useSelector((state) => state.auth);

  return (
    <Routes>
      {/* Public / landing - the app always opens here */}
      <Route path="/" element={<Homepage />} />

      {/* Auth pages redirect authenticated users into the app */}
      <Route
        path="/login"
        element={
          !isAuthenticated ? <Login /> : <Navigate to="/dashboard" replace />
        }
      />
      <Route
        path="/register"
        element={
          !isAuthenticated ? <Register /> : <Navigate to="/dashboard" replace />
        }
      />
      <Route
        path="/forgot-password"
        element={
          !isAuthenticated ? (
            <ForgotPassword />
          ) : (
            <Navigate to="/dashboard" replace />
          )
        }
      />
      <Route path="/auth/callback" element={<OAuthCallback />} />

      {/* Protected app routes inside the sidebar shell */}
      <Route element={<MainLayout />}>
        <Route
          path="/dashboard"
          element={
            <RequireAuth>
              <Dashboard />
            </RequireAuth>
          }
        />
        <Route
          path="/strategies"
          element={
            <RequireAuth>
              <Strategies />
            </RequireAuth>
          }
        />
        <Route
          path="/strategies/:id"
          element={
            <RequireAuth>
              <StrategyDetails />
            </RequireAuth>
          }
        />
        <Route
          path="/ai-insights"
          element={
            <RequireAuth>
              <AIInsights />
            </RequireAuth>
          }
        />
        <Route
          path="/analytics"
          element={
            <RequireAuth>
              <Analytics />
            </RequireAuth>
          }
        />
        <Route
          path="/trading"
          element={
            <RequireAuth>
              <Trading />
            </RequireAuth>
          }
        />
        <Route
          path="/profile"
          element={
            <RequireAuth>
              <Profile />
            </RequireAuth>
          }
        />
        <Route
          path="/watchlist"
          element={
            <RequireAuth>
              <Watchlist />
            </RequireAuth>
          }
        />
        <Route
          path="/news"
          element={
            <RequireAuth>
              <NewsFeed />
            </RequireAuth>
          }
        />
        <Route
          path="/settings"
          element={
            <RequireAuth>
              <Settings />
            </RequireAuth>
          }
        />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};

export default App;
