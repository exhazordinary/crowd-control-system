'use client';

import { Play, Pause, SkipForward, RotateCcw, Loader2, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface SimulationControlsProps {
  isRunning: boolean;
  isPaused: boolean;
  speed: number;
  isInitialized: boolean;
  isLoading: boolean;
  isEmergencyMode?: boolean;
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
  onStep: () => void;
  onReset: () => void;
  onEmergencyToggle?: () => void;
}

export const SimulationControls = ({
  isRunning,
  isPaused,
  speed,
  isInitialized,
  isLoading,
  isEmergencyMode = false,
  onStart,
  onPause,
  onResume,
  onStep,
  onReset,
  onEmergencyToggle,
}: SimulationControlsProps) => {
  if (!isInitialized) {
    return (
      <Button
        onClick={onStart}
        disabled={isLoading}
        size="default"
        className="transition-all duration-200"
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
        ) : (
          <Play className="w-4 h-4 mr-2" />
        )}
        Start Simulation
      </Button>
    );
  }

  return (
    <div className="flex items-center gap-2">
      {/* Emergency Mode Toggle */}
      {onEmergencyToggle && (
        <Button
          onClick={onEmergencyToggle}
          variant={isEmergencyMode ? "destructive" : "outline"}
          size="sm"
          className={isEmergencyMode ? "animate-pulse" : ""}
        >
          <AlertTriangle className="w-4 h-4 mr-2" />
          {isEmergencyMode ? "Exit Emergency" : "Emergency Mode"}
        </Button>
      )}

      {/* Play/Pause */}
      {isRunning ? (
        <Button
          onClick={onPause}
          variant="secondary"
          size="sm"
        >
          <Pause className="w-4 h-4 mr-2" />
          Pause
        </Button>
      ) : (
        <Button
          onClick={onResume}
          variant="default"
          size="sm"
        >
          <Play className="w-4 h-4 mr-2" />
          Resume
        </Button>
      )}

      {/* Step */}
      <Button
        onClick={onStep}
        disabled={isRunning}
        variant="outline"
        size="sm"
      >
        <SkipForward className="w-4 h-4 mr-2" />
        Step
      </Button>

      {/* Reset */}
      <Button
        onClick={onReset}
        variant="outline"
        size="sm"
        className="text-red-600 hover:text-red-700 hover:bg-red-50"
      >
        <RotateCcw className="w-4 h-4 mr-2" />
        Reset
      </Button>

      {/* Speed indicator */}
      <Badge variant="secondary" className="ml-2">
        {speed}x speed
      </Badge>
    </div>
  );
};
