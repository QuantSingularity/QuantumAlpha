import { useSelector } from "react-redux";
import { Navigate, Route, Routes } from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import Analytics from "./pages/Analytics";
import Dashboard from "./pages/Dashboard";
import Homepage from "./pages/Homepage";
import Login from "./pages/Login";
import NewsFeed from "./pages/NewsFeed";
import NotFound from "./pages/NotFound";
import OAuthCallback from "./pages/OAuthCallback";
import Profile from "./pages/Profile";
import Register from "./pages/Register";
import Settings from "./pages/Settings";
import Strategies from "./pages/Strategies";
import StrategyDetails from "./pages/StrategyDetails";
import Trading from "./pages/Trading";
import Watchlist from "./pages/Watchlist";

const App = () => {
  const { isAuthenticated } = useSelector((state) => state.auth);

  return (
    <Routes>
      {/* ── Public / Landing ─────────────────────────────── */}
      {/* Homepage always accessible; shows CTA or "Go to Dashboard" */}
      <Route path="/" element={<Homepage />} />

      {/* Auth pages — redirect authenticated users to dashboard */}
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

      {/* OAuth 2.0 PKCE callback handler */}
      <Route path="/auth/callback" element={<OAuthCallback />} />

      {/* ── Protected routes (inside sidebar layout) ─────── */}
      <Route element={<MainLayout />}>
        <Route
          path="/dashboard"
          element={
            isAuthenticated ? <Dashboard /> : <Navigate to="/login" replace />
          }
        />
        <Route
          path="/strategies"
          element={
            isAuthenticated ? <Strategies /> : <Navigate to="/login" replace />
          }
        />
        <Route
          path="/strategies/:id"
          element={
            isAuthenticated ? (
              <StrategyDetails />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
        <Route
          path="/analytics"
          element={
            isAuthenticated ? <Analytics /> : <Navigate to="/login" replace />
          }
        />
        <Route
          path="/trading"
          element={
            isAuthenticated ? <Trading /> : <Navigate to="/login" replace />
          }
        />
        <Route
          path="/profile"
          element={
            isAuthenticated ? <Profile /> : <Navigate to="/login" replace />
          }
        />
        <Route
          path="/watchlist"
          element={
            isAuthenticated ? <Watchlist /> : <Navigate to="/login" replace />
          }
        />
        <Route
          path="/news"
          element={
            isAuthenticated ? <NewsFeed /> : <Navigate to="/login" replace />
          }
        />
        <Route
          path="/settings"
          element={
            isAuthenticated ? <Settings /> : <Navigate to="/login" replace />
          }
        />
      </Route>

      {/* ── 404 ─────────────────────────────────────────── */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};

export default App;
