# Error Handling

Error handling is the process of detecting, managing, and responding to errors so that the application does not crash and users receive meaningful responses.

### Example

```csharp
var employee = _dataService.GetEmployeeById(id);
```

If the employee does not exist, the API should return an appropriate response instead of throwing an unhandled exception.

---

## Why Error Handling is Important

Without Error Handling:

```text
User Request
    ↓
Error Occurs
    ↓
Application Crashes
```

With Error Handling:

```text
User Request
    ↓
Error Occurs
    ↓
Catch Error
    ↓
Return Meaningful Response
```

### Benefits

- Prevents application crashes
- Improves user experience
- Simplifies debugging
- Provides meaningful API responses
- Improves application reliability

---

# Types of Error Handling

## 1. Validation Errors (400 Bad Request)

Used when the client sends invalid input.

### Example

```csharp
if (request == null ||
    request.EmployeeId <= 0 ||
    string.IsNullOrWhiteSpace(request.Title))
{
    return BadRequest();
}
```

### Invalid Request

```json
{
  "employeeId": 0
}
```

### Response

```json
{
  "success": false,
  "message": "Invalid task request."
}
```

### HTTP Status

```http
400 Bad Request
```

---

## 2. Resource Not Found Errors (404 Not Found)

Used when the requested resource does not exist.

### Example

```csharp
var employee = _dataService.GetEmployeeById(id);

if (employee == null)
{
    return NotFound();
}
```

### Request

```http
GET /api/hrms/employees/999
```

### Response

```json
{
  "success": false,
  "message": "No employee found with ID 999"
}
```

### HTTP Status

```http
404 Not Found
```

---

## 3. Unexpected Errors (500 Internal Server Error)

Used when an unhandled exception occurs.

### Example

```csharp
catch (Exception ex)
{
    logger.LogError(ex, ex.Message);
}
```

### Response

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

### HTTP Status

```http
500 Internal Server Error
```

---

# Global Exception Handling Middleware

Middleware catches unhandled exceptions before they crash the application.

## Flow

```text
Request
   ↓
Middleware
   ↓
Controller
   ↓
Service
```

If an exception occurs:

```text
Request
   ↓
Controller
   ↓
Exception Thrown
   ↓
Middleware Catches Exception
   ↓
Logs Error
   ↓
Returns 500 Response
```

### Example

```csharp
app.Use(async (context, next) =>
{
    try
    {
        await next();
    }
    catch (Exception ex)
    {
        logger.LogError(ex, ex.Message);

        context.Response.StatusCode = 500;

        await context.Response.WriteAsJsonAsync(new
        {
            error = "Internal Server Error",
            message = ex.Message
        });
    }
});
```

---

# HTTP Status Codes

| Status Code | Meaning |
|------------|----------|
| 200 | OK (Success) |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |

---

# Logging Errors

Errors should be logged to help diagnose issues.

### Example

```csharp
logger.LogError(
    ex,
    "Unhandled exception occurred: {Message}",
    ex.Message);
```

### Sample Log

```text
✗ [ERROR]
Unhandled exception:
Object reference not set to an instance of an object
```

---

# Best Practices

## Validate Inputs

```csharp
if (request == null)
{
    return BadRequest();
}
```

## Verify Resources Exist

```csharp
if (employee == null)
{
    return NotFound();
}
```

## Return Proper Status Codes

```csharp
return Ok();          // 200
return Created();     // 201
return BadRequest();  // 400
return NotFound();    // 404
```

## Log Exceptions

```csharp
logger.LogError(ex, ex.Message);
```

## Use Global Exception Middleware

Avoid repeating try-catch blocks in every controller.

Instead, handle exceptions centrally using middleware.

---

# HRMS Project Error Handling Summary

| Scenario | Status Code | Response |
|----------|------------|----------|
| Invalid Request Data | 400 | Bad Request |
| Employee Not Found | 404 | Not Found |
| Task Not Found | 404 | Not Found |
| Attendance Validation Failure | 400 | Bad Request |
| Unhandled Exception | 500 | Internal Server Error |

---
