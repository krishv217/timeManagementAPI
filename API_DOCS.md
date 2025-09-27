# TimeAPI Documentation

A powerful REST API for intelligent task scheduling using natural language processing and OpenAI's GPT models.

## 🌐 **Live API**

**Base URL:** `https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app`

## 🚀 **Quick Start**

### **Health Check**
```bash
curl https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app/health
```

### **Schedule Your First Task**
```bash
curl -X POST https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app/schedule \
  -H "Content-Type: application/json" \
  -d '{"text": "I have a meeting at 2pm and need to go to the gym"}'
```

## 📋 **API Endpoints**

### **1. Health Check**
Check if the API is running and healthy.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "message": "TimeAPI is running",
  "status": "healthy"
}
```

---

### **2. Schedule Tasks**
Schedule tasks from natural language input.

**Endpoint:** `POST /schedule`

**Request Body:**
```json
{
  "text": "I have a meeting at 2pm and need to go to the gym"
}
```

**Response:**
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
    },
    {
      "name": "Gym",
      "start": "2025-09-27T17:00:00",
      "end": "2025-09-27T18:00:00",
      "start_time_display": "05:00 PM",
      "end_time_display": "06:00 PM",
      "date_display": "September 27, 2025"
    }
  ],
  "new_tasks": [...],
  "extracted_tasks": [
    {
      "name": "Meeting at 2pm",
      "duration_hours": 1.0
    },
    {
      "name": "Gym",
      "duration_hours": 1.0
    }
  ],
  "original_text": "I have a meeting at 2pm and need to go to the gym"
}
```

---

### **3. Get All Tasks**
Retrieve all scheduled tasks in chronological order.

**Endpoint:** `GET /tasks`

**Response:**
```json
{
  "tasks": [
    {
      "name": "Meeting at 2pm",
      "start": "2025-09-27T14:00:00",
      "end": "2025-09-27T15:00:00",
      "start_time_display": "02:00 PM",
      "end_time_display": "03:00 PM",
      "date_display": "September 27, 2025"
    }
  ],
  "total_count": 1
}
```

---

### **4. Clear All Tasks**
Remove all scheduled tasks.

**Endpoint:** `DELETE /tasks`

**Response:**
```json
{
  "message": "All tasks cleared",
  "tasks": []
}
```

---

### **5. API Information**
Get information about the API and its capabilities.

**Endpoint:** `GET /`

**Response:**
```json
{
  "name": "TimeAPI",
  "version": "1.0.0",
  "description": "Intelligent task scheduling API using natural language processing",
  "endpoints": {
    "health": "GET /health",
    "schedule": "POST /schedule",
    "tasks": "GET /tasks",
    "clear": "DELETE /tasks"
  },
  "example_request": {
    "text": "I have a meeting at 2pm and need to go to the gym"
  },
  "example_response": {
    "tasks": [
      {
        "name": "Meeting at 2pm",
        "start": "2025-09-27T14:00:00",
        "end": "2025-09-27T15:00:00"
      }
    ]
  }
}
```

## 🧠 **Smart Features**

### **1. Explicit Time Priority**
When you specify exact times, the API prioritizes them over optimal scheduling:

```bash
# Input: "I have a meeting at 2pm"
# Result: Meeting scheduled at exactly 2:00 PM
```

### **2. Optimal Time Scheduling**
For tasks without explicit times, the API uses intelligent defaults:

- **Breakfast:** 8:00 AM
- **Lunch:** 12:00 PM  
- **Dinner:** 6:00 PM
- **Gym:** 5:00 PM
- **Work:** 9:00 AM
- **Sleep:** 10:00 PM

### **3. Priority-Based Rescheduling**
The API automatically reschedules lower-priority tasks to accommodate higher-priority ones:

**Priority Levels:**
- **Priority 0:** User-specified explicit times (highest)
- **Priority 1:** Critical events (meetings, appointments, deadlines)
- **Priority 2:** Essential daily activities (meals, sleep)
- **Priority 3:** Work and important tasks
- **Priority 4:** Health and exercise
- **Priority 5:** Low priority tasks (calls, shopping, cleaning)

### **4. Chronological Ordering**
All tasks are automatically sorted by start time (earliest to latest).

### **5. Conflict Resolution**
The API intelligently handles scheduling conflicts by:
- Moving lower-priority tasks to make room
- Finding the next available time slot
- Maintaining realistic break times between tasks

## 📝 **Usage Examples**

### **Basic Scheduling**
```bash
curl -X POST https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app/schedule \
  -H "Content-Type: application/json" \
  -d '{"text": "I need to have breakfast and work on my project"}'
```

### **Complex Daily Schedule**
```bash
curl -X POST https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app/schedule \
  -H "Content-Type: application/json" \
  -d '{"text": "Schedule my day: breakfast at 8am, work from 9am to 12pm, lunch at 12:30pm, gym at 6pm, dinner at 7pm"}'
```

