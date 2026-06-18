## HRMS Attendance Agent Voyon

This API integrates with Voyon HRMS to retrieve and update employee attendance information. It reads attendance data from Voyon and writes attendance updates back to the system in real time.

### Available APIs

* **GET /api/hrms/attendance/team**

  * Retrieves the complete team attendance report for a specified date.
  * Includes present, absent, leave, and weekly-off details.

* **GET /api/hrms/attendance/present**

  * Retrieves the list of employees who have checked in and are marked present.

* **GET /api/hrms/attendance/absent**

  * Retrieves the list of employees who are absent on a specified date.

* **POST /api/hrms/attendance/mark**

  * Records employee check-in or check-out attendance in Voyon HRMS.

### Features

* Fetches live attendance data from Voyon HRMS.
* Retrieves team and employee attendance information.
* Identifies present and absent employees.
* Records employee check-in and check-out actions.
* Synchronizes attendance data directly with Voyon HRMS.

