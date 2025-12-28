import type { Venue, Event, Scenario, SimulationState, Alert, Recommendation } from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

class APIClient {
  private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Venues
  async getVenues(): Promise<Venue[]> {
    return this.fetch<Venue[]>('/venues');
  }

  async getVenue(venueId: string): Promise<Venue> {
    return this.fetch<Venue>(`/venues/${venueId}`);
  }

  // Events
  async getEvents(venueId?: string): Promise<Event[]> {
    const query = venueId ? `?venue_id=${venueId}` : '';
    return this.fetch<Event[]>(`/events${query}`);
  }

  async getEvent(eventId: string): Promise<Event> {
    return this.fetch<Event>(`/events/${eventId}`);
  }

  // Scenarios
  async getScenarios(): Promise<Scenario[]> {
    return this.fetch<Scenario[]>('/simulation/scenarios');
  }

  // Simulation
  async startSimulation(eventId: string, scenarioId?: string, speed = 1.0): Promise<{ status: string; event_id: string }> {
    return this.fetch('/simulation/start', {
      method: 'POST',
      body: JSON.stringify({
        event_id: eventId,
        scenario_id: scenarioId,
        speed,
      }),
    });
  }

  async stepSimulation(eventId: string, steps = 1): Promise<{
    state: SimulationState;
    alerts: Alert[];
    recommendations: Recommendation[];
  }> {
    return this.fetch(`/simulation/step/${eventId}`, {
      method: 'POST',
      body: JSON.stringify({ steps }),
    });
  }

  async getSimulationState(eventId: string): Promise<{
    state: SimulationState;
    alerts?: Alert[];
    recommendations?: Recommendation[];
  }> {
    return this.fetch(`/simulation/${eventId}/state`);
  }

  async stopSimulation(eventId: string): Promise<{ status: string }> {
    return this.fetch(`/simulation/stop/${eventId}`, { method: 'POST' });
  }

  async resetSimulation(eventId: string): Promise<{ status: string }> {
    return this.fetch(`/simulation/reset/${eventId}`, { method: 'POST' });
  }

  // Alerts
  async getAlerts(eventId: string): Promise<Alert[]> {
    return this.fetch<Alert[]>(`/alerts/${eventId}`);
  }

  async acknowledgeAlert(alertId: string): Promise<{ status: string }> {
    return this.fetch(`/alerts/${alertId}/acknowledge`, { method: 'POST' });
  }

  async getRecommendations(eventId: string): Promise<Recommendation[]> {
    return this.fetch<Recommendation[]>(`/alerts/${eventId}/recommendations`);
  }
}

export const api = new APIClient();
