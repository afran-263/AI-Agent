## Function Calling

Function calling is a mechanism that allows Large Language Models (LLMs) to interact with external functions, APIs, or tools by generating structured function calls rather than just text responses. This enables AI agents to perform real-world actions and retrieve data dynamically.

### Key Concepts

**1. Function Definition**
- Define functions with clear descriptions, parameters, and return types
- Provide context about what each function does
- Include parameter constraints and validation rules

# Function Calling Example in an AI Agent

This example demonstrates how an AI agent uses function calling to retrieve weather information.

---

## Step 1: C# Function Implementation

This is the actual backend function that executes business logic and retrieves data.

```csharp
public class WeatherService
{
    public async Task<WeatherResponse> GetWeatherAsync(
        string location,
        string units = "celsius")
    {
        // Call external weather API

        return new WeatherResponse
        {
            Location = location,
            Temperature = 28,
            Condition = "Sunny",
            Units = units
        };
    }
}
```

---

## Step 2: Tool Definition

The AI model does not see the C# implementation.

Instead, it sees a tool definition that describes:

* Tool name
* Purpose
* Parameters
* Required inputs

```json
{
  "type": "function",
  "function": {
    "name": "get_weather",
    "description": "Get current weather information for a location",
    "parameters": {
      "type": "object",
      "properties": {
        "location": {
          "type": "string",
          "description": "City name"
        },
        "units": {
          "type": "string",
          "enum": ["celsius", "fahrenheit"],
          "description": "Temperature units"
        }
      },
      "required": ["location"]
    }
  }
}
```

### Tool Available to AI

```text
get_weather(location, units)
```

---

## Step 3: User Request

The user asks:

```text
What's the weather in Kochi?
```

---

## Step 4: AI Generates Function Call

The AI determines that it needs to use the `get_weather` tool and extracts the required parameters.

```json
{
  "name": "get_weather",
  "arguments": {
    "location": "Kochi",
    "units": "celsius"
  }
}
```

### What Happened?

* AI selected the appropriate tool
* AI extracted the location from user input
* AI generated the required arguments
* No API call has occurred yet

---

## Step 5: Backend Executes Function

The application receives the tool call and invokes the corresponding C# method.

```csharp
var result = await weatherService.GetWeatherAsync(
    "Kochi",
    "celsius"
);
```

---

## Step 6: Function Returns Data

The function returns structured data to the AI.

```json
{
  "location": "Kochi",
  "temperature": 28,
  "condition": "Sunny",
  "units": "celsius"
}
```

---

## Step 7: AI Generates Final Response

Using the returned data, the AI creates a natural language response.

```text
The current weather in Kochi is sunny with a temperature of 28°C.
```

---

# Complete Function Calling Flow

```text
User
 │
 ▼
"What's the weather in Kochi?"
 │
 ▼
AI Model
 │
 ▼
Tool Selection
(get_weather)
 │
 ▼
Function Call JSON
 │
 ▼
Backend Application
 │
 ▼
GetWeatherAsync()
 │
 ▼
Weather API
 │
 ▼
Weather Data
 │
 ▼
AI Model
 │
 ▼
Natural Language Response
```

---
# API Wrappers

An API Wrapper is a layer of code that sits between the AI agent and an external API.

Instead of allowing the AI agent to directly interact with complex API endpoints, authentication mechanisms, and request formatting, we expose simple functions that internally handle all API communication.

### Without API Wrapper

```text id="nzgqot"
AI Agent
    │
    ▼
HTTP Request
    │
    ▼
HRMS API
```

The agent would need to know:

* API URLs
* Authentication tokens
* Headers
* Request formats
* Error handling

---

### With API Wrapper

```text id="ozuxsx"
AI Agent
    │
    ▼
get_employee_details()
    │
    ▼
API Wrapper
    │
    ▼
HRMS API
```

The agent only interacts with simple functions.

---

# Why Use API Wrappers?

## 1. Simplifies Tool Usage

Instead of exposing:

```http id="x8s5k4"
GET https://hrms.company.com/api/v1/employees/EMP001
```

Expose:

```csharp id="w4u9nh"
GetEmployeeDetails("EMP001")
```

The AI only needs to understand the function.

---

## 2. Hides Implementation Details

The AI does not need to know:

* API endpoints
* Authentication methods
* API keys
* HTTP request construction

All implementation details remain inside the wrapper.

---

## 3. Centralized Error Handling

Without wrappers:

```text id="1h7h80"
Every tool must handle errors separately.
```

With wrappers:

```text id="1hbbvn"
Error handling is implemented once.
```

Example:

