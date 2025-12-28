// Venue Types
export interface Gate {
  gate_id: string;
  name: string;
  capacity_per_minute: number;
  location: [number, number];
  is_emergency_exit: boolean;
  connected_zones: string[];
  is_open: boolean;
  current_queue: number;
}

export interface Zone {
  zone_id: string;
  name: string;
  capacity: number;
  area_sqm: number;
  zone_type: string;
  connected_zones: string[];
  connected_gates: string[];
  current_occupancy: number;
  svg_path?: string;
}

export interface VenueLocation {
  lat: number;
  lng: number;
  address: string;
  city: string;
}

export interface Venue {
  venue_id: string;
  name: string;
  venue_type: 'stadium' | 'arena' | 'convention' | 'outdoor';
  total_capacity: number;
  gates: Gate[];
  zones: Zone[];
  location: VenueLocation;
  floor_plan_svg?: string;
}

// Event Types
export type EventType = 'concert' | 'football' | 'festival' | 'conference' | 'rally';

export interface Event {
  event_id: string;
  name: string;
  venue_id: string;
  event_type: EventType;
  start_time: string;
  end_time: string;
  gates_open?: string;
  expected_attendance: number;
}

// Crowd State Types
export interface ZoneState {
  zone_id: string;
  current_occupancy: number;
  density: number;
  inflow_rate: number;
  outflow_rate: number;
  risk_level: 'safe' | 'moderate' | 'high' | 'critical';
}

export interface GateState {
  gate_id: string;
  queue_length: number;
  throughput_rate: number;
  wait_time_minutes: number;
  is_congested: boolean;
}

export interface CrowdState {
  event_id: string;
  timestamp: string;
  simulation_time_minutes: number;
  total_inside: number;
  total_queuing: number;
  total_exited: number;
  total_approaching: number;
  zone_states: Record<string, ZoneState>;
  gate_states: Record<string, GateState>;
  overall_inflow_rate: number;
  overall_outflow_rate: number;
}

export interface SimulationState {
  event_id: string;
  is_running: boolean;
  is_paused: boolean;
  speed: number;
  current_time_minutes: number;
  crowd_state: CrowdState;
  scenario: string;
}

// Alert Types
export type AlertLevel = 'info' | 'warning' | 'critical' | 'emergency';
export type AlertCategory = 'density' | 'queue' | 'flow' | 'capacity' | 'safety' | 'transport';

export interface Alert {
  alert_id: string;
  event_id: string;
  timestamp: string;
  level: AlertLevel;
  category: AlertCategory;
  zone_id?: string;
  gate_id?: string;
  title: string;
  message: string;
  suggested_actions: string[];
  is_acknowledged: boolean;
}

export interface Recommendation {
  recommendation_id: string;
  event_id: string;
  timestamp: string;
  category: string;
  title: string;
  description: string;
  impact: string;
  affected_zones: string[];
  affected_gates: string[];
  confidence: number;
  is_applied: boolean;
  icon: string;
}

// Scenario Types
export interface Scenario {
  scenario_id: string;
  name: string;
  description: string;
  venue_id: string;
  event_type: EventType;
  expected_attendance: number;
  demo_highlights: string[];
}

// WebSocket Message Types
export type WSMessageType = 'state_update' | 'alert' | 'recommendation' | 'speed_changed' | 'paused' | 'resumed';

export interface WSMessage {
  type: WSMessageType;
  data?: SimulationState | Alert | Recommendation | number;
}
