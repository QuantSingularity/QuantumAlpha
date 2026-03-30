import { IconButton, Tooltip } from "@mui/material";
import { Moon, Sun } from "lucide-react";
import { useDispatch, useSelector } from "react-redux";
import { toggleDarkMode } from "../store/slices/themeSlice";

const DarkModeToggle = ({ size = 24, showTooltip = true }) => {
  const dispatch = useDispatch();
  const { darkMode, primaryColor } = useSelector((state) => state.theme);

  const handleToggle = () => {
    dispatch(toggleDarkMode());
  };

  const button = (
    <IconButton
      onClick={handleToggle}
      sx={{
        color: darkMode ? primaryColor : "#f59e0b",
        background: darkMode
          ? "rgba(0, 212, 255, 0.1)"
          : "rgba(245, 158, 11, 0.1)",
        transition: "all 0.3s ease",
        "&:hover": {
          background: darkMode
            ? "rgba(0, 212, 255, 0.2)"
            : "rgba(245, 158, 11, 0.2)",
          transform: "scale(1.1)",
        },
      }}
    >
      {darkMode ? <Moon size={size} /> : <Sun size={size} />}
    </IconButton>
  );

  if (showTooltip) {
    return (
      <Tooltip title={`Switch to ${darkMode ? "light" : "dark"} mode`}>
        {button}
      </Tooltip>
    );
  }

  return button;
};

export default DarkModeToggle;