```csharp id="pxn5xk"
try
{
    var response = await _httpClient.GetAsync(url);
    response.EnsureSuccessStatusCode();
}
catch (Exception ex)
{
    _logger.LogError(ex.Message);
}
```

---

## 4. Reusability

Multiple AI tools can reuse the same wrapper.

```text id="yq8hb0"
AI Agent
     │
     ├── GetEmployeeDetails
     │
     ├── GetEmployeeTasks
     │
     └── GetEmployeeLeaveBalance
              │
              ▼
         HRMS Wrapper
```

---

## HRMS API Wrapper Example

### Raw API Call

```http id="8wn8av"
GET /employees/EMP001
```

### Wrapper Function

```csharp id="wj15jg"
public async Task<Employee> GetEmployeeDetailsAsync(
    string employeeId)
{
    var response = await _httpClient.GetAsync(
        $"/employees/{employeeId}");

    response.EnsureSuccessStatusCode();

    return await response.Content
        .ReadFromJsonAsync<Employee>();
}
```

The AI never sees the HTTP request.

It only sees:

```text id="1b0b2f"
GetEmployeeDetails(employeeId)
```

---

# API Wrapper in Function Calling

## Tool Definition

```json id="mfg6jx"
{
  "name": "get_employee_details",
  "description": "Get employee details",
  "parameters": {
    "type": "object",
    "properties": {
      "employee_id": {
        "type": "string"
      }
    },
    "required": ["employee_id"]
  }
}
```

---

## AI Generates Function Call

```json id="34k9tz"
{
  "name": "get_employee_details",
  "arguments": {
    "employee_id": "EMP001"
  }
}
```

---

## Backend Calls Wrapper

```csharp id="c5o5um"
var employee =
    await hrmsService.GetEmployeeDetailsAsync(
        "EMP001");
```

---

## Wrapper Calls API

```http id="d3xl7d"
GET /employees/EMP001
```

---

## API Returns

```json id="6e44nm"
{
  "employeeId": "EMP001",
  "name": "John Doe",
  "department": "Engineering"
}
```

---

## AI Responds

```text id="r6n69g"
Employee: John Doe
Department: Engineering
```

---

# Read-Only Tools

Read-only tools are utilities or API endpoints that only retrieve data without modifying any system state. These tools are safe for querying information and do not perform create, update, or delete operations.

## Key Characteristics
* No data modification (no POST/PUT/DELETE actions)
* Safe for repeated calls (idempotent)
* Used for fetching or displaying information
* Typically used in dashboards, reports, and analytics
## Common Examples
* Fetching user profile details
* Retrieving product lists
* Getting transaction history
* Reading configuration settings
* Viewing logs or audit trails
## Benefits
* Improves system safety
* Reduces risk of accidental data corruption
* Easier to cache responses
* Useful for analytics and monitoring systems

---
# API Configuration

API configuration defines how your application communicates with external or internal services.

## Base Configuration Parameters
```
{
  "base_url": "https://api.example.com/v1",
  "api_key": "YOUR_API_KEY",
  "timeout": 5000,
  "retries": 3
}
```
## Key Components
1. Base URL

    The root endpoint for all API requests.

2. Authentication
    
    Used to verify identity and permissions.
    
    * API Key (most common)
    * OAuth 2.0 tokens
    * Bearer tokens

3. Headers

    Used to define request metadata.

4. Timeout

    Defines maximum waiting time for a response.
    
    * Prevents hanging requests

5. Retry Mechanism

    Handles temporary failures.
    
    * Retry count: number of attempts
    * Backoff strategy: exponential delay between retries
  ---

  # Error Handling

Proper error handling ensures your application remains stable and user-friendly when failures occur.

---

## Common HTTP Status Codes

| Code | Meaning | Description |
|------|--------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource successfully created |
| 400 | Bad Request | Invalid input from client |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | No permission to access resource |
| 404 | Not Found | Resource does not exist |
| 500 | Server Error | Internal server failure |

---

## Error Response Format

A standard API error response should look like:

```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The provided user ID is invalid",
    "details": "User ID must be a valid UUID"
  }
}
```
---
## Error Handling Strategy

### 1. Client-Side Validation

    * Validate inputs before sending requests
    * Reduce unnecessary API calls
    
### 2. Try-Catch Blocks
   ```
    try {
      const response = await fetch(url);
      const data = await response.json();
    } catch (error) {
      console.error("API request failed:", error);
    }
   ```
### 3. Graceful Fallbacks

    * Show user-friendly messages when something fails
    * Provide default values when API is unavailable
    
### 4. Logging

    * Log errors for debugging and monitoring
    * Include request ID, timestamp, and endpoint for traceability
