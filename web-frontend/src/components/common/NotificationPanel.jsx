import { Alert, Slide, Snackbar } from "@mui/material";
import { useDispatch, useSelector } from "react-redux";
import { removeNotification } from "../../store/slices/uiSlice";

const NotificationPanel = () => {
  const dispatch = useDispatch();
  const notifications = useSelector((state) => state.ui.notifications);

  const handleClose = (id) => {
    dispatch(removeNotification(id));
  };

  return (
    <>
      {notifications.map((notification, index) => (
        <Snackbar
          key={notification.id}
          open={true}
          anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
          TransitionComponent={Slide}
          autoHideDuration={notification.duration || 6000}
          onClose={() => handleClose(notification.id)}
          sx={{ bottom: { xs: 16 + index * 72, sm: 24 + index * 72 } }}
        >
          <Alert
            onClose={() => handleClose(notification.id)}
            severity={notification.type || "info"}
            variant="filled"
            elevation={6}
            sx={{ width: "100%" }}
          >
            {notification.message}
          </Alert>
        </Snackbar>
      ))}
    </>
  );
};

export default NotificationPanel;
