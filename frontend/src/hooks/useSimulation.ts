'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import type { SimulationState, Alert, Recommendation } from '@/types';
import { api } from '@/lib/api';

interface UseSimulationOptions {
  autoStep?: boolean;
  stepInterval?: number;
}

export const useSimulation = (eventId: string | null, options: UseSimulationOptions = {}) => {
  const { autoStep = false, stepInterval = 1000 } = options;

  const [state, setState] = useState<SimulationState | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const start = useCallback(async (scenarioId?: string, speed = 1.0) => {
    if (!eventId) return;

    setIsLoading(true);
    setError(null);

    try {
      await api.startSimulation(eventId, scenarioId, speed);
      const result = await api.getSimulationState(eventId);
      setState(result.state);
      setAlerts(result.alerts || []);
      setRecommendations(result.recommendations || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start simulation');
    } finally {
      setIsLoading(false);
    }
  }, [eventId]);

  const step = useCallback(async (steps = 1) => {
    if (!eventId) return;

    try {
      const result = await api.stepSimulation(eventId, steps);
      setState(result.state);
      setAlerts(result.alerts);
      setRecommendations(result.recommendations);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to step simulation');
    }
  }, [eventId]);

  const stop = useCallback(async () => {
    if (!eventId) return;

    try {
      await api.stopSimulation(eventId);
      if (state) {
        setState({ ...state, is_running: false });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop simulation');
    }
  }, [eventId, state]);

  const reset = useCallback(async () => {
    if (!eventId) return;

    try {
      await api.resetSimulation(eventId);
      setState(null);
      setAlerts([]);
      setRecommendations([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset simulation');
    }
  }, [eventId]);

  const pause = useCallback(() => {
    if (state) {
      setState({ ...state, is_paused: true });
    }
  }, [state]);

  const resume = useCallback(() => {
    if (state) {
      setState({ ...state, is_paused: false });
    }
  }, [state]);

  const setSpeed = useCallback((speed: number) => {
    if (state) {
      setState({ ...state, speed });
    }
  }, [state]);

  // Auto-step effect
  useEffect(() => {
    if (!autoStep || !state?.is_running || state?.is_paused) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    intervalRef.current = setInterval(() => {
      step(1);
    }, stepInterval / (state.speed || 1));

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [autoStep, state?.is_running, state?.is_paused, state?.speed, step, stepInterval]);

  return {
    state,
    alerts,
    recommendations,
    isLoading,
    error,
    start,
    step,
    stop,
    reset,
    pause,
    resume,
    setSpeed,
  };
};
