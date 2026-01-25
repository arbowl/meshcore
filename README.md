# MeshCore

A hexagonal architecture implementation for Meshtastic network monitoring and event processing.

## What is this?

MeshCore is an event-sourcing system for Meshtastic mesh networks. The core ingests events from Meshtastic devices, stores them in an event log, projects them into queryable state, and publishes them via MQTT for downstream consumers.

The project demonstrates clean architecture principles by separating business logic from infrastructure concerns. Event ingestion, storage, and state management form the core, while UIs and external integrations live at the edges as adapters.

## Setup

This project uses `uv` for dependency management.

Install dependencies:
```bash
uv sync
```

## Running the Service

MeshCore supports both interactive and CLI modes for flexible configuration.

### Interactive Mode (Beginner-Friendly)

Run without arguments to get guided prompts:
```bash
python -m meshcore.main
```

You'll be prompted to choose:
- Event source (Mock, Serial USB, or TCP/IP)
- Device configuration
- MQTT settings

### CLI Mode (Automation & Scripts)

Use command-line arguments for scripting and automation:

```bash
# Mock data for testing
python -m meshcore.main --source mock --mock-interval 1.5

# Real device via USB (auto-detect)
python -m meshcore.main --source serial

# Real device via USB (specific port)
python -m meshcore.main --source serial --device COM3

# Real device via TCP/IP network
python -m meshcore.main --source tcp --tcp-host 192.168.1.100

# Disable MQTT (console logging only)
python -m meshcore.main --source mock --no-mqtt

# Custom MQTT broker
python -m meshcore.main --source serial --mqtt-host mqtt.local

# Show all options
python -m meshcore.main --help
```

Or use the installed script:
```bash
uv run meshtastic-hexagonal --source mock
```

### What It Does

The service will:
- Connect to a Meshtastic device (or use mock data)
- Store events in `events.db`
- Project state to `state.db`
- Publish events to MQTT (localhost:1883 by default)

You'll need an MQTT broker running. For example, using Mosquitto:
```bash
mosquitto -v
```

## Architecture

The project follows hexagonal (ports and adapters) architecture:

```
┌─────────────────────┐
│   Domain Models     │  Pure data structures
└──────────┬──────────┘
           │
┌──────────V──────────┐
│  Application Core   │  Business logic
│  - Event ingestion  │  - Services
│  - State projection │  - Ports (interfaces)
└──────────┬──────────┘
           │
┌──────────V──────────┐
│      Adapters       │  Infrastructure
│  - Meshtastic       │  - Storage (SQLite)
│  - MQTT             │  - UIs (Web, TUI)
└─────────────────────┘
```

Core principles:
- Events are immutable and stored in append-only log
- State is a projection from the event stream
- All external dependencies implement port interfaces
- Business logic has no knowledge of infrastructure

Key components:

**Domain** (`domain/models.py`): Core data structures - MeshEvent, NodeState, etc.

**Application** (`application/`):
- Services coordinate event flow
- Ports define interfaces for external systems
- State projection builds queryable views from events

**Adapters** (`adapters/`):
- Meshtastic: Serial, TCP/IP, and mock data sources
- Storage: SQLite implementations of event and state stores
- PubSub: MQTT event publishing
- UI: Web dashboard and terminal UI

## Available UIs

Two user interfaces are provided as adapters:

**Terminal UI**
```bash
uv run meshcore-tui
```

Read-only terminal interface showing live node status.

**Web Dashboard**
```bash
uv run meshcore-web
```

Full-featured web UI at http://localhost:5000 with:
- Real-time node monitoring
- Message history and search
- Message composition and sending
- Telemetry visualization
- Network analytics

The web UI is read-only by default (uses MockCommander). To enable sending, modify `web_main.py` to use `MeshtasticCommander` with your device.

## Extending

The architecture makes it straightforward to add new capabilities:

**New event sources**: Implement the `EventSource` port. See `adapters/meshtastic/mock.py` for an example.

**New storage backends**: Implement `EventStore` or `StateStore` ports. Current SQLite implementations are in `adapters/storage/`.

**New publishers**: Implement `EventPublisher`. See `adapters/pubsub/mqtt.py`.

**New UIs**: Query the state store or event store. See `adapters/ui/` for examples.

**New commands**: Implement `MeshCommandPort` for different communication methods.

Common extensions:
- CSV/JSON export adapters for data analysis
- Webhook publishers for external systems
- Grafana dashboards (MQTT is already available)
- Map views using position data
- Alert systems based on telemetry thresholds

The event store supports replay, making it possible to reprocess events with new projections or analytics without re-collecting data.

## Project Structure

```
src/meshcore/
├── domain/           # Core models
├── application/      # Business logic and ports
│   ├── services.py
│   ├── ports.py
│   ├── state_projection.py
│   ├── message_service.py
│   └── telemetry_service.py
└── adapters/         # Infrastructure
    ├── meshtastic/   # Device communication
    ├── storage/      # Persistence
    ├── pubsub/       # Event publishing
    └── ui/           # User interfaces
```

## Requirements

- Python 3.12+
- MQTT broker (Mosquitto recommended)
- Meshtastic device (optional - mock source available)

See `pyproject.toml` for full dependency list.
