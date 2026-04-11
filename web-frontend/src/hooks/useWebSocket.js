import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Custom hook for WebSocket connections
 * @param {string} url - WebSocket URL
 * @param {object} options - Options for connection
 * @returns {object} WebSocket connection state and methods
 */
export const useWebSocket = (url, options = {}) => {
  const {
    onOpen,
    onClose,
    onMessage,
    onError,
    reconnect = true,
    reconnectInterval = 3000,
    reconnectAttempts = 10,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimerRef = useRef(null);

  // Keep callbacks in refs so the connect() closure never goes stale
  const onOpenRef = useRef(onOpen);
  const onCloseRef = useRef(onClose);
  const onMessageRef = useRef(onMessage);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onOpenRef.current = onOpen;
    onCloseRef.current = onClose;
    onMessageRef.current = onMessage;
    onErrorRef.current = onError;
  });

  const connect = useCallback(() => {
    if (!url) return;

    try {
      const ws = new WebSocket(url);

      ws.onopen = (event) => {
        setIsConnected(true);
        setError(null);
        reconnectCountRef.current = 0;
        if (onOpenRef.current) onOpenRef.current(event);
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        if (onCloseRef.current) onCloseRef.current(event);

        // Attempt reconnection
        if (reconnect && reconnectCountRef.current < reconnectAttempts) {
          reconnectTimerRef.current = setTimeout(() => {
            reconnectCountRef.current += 1;
            connect();
          }, reconnectInterval);
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
          if (onMessageRef.current) onMessageRef.current(data);
        } catch (err) {
          console.error("Error parsing WebSocket message:", err);
        }
      };

      ws.onerror = (event) => {
        const errorMsg = "WebSocket error occurred";
        setError(errorMsg);
        if (onErrorRef.current) onErrorRef.current(event);
      };

      wsRef.current = ws;
    } catch (err) {
      setError(err.message);
      console.error("Error creating WebSocket:", err);
    }
  }, [url, reconnect, reconnectInterval, reconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((data) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    } else {
      console.warn("WebSocket is not connected");
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    error,
    sendMessage,
    disconnect,
    reconnect: connect,
  };
};

export default useWebSocket;
