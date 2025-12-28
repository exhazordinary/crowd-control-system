'use client';

import { useState, useEffect, use, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft, Users, Clock, AlertTriangle, Activity,
  Radio, Siren, Volume2, VolumeX, Bell
} from 'lucide-react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useSimulation } from '@/hooks/useSimulation';
import { formatNumber, formatTime, cn } from '@/lib/utils';
import type { Scenario, Venue } from '@/types';
import { StatCard } from '@/components/dashboard/StatCard';
import { SimulationControls } from '@/components/dashboard/SimulationControls';
import { VenueMap } from '@/components/visualization/VenueMap';
import { AlertPanel } from '@/components/alerts/AlertPanel';
import { AttendanceChart } from '@/components/charts/AttendanceChart';
import { ZoneList } from '@/components/visualization/ZoneList';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { StaffNotifications, NotificationButton } from '@/components/notifications/StaffNotifications';

interface PageProps {
  params: Promise<{ eventId: string }>;
}

export default function DashboardPage({ params }: PageProps) {
  const { eventId } = use(params);
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [venue, setVenue] = useState<Venue | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isEmergencyMode, setIsEmergencyMode] = useState(false);
  const [selectedZone, setSelectedZone] = useState<string | null>(null);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const {
    state,
    alerts,
    recommendations,
    isLoading,
    error,
    start,
    step,
    reset,
    pause,
    resume,
  } = useSimulation(eventId, { autoStep: true, stepInterval: 500 });

  // Load scenario and venue data
  useEffect(() => {
    const loadData = async () => {
      try {
        const scenarios = await api.getScenarios();
        const found = scenarios.find(s => s.scenario_id === eventId);
        if (found) {
          setScenario(found);
          const venueData = await api.getVenue(found.venue_id);
          setVenue(venueData);
        }
      } catch (err) {
        console.error('Failed to load data:', err);
      }
    };

    loadData();
  }, [eventId]);

  // Play alert sound when critical alerts come in
  useEffect(() => {
    if (soundEnabled && alerts.some(a => a.level === 'critical' || a.level === 'emergency')) {
      // Play alert sound (using Web Audio API for simple beep)
      try {
        const audioContext = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        oscillator.frequency.value = 880;
        oscillator.type = 'sine';
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.3);
      } catch {
        // Audio not supported
      }
    }
  }, [alerts, soundEnabled]);

  // Initialize simulation
  const handleStart = async () => {
    await start(eventId, 1.0);
    setIsInitialized(true);
  };

  const handleReset = async () => {
    await reset();
    setIsInitialized(false);
    setIsEmergencyMode(false);
    setSelectedZone(null);
  };

  const handleEmergencyToggle = useCallback(() => {
    setIsEmergencyMode(prev => !prev);
    if (!isEmergencyMode && soundEnabled) {
      // Play emergency siren sound
      try {
        const audioContext = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        oscillator.frequency.value = 660;
        oscillator.type = 'sawtooth';
        gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
      } catch {
        // Audio not supported
      }
    }
  }, [isEmergencyMode, soundEnabled]);

  const handleZoneClick = (zoneId: string) => {
    setSelectedZone(prev => prev === zoneId ? null : zoneId);
  };

  const crowdState = state?.crowd_state;
  const isRunning = state?.is_running && !state?.is_paused;

  // Calculate average density
  const avgDensity = crowdState
    ? Object.values(crowdState.zone_states).reduce((sum, z) => sum + z.density, 0) /
      Math.max(Object.keys(crowdState.zone_states).length, 1)
    : 0;

  return (
    <div className={cn(
      'min-h-screen bg-background transition-colors duration-300',
      isEmergencyMode && 'bg-red-50'
    )}>
      {/* Emergency Mode Overlay */}
      <AnimatePresence>
        {isEmergencyMode && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-red-500/10 pointer-events-none z-40"
          />
        )}
      </AnimatePresence>

      {/* Header */}
      <header className={cn(
        'sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60',
        isEmergencyMode && 'bg-red-50/95 border-red-200'
      )}>
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="p-2 hover:bg-muted rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-3">
              <div className={cn(
                'flex h-9 w-9 items-center justify-center rounded-lg',
                isEmergencyMode ? 'bg-red-600 text-white animate-pulse' : 'bg-primary text-primary-foreground'
              )}>
                {isEmergencyMode ? <Siren className="h-5 w-5" /> : <Radio className="h-5 w-5" />}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-lg font-semibold">
                    {scenario?.name || 'Loading...'}
                  </h1>
                  {isEmergencyMode && (
                    <Badge variant="emergency">EMERGENCY MODE</Badge>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">
                  {venue?.name || ''} - {formatNumber(scenario?.expected_attendance || 0)} expected
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Sound Toggle */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSoundEnabled(!soundEnabled)}
              className="h-9 w-9"
            >
              {soundEnabled ? (
                <Volume2 className="h-4 w-4" />
              ) : (
                <VolumeX className="h-4 w-4 text-muted-foreground" />
              )}
            </Button>

            {/* Staff Notifications */}
            <NotificationButton
              unreadCount={alerts.filter(a => !a.is_acknowledged).length + recommendations.filter(r => !r.is_applied).length}
              criticalCount={alerts.filter(a => (a.level === 'critical' || a.level === 'emergency') && !a.is_acknowledged).length}
              onClick={() => setNotificationsOpen(true)}
            />

            <SimulationControls
              isRunning={isRunning ?? false}
              isPaused={state?.is_paused || false}
              speed={state?.speed || 1}
              isInitialized={isInitialized}
              isLoading={isLoading}
              isEmergencyMode={isEmergencyMode}
              onStart={handleStart}
              onPause={pause}
              onResume={resume}
              onStep={() => step(1)}
              onReset={handleReset}
              onEmergencyToggle={isInitialized ? handleEmergencyToggle : undefined}
            />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container py-6">
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-lg mb-6"
          >
            {error}
          </motion.div>
        )}

        {/* Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <StatCard
            title="Inside Venue"
            value={formatNumber(crowdState?.total_inside || 0)}
            icon={<Users className="w-5 h-5" />}
            trend={crowdState?.overall_inflow_rate ? `+${Math.round(crowdState.overall_inflow_rate)}/min` : undefined}
            color="blue"
          />
          <StatCard
            title="In Queue"
            value={formatNumber(crowdState?.total_queuing || 0)}
            icon={<Clock className="w-5 h-5" />}
            status={crowdState && crowdState.total_queuing > 2000 ? 'warning' : 'normal'}
            color="amber"
          />
          <StatCard
            title="Avg Density"
            value={`${avgDensity.toFixed(1)}/m²`}
            icon={<Activity className="w-5 h-5" />}
            status={avgDensity > 4 ? 'critical' : avgDensity > 2 ? 'warning' : 'normal'}
            color="green"
          />
          <StatCard
            title="Active Alerts"
            value={alerts.length.toString()}
            icon={<AlertTriangle className="w-5 h-5" />}
            status={alerts.some(a => a.level === 'critical' || a.level === 'emergency') ? 'critical' : alerts.length > 0 ? 'warning' : 'normal'}
            color="red"
          />
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Venue Map - 8 columns */}
          <div className="lg:col-span-8 space-y-6">
            {venue && crowdState ? (
              <VenueMap
                venue={venue}
                zoneStates={crowdState.zone_states}
                gateStates={crowdState.gate_states}
                isEmergencyMode={isEmergencyMode}
                onZoneClick={handleZoneClick}
                selectedZone={selectedZone}
              />
            ) : (
              <Card>
                <CardContent className="h-[420px] flex items-center justify-center">
                  <div className="text-center text-muted-foreground">
                    {isInitialized ? (
                      <div className="flex flex-col items-center gap-2">
                        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                        <span>Loading venue map...</span>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center gap-2">
                        <Radio className="w-12 h-12 text-muted-foreground/50" />
                        <span>Start simulation to see venue map</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Attendance Chart */}
            <AttendanceChart
              currentMinute={state?.current_time_minutes || 0}
              totalInside={crowdState?.total_inside || 0}
              totalQueuing={crowdState?.total_queuing || 0}
              capacity={venue?.total_capacity || 0}
              isEmergencyMode={isEmergencyMode}
            />
          </div>

          {/* Sidebar - 4 columns */}
          <div className="lg:col-span-4 space-y-6">
            {/* Simulation Time */}
            <Card className={cn(
              isEmergencyMode && 'ring-2 ring-red-500'
            )}>
              <CardContent className="p-4">
                <div className="text-center">
                  <div className="text-sm text-muted-foreground mb-1">Simulation Time</div>
                  <div className="text-3xl font-semibold tracking-tight">
                    {formatTime(state?.current_time_minutes || 0)}
                  </div>
                  <div className="flex items-center justify-center gap-2 mt-2">
                    <Badge variant="secondary">
                      {state?.speed || 1}x speed
                    </Badge>
                    {isRunning && (
                      <Badge variant="default" className="animate-pulse">
                        Running
                      </Badge>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Alerts Panel */}
            <AlertPanel
              alerts={alerts}
              recommendations={recommendations}
              isEmergencyMode={isEmergencyMode}
            />

            {/* Zone List */}
            {venue && crowdState && (
              <ZoneList
                zones={venue.zones}
                zoneStates={crowdState.zone_states}
                onZoneClick={handleZoneClick}
                selectedZone={selectedZone}
              />
            )}
          </div>
        </div>
      </main>

      {/* Emergency Mode Footer */}
      <AnimatePresence>
        {isEmergencyMode && (
          <motion.div
            initial={{ y: 100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 100, opacity: 0 }}
            className="fixed bottom-0 left-0 right-0 bg-red-600 text-white py-3 px-4 z-50"
          >
            <div className="container flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Siren className="w-5 h-5 animate-pulse" />
                <span className="font-semibold">EMERGENCY EVACUATION MODE ACTIVE</span>
              </div>
              <div className="text-sm">
                All emergency exits highlighted • Follow evacuation procedures
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Staff Notifications Panel */}
      <AnimatePresence>
        {notificationsOpen && (
          <StaffNotifications
            alerts={alerts}
            recommendations={recommendations}
            isOpen={notificationsOpen}
            onClose={() => setNotificationsOpen(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
