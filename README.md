# TimeAPI - Task Scheduling Service

A Python API that analyzes text input to extract tasks and schedule them optimally throughout the day.

## Features

- Extracts tasks from natural language text using OpenAI GPT
- Estimates task durations intelligently
- Schedules tasks with optimal timing and breaks
- Returns structured JSON with start/end times
- Handles multi-day scheduling automatically

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key in the `app.py` file (already configured)

## Usage

### Start the server:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

### API Endpoints

#### POST /schedule
Schedule tasks from text input.

**Request:**
```json
{
    "text": "I have an ML project and want to go to the gym"
}
```

**Response:**
```json
{
    "tasks": [
        {
            "name": "ML project",
            "start": "2024-01-15T09:00:00",
            "end": "2024-01-15T11:00:00"
        },
        {
            "name": "Gym",
            "start": "2024-01-15T11:30:00",
            "end": "2024-01-15T13:00:00"
        }
    ],
    "original_text": "I have an ML project and want to go to the gym",
    "extracted_tasks": [
        {"name": "ML project", "duration_hours": 2.0},
        {"name": "Gym", "duration_hours": 1.5}
    ]
}
```

#### GET /health
Health check endpoint.

#### GET /
API documentation and examples.

## Example Usage

```bash
curl -X POST http://localhost:5000/schedule \
  -H "Content-Type: application/json" \
  -d '{"text": "I need to finish my presentation, go grocery shopping, and call my mom"}'
```

## Scheduling Logic

- Tasks are scheduled during work hours (9 AM - 6 PM)
- 30-minute breaks between tasks
- Multi-day scheduling for tasks that don't fit in one day
- Intelligent duration estimation based on task type

