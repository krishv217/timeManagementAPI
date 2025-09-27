# TimeAPI Client

A Python command-line client for the TimeAPI REST service that takes natural language input and returns scheduled tasks in JSON format.

## Features

- 🚀 **Easy to use**: Simple command-line interface
- 📝 **Natural language**: Input tasks in plain English
- 📄 **JSON output**: Automatically saves results to JSON files
- ⏰ **Smart scheduling**: Handles explicit times and priorities
- 🔄 **Full CRUD**: Schedule, view, and clear tasks
- 📊 **Verbose mode**: Detailed output for debugging

## Installation

Make sure you have the required dependencies:

```bash
pip install requests
```

## Usage

### Basic Commands

```bash
# Schedule tasks from natural language
python3 client.py "I have a meeting at 2pm and need to go to the gym"

# Save to specific JSON file
python3 client.py "Schedule my day: breakfast, work, lunch, dinner" --output my_schedule.json

# Show current schedule
python3 client.py --show

# Clear all tasks
python3 client.py --clear

# Verbose output
python3 client.py "I need to call mom" --verbose
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `text` | Text describing tasks to schedule |
| `--output, -o` | Output JSON file name |
| `--show, -s` | Show current schedule |
| `--clear, -c` | Clear all tasks |
| `--url` | API base URL (default: http://localhost:5001) |
| `--verbose, -v` | Verbose output |
| `--help, -h` | Show help message |

### Examples

#### 1. Basic Scheduling
```bash
python3 client.py "I have a meeting at 2pm and need to go to the gym"
```
**Output:**
- Schedules the meeting at exactly 2:00 PM
- Schedules gym at an optimal time
- Saves result to auto-generated JSON file

#### 2. Complex Daily Schedule
```bash
python3 client.py "Schedule my day: breakfast at 8am, work from 9am to 12pm, lunch at 12:30pm, gym at 6pm, dinner at 7pm" --output daily_schedule.json
```

#### 3. View Current Schedule
```bash
python3 client.py --show
```

#### 4. Clear All Tasks
```bash
python3 client.py --clear
```

## JSON Output Format

The client saves results in the following JSON format:

```json
{
  "all_tasks": [
    {
      "name": "Meeting at 2pm",
      "start": "2025-09-27T14:00:00",
      "end": "2025-09-27T15:00:00",
      "start_time_display": "02:00 PM",
      "end_time_display": "03:00 PM",
      "date_display": "September 27, 2025"
    }
  ],
  "new_tasks": [...],
  "extracted_tasks": [
    {
      "name": "Meeting at 2pm",
      "duration_hours": 1.0
    }
  ],
  "original_text": "I have a meeting at 2pm and need to go to the gym"
}
```

## Features

### Smart Time Handling
- **Explicit times**: "Meeting at 2pm" → scheduled at exactly 2:00 PM
- **Time ranges**: "Work from 9am to 12pm" → scheduled for that exact period
- **Optimal times**: "Gym" → scheduled at optimal time (5:00 PM)

### Priority System
- **Priority 0**: User-specified explicit times (highest priority)
- **Priority 1**: Critical events (meetings, appointments)
- **Priority 2**: Essential daily activities (meals, sleep)
- **Priority 3**: Work and important tasks
- **Priority 4**: Health and exercise
- **Priority 5**: Low priority tasks (calls, shopping)

### Conflict Resolution
- Automatically reschedules lower-priority tasks to make room for higher-priority ones
- Maintains chronological order
- Preserves explicit user-specified times

## Error Handling

The client handles various error scenarios:

- **Connection errors**: Checks if the API server is running
- **Invalid input**: Provides helpful error messages
- **File errors**: Handles JSON file creation issues
- **API errors**: Displays server error messages

## Integration

### Python Script Integration
```python
from client import TimeAPIClient

client = TimeAPIClient("http://localhost:5001")
result = client.schedule_tasks("I have a meeting at 2pm")
print(result)
```

### Shell Script Integration
```bash
#!/bin/bash
TEXT="I need to schedule my day"
RESULT=$(python3 client.py "$TEXT" --output schedule.json)
echo "Scheduling complete: $RESULT"
```

## Troubleshooting

### Common Issues

1. **"Cannot connect to TimeAPI"**
   - Make sure the server is running: `python3 app.py`
   - Check the URL: `--url http://localhost:5001`

2. **"No tasks could be extracted"**
   - Try more specific language: "I need to have a meeting at 2pm"
   - Use explicit times: "Meeting at 2pm" instead of "Meeting"

3. **JSON file not created**
   - Check file permissions
   - Ensure directory is writable

### Debug Mode
Use `--verbose` for detailed output:
```bash
python3 client.py "Your text here" --verbose
```

## Examples

Run the example script to see various usage patterns:
```bash
python3 example_usage.py
```

## API Endpoints

The client interacts with these REST API endpoints:

- `GET /health` - Health check
- `POST /schedule` - Schedule new tasks
- `GET /tasks` - Get all tasks
- `DELETE /tasks` - Clear all tasks

## License

This client is part of the TimeAPI project and follows the same license terms.

