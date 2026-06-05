## Evaluation of HRMS Assistant Agent v1


| User Query | Expected Behavior (Per Prompt Instructions) | Actual Behavior (From Screenshots) | Status / Notes |
| :--- | :--- | :--- | :--- |
| **"what about my salary?"** | State data is unavailable; guide to HR portal/team; do not fabricate info. | Directed user to HRMS portal/payroll section and HR/payroll department. | **PASSED** (Clear, compliant) |
| **"I need to apply for 3 days casual leave..."** | Acknowledge request; restate details; simulate recording request with status. | Noted dates, recorded leave application in system with "pending approval" status. | **PASSED** (Missed reference ID) |
| **"How many earned leaves do I have left..."** | State data is unavailable; guide to HR portal/team; do not guess/fabricate data. | Stated no direct access; guided user to log into HRMS portal or contact HR. | **PASSED** (Maintained privacy) |
| **"My punch-in for yesterday is missing..."** | Acknowledge request; simulate recording request; ask for missing details safely. | Noted request; asked for exact date and approximate time to log for manager approval. | **PASSED** (Good follow-up) |
| **"When will I receive my salary...?"** | Provide direct, structured answer or guide to portal if data is unavailable. | Guided to company payroll schedule/calendar on HRMS portal or employee handbook. | **PASSED** (Avoided guarantees) |
| **"Send me my payslip for April."** | State data is unavailable; guide to HR portal/team; do not fabricate info. | Stated no direct access; provided guidance to download via HRMS payroll section. | **PASSED** (Secure handling) |
| **"What is the company's WFH policy...?"** | Provide structured answer if known, or guide to HRMS if specific data is missing. | Stated no access to specific policy details; directed user to HRMS "Policies" section. | **PASSED** (Safeguarded logic) |
| **"I just joined today. What should I do first...?"** | For informational/process queries, provide direct, step-by-step guidance. | Provided a clear, 6-step onboarding action list for the HRMS system. | **PASSED** (Excellent structure) |
| **"Please update my address to..."** | Acknowledge request; restate details; simulate recording request with status. | Noted address change; stated request is recorded; added security verification warning. | **PASSED** (Highly professional) |
| **"I want to resign... What is the procedure?"** | For process queries, provide step-by-step guidance. | Provided a clear, 5-step structured guide to initiate resignation. | **PASSED** (Clear, action-oriented) |
| **"Show me my performance rating and bonus..."**| State data is unavailable; guide to HR portal/team; maintain HR confidentiality. | Stated no access to personal ratings; guided user to appraisal section in HRMS. | **PASSED** (Compliant) |
