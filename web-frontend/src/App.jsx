import { useSelector } from "react-redux";
import { Navigate, Route, Routes } from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import Analytics from "./pages/Analytics";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import NewsFeed from "./pages/NewsFeed";
import NotFound from "./pages/NotFound";
import Profile from "./pages/Profile";
import Register from "./pages/Register";
import Settings from "./pages/Settings";
import Strategies from "./pages/Strategies";
import StrategyDetails from "./pages/StrategyDetails";
import Watchlist from "./pages/Watchlist";

const App = () => {
  const { isAuthenticated } = useSelector((state) => state.auth);

  return (
    <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={!isAuthenticated ? <Login /> : <Navigate to="/" />}
      />
      <Route
        path="/register"
        element={!isAuthenticated ? <Register /> : <Navigate to="/" />}
      />

      {/* Protected routes */}
      <Route element={<MainLayout />}>
        <Route
          path="/"
          element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />}
        />
        <Route
          path="/strategies"
          element={isAuthenticated ? <Strategies /> : <Navigate to="/login" />}
        />
        <Route
          path="/strategies/:id"
          element={
            isAuthenticated ? <StrategyDetails /> : <Navigate to="/login" />
          }
        />
        <Route
          path="/analytics"
          element={isAuthenticated ? <Analytics /> : <Navigate to="/login" />}
        />
        <Route
          path="/profile"
          element={isAuthenticated ? <Profile /> : <Navigate to="/login" />}
        />
        <Route
          path="/watchlist"
          element={isAuthenticated ? <Watchlist /> : <Navigate to="/login" />}
        />
        <Route
          path="/news"
          element={isAuthenticated ? <NewsFeed /> : <Navigate to="/login" />}
        />
        <Route
          path="/settings"
          element={isAuthenticated ? <Settings /> : <Navigate to="/login" />}
        />
      </Route>

      {/* 404 route */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};

export default App;
