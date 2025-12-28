# AI-Powered Crowd Control System

An AI-powered crowd simulation and management system for Malaysian events. Predicts, simulates, and manages crowd movements without requiring additional sensors or hardware.

## Features

### Core Capabilities
- **Data Ingestion**: Upload ticketing records, transport schedules, event configurations via CSV/JSON
- **Scenario Simulation**: Models crowd movements (entry rush, half-time exits, emergency evacuation)
- **Risk Identification**: Predicts bottlenecks, overcrowded zones, parking overflow
- **Smart Recommendations**: Provides actionable, specific suggestions for event staff
- **Real-time Dashboard**: Interactive visualization with density heatmaps and live updates

### New Features
- **Custom Scenarios**: Upload your own data to create runnable simulations
- **Pre-Event Planner**: Plan and compare multiple scenarios before the event
- **Transport Integration**: Sync gate operations with LRT/bus schedules
- **WhatsApp-Style Notifications**: Staff alerts with quick action buttons
- **Import/Export**: Save and load event plans as JSON files

## Demo Scenarios

| Scenario | Venue | Attendance | Type |
|----------|-------|------------|------|
| Stadium Exit Rush | Bukit Jalil Stadium | 75,000 | Football Match |
| K-Pop Concert Entry | Axiata Arena | 15,500 | Concert |
| CNY Festival | Pavilion KL | 50,000 | Festival |

## Screenshots

### Home Page
Select from demo scenarios or your custom uploaded scenarios.

### Dashboard
Real-time simulation with:
- Interactive venue map with zone density
- Live statistics (inside, queuing, exited)
- AI-powered alerts and recommendations
- Staff notification panel

### Data Import
Upload CSV files to create custom scenarios:
- Ticketing data (zones, gates, entry times)
- Transport schedules (LRT/bus arrivals)
- Event phases (gates open, halftime, exit)

### Pre-Event Planner
- Configure gate opening times
- Adjust expected attendance
- Compare multiple scenarios side-by-side
- Export/import plans

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15, React 19, TypeScript, TailwindCSS, shadcn/ui |
| Charts | Recharts |
| Animation | Framer Motion |
| Backend | Python 3.10+, FastAPI, Pydantic |
| Simulation | NumPy, SciPy (Social Force Model) |
| Real-time | WebSocket |

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or pnpm

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

### Access the Application

| URL | Description |
|-----|-------------|
| http://localhost:3000 | Frontend Application |
| http://localhost:3000/data-import | Data Import Page |
| http://localhost:3000/planner | Pre-Event Planner |
| http://localhost:8000 | Backend API |
| http://localhost:8000/docs | Swagger API Docs |

## Creating Custom Scenarios

### Step 1: Prepare Your Data

**Ticketing CSV:**
```csv
ticket_id,zone,gate,purchase_time,entry_time_estimate,seat_section
TK001,north-stand,gate-a,2024-01-15 10:30,19:00,A1
TK002,south-stand,gate-c,2024-01-15 14:22,19:15,B5
```

**Transport CSV:**
```csv
transport_type,station,arrival_time,capacity,expected_passengers
lrt,Bukit Jalil,18:30,1200,1100
bus,Stadium Bus Stop,18:35,50,45
```

**Schedule CSV:**
```csv
event_phase,start_time,end_time,description
gates_open,18:00,19:30,Entry period
event_start,19:30,19:30,Match kickoff
halftime,20:15,20:30,Half-time break
```

### Step 2: Upload Data

1. Go to `/data-import`
2. Enter an Event ID (e.g., "my-concert-2024")
3. Upload your ticketing CSV
4. (Optional) Upload transport and schedule data
5. Click "Run Simulation" to see your custom scenario

### Step 3: Run Simulation

Your custom scenario appears on the homepage with a "Custom uploaded data" badge.

## Project Structure

