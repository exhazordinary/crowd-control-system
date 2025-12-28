'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import type { SimulationState, Alert, Recommendation, WSMessage } from '@/types';

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

interface UseWebSocketOptions {
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export const useWebSocket = (eventId: string | null, options: UseWebSocketOptions = {}) => {
  const {
    autoConnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [state, setState] = useState<SimulationState | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (!eventId || wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      wsRef.current = new WebSocket(`${WS_BASE}/ws/simulation/${eventId}`);

      wsRef.current.onopen = () => {
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);

          switch (message.type) {
            case 'state_update':
              setState(message.data as SimulationState);
              break;
            case 'alert':
              setAlerts(prev => {
                const newAlert = message.data as Alert;
                // Avoid duplicates
                if (prev.some(a => a.alert_id === newAlert.alert_id)) {
                  return prev;
                }
                return [newAlert, ...prev].slice(0, 10);
              });
              break;
            case 'recommendation':
              setRecommendations(prev => {
                const newRec = message.data as Recommendation;
                if (prev.some(r => r.recommendation_id === newRec.recommendation_id)) {
                  return prev;
                }
                return [newRec, ...prev].slice(0, 5);
              });
              break;
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      wsRef.current.onclose = () => {
        setIsConnected(false);

        // Attempt reconnection
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval);
        } else {
          setError('Connection lost. Please refresh the page.');
        }
      };

      wsRef.current.onerror = () => {
        setError('WebSocket connection error');
      };
    } catch (err) {
      setError('Failed to connect to WebSocket');
    }
  }, [eventId, maxReconnectAttempts, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const send = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const setSpeed = useCallback((speed: number) => {
    send({ type: 'set_speed', speed });
  }, [send]);

  const pause = useCallback(() => {
    send({ type: 'pause' });
  }, [send]);

  const resume = useCallback(() => {
    send({ type: 'resume' });
  }, [send]);

  const step = useCallback((count = 1) => {
    send({ type: 'step', count });
  }, [send]);

  // Auto-connect effect
  useEffect(() => {
    if (autoConnect && eventId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, eventId, connect, disconnect]);

  return {
    isConnected,
    state,
    alerts,
    recommendations,
    error,
    connect,
    disconnect,
    setSpeed,
    pause,
    resume,
    step,
  };
};