### **Explicit Time Ranges**
```bash
curl -X POST https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app/schedule \
  -H "Content-Type: application/json" \
  -d '{"text": "I have a meeting from 2pm to 3pm and need to call mom at 5pm"}'
```

### **Mixed Priority Tasks**
```bash
curl -X POST https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app/schedule \
  -H "Content-Type: application/json" \
  -d '{"text": "I have a critical meeting at 2pm, need to eat lunch, and want to do laundry"}'
```

## 🐍 **Python Client Usage**

### **Installation**
```bash
# Clone the repository or download client.py
python3 client.py --help
```

### **Basic Usage**
```bash
# Schedule tasks
python3 client.py "I have a meeting at 2pm and need to go to the gym"

# Save to specific file
python3 client.py "Schedule my day" --output my_schedule.json

# Show current schedule
python3 client.py --show

# Clear all tasks
python3 client.py --clear
```

### **Using with Deployed API**
```bash
# Use deployed API
python3 client.py "I have a meeting at 2pm" \
  --url https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app

# With verbose output
python3 client.py "Test API" \
  --url https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app \
  --verbose
```

## 🔧 **Integration Examples**

### **JavaScript/Node.js**
```javascript
const response = await fetch('https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app/schedule', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    text: 'I have a meeting at 2pm and need to go to the gym'
  })
});

const data = await response.json();
console.log(data.all_tasks);
```

### **Python Requests**
```python
import requests

response = requests.post(
    'https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app/schedule',
    json={'text': 'I have a meeting at 2pm and need to go to the gym'}
)

data = response.json()
print(data['all_tasks'])
```

### **cURL**
```bash
curl -X POST https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app/schedule \
  -H "Content-Type: application/json" \
  -d '{"text": "I have a meeting at 2pm and need to go to the gym"}'
```

## 📊 **Response Format**

### **Task Object Structure**
```json
{
  "name": "Task name",
  "start": "2025-09-27T14:00:00",        // ISO 8601 format
  "end": "2025-09-27T15:00:00",          // ISO 8601 format
  "start_time_display": "02:00 PM",      // Human-readable time
  "end_time_display": "03:00 PM",        // Human-readable time
  "date_display": "September 27, 2025"   // Human-readable date
}
```

### **Extracted Task Structure**
```json
{
  "name": "Task name",
  "duration_hours": 1.0
}
```

## ⚠️ **Error Handling**

### **Common Error Responses**

**400 Bad Request:**
```json
{
  "error": "No tasks could be extracted from the text"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error: [error details]"
}
```

### **Error Handling Best Practices**
- Always check response status codes
- Handle JSON parsing errors
- Implement retry logic for network issues
- Validate input text before sending requests

## 🔒 **Rate Limits & Best Practices**

### **Rate Limits**
- No explicit rate limits currently enforced
- Consider implementing client-side rate limiting for production use

### **Best Practices**
- **Keep text concise** but descriptive
- **Use specific times** when possible for better scheduling
- **Batch related tasks** in single requests
- **Handle errors gracefully** in your applications
- **Cache responses** when appropriate

## 🚀 **Advanced Features**

### **Time Range Support**
```bash
# Input: "Work from 9am to 12pm"
# Result: Task scheduled for exact 3-hour duration
```

### **Duration Estimation**
The API automatically estimates task durations based on:
- Task type and complexity
- Natural language context
- Realistic time requirements

### **Multi-Day Scheduling**
Tasks automatically extend to subsequent days when the current day is full.

### **Break Management**
Standard 30-minute breaks are automatically inserted between tasks.

## 📈 **Performance**

- **Response Time:** Typically 2-5 seconds
- **Availability:** 99.9% uptime on Vercel
- **Scalability:** Serverless architecture scales automatically
- **Global CDN:** Fast response times worldwide

## 🛠️ **Development & Testing**

### **Local Development**
```bash
# Clone repository
git clone [repository-url]
cd TimeAPI

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp env.example .env
# Edit .env with your OpenAI API key

# Run locally
python3 app.py
```

### **Testing**
```bash
# Test local API
python3 test_deployment.py

# Test deployed API
python3 test_deployment.py
export DEPLOYED_URL=https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app
python3 test_deployment.py
```

## 📞 **Support & Contributing**

### **Issues & Bug Reports**
- Report issues via GitHub issues
- Include request/response examples
- Provide error messages and logs

### **Feature Requests**
- Submit feature requests via GitHub issues
- Describe use cases and expected behavior
- Consider contributing pull requests

### **Contributing**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 **License**

This project is open source and available under the MIT License.

## 🔗 **Links**

- **Live API:** https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app
- **GitHub Repository:** [Add your repository URL]
- **Documentation:** This file
- **Python Client:** `client.py`

---

**TimeAPI** - Intelligent task scheduling made simple! 🚀