```
crowd-control-system/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx              # Home - scenario selection
│   │   │   ├── dashboard/[eventId]/  # Simulation dashboard
│   │   │   ├── data-import/          # CSV upload wizard
│   │   │   └── planner/              # Pre-event planning
│   │   ├── components/
│   │   │   ├── dashboard/            # Layout, controls, stats
│   │   │   ├── visualization/        # VenueMap, ZoneList
│   │   │   ├── charts/               # CrowdFlowChart, density viz
│   │   │   ├── alerts/               # AlertPanel
│   │   │   ├── notifications/        # StaffNotifications
│   │   │   └── ui/                   # shadcn components
│   │   ├── hooks/                    # useSimulation, useWebSocket
│   │   ├── lib/                      # API client, utils
│   │   └── types/                    # TypeScript interfaces
│   └── public/
│
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI entry point
│   │   ├── api/routes/
│   │   │   ├── simulation.py         # Simulation endpoints
│   │   │   ├── data_import.py        # CSV upload endpoints
│   │   │   ├── venues.py             # Venue data
│   │   │   └── alerts.py             # Alert endpoints
│   │   ├── models/                   # Pydantic models
│   │   ├── engine/
│   │   │   ├── simulation.py         # Hybrid agent-flow model
│   │   │   ├── risk_analyzer.py      # Bottleneck detection
│   │   │   ├── recommender.py        # AI recommendations
│   │   │   ├── transport.py          # LRT/bus integration
│   │   │   ├── evacuation.py         # Emergency simulation
│   │   │   └── facilities.py         # Restroom/parking
│   │   ├── services/
│   │   │   └── data_store.py         # Uploaded data storage
│   │   ├── data/                     # Data generation
│   │   └── scenarios/                # Demo scenario configs
│   └── data/venues/                  # Venue JSON definitions
```

## API Endpoints

### Simulation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/simulation/scenarios` | GET | List all scenarios (demo + custom) |
| `/api/simulation/start` | POST | Start a simulation |
| `/api/simulation/step/{id}` | POST | Advance simulation by N steps |
| `/api/simulation/{id}/state` | GET | Get current simulation state |
| `/api/simulation/{id}/reset` | POST | Reset simulation |
| `/ws/simulation/{id}` | WS | Real-time simulation updates |

### Data Import

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/data/upload/ticketing` | POST | Upload ticketing CSV |
| `/api/data/upload/transport` | POST | Upload transport schedule |
| `/api/data/upload/schedule` | POST | Upload event phases |
| `/api/data/templates/{type}` | GET | Download CSV template |
| `/api/data/sample/{type}` | GET | Generate sample data |
| `/api/data/scenarios` | GET | List custom scenarios |

### Venues & Alerts

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/venues` | GET | List all venues |
| `/api/venues/{id}` | GET | Get venue details |
| `/api/alerts/{id}` | GET | Get active alerts |

## Simulation Algorithm

The system uses a **hybrid approach**:

- **Agent-based** for < 5,000 attendees
  - Social Force Model for realistic pedestrian behavior
  - Individual decision-making and route choice

- **Flow-based** for >= 5,000 attendees
  - Fluid dynamics for aggregate crowd patterns
  - Computationally efficient for large events

### Density Thresholds (Fruin's Level of Service)

| Level | Density | Color | Description |
|-------|---------|-------|-------------|
| Safe | < 0.5/m² | Green | Comfortable movement |
| Moderate | 0.5-2.0/m² | Yellow | Crowded but manageable |
| High | 2.0-4.0/m² | Orange | Movement restricted |
| Critical | > 4.0/m² | Red | Safety risk - immediate action |

## Recommendation Engine

The AI generates specific, actionable recommendations:

### Gate Management
- "Open Gate C at 18:30 to reduce Gate A queue by 40%"
- "Close Gate B temporarily - redirect to Gate D"

### Timing Adjustments
- "Delay South Stand exit by 5 min to prevent LRT overcrowding"
- "Announce staggered exit: North Stand first"

### Transport Coordination
- "Open south exits 3 min before 22:15 LRT departure"

### Facility Management
- "Deploy 2 additional porta-potties near Zone B"
- "Activate overflow parking at 18:30"

## Challenge Requirements Mapping

| Requirement | Implementation |
|-------------|----------------|
| **Ingests Data** | CSV/JSON upload for ticketing, transport, schedules |
| **Simulates Scenarios** | Entry, exit, halftime, evacuation modes |
| **Identifies Risks** | Bottlenecks, overcrowding, parking overflow |
| **Suggests Solutions** | Specific actions with timing & gate names |
| **3+ Scenarios** | 3 demo + unlimited custom scenarios |
| **User-Friendly** | WhatsApp-style notifications, visual alerts |
| **No Hardware** | Uses existing ticketing & schedule data |
| **Innovation** | Transport timing → gate opening strategy |

## Development

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Building for Production

```bash
# Frontend
cd frontend
npm run build

# Backend - use gunicorn for production
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## License

MIT

---

Built with Next.js, FastAPI, and shadcn/ui.
