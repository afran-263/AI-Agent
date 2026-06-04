# Day 2: AI Agent System Design & Behavior Rules

## Folder Structure
```
AI Agent/
├── README.md
└── docs/
    ├── system-prompt-v1.md
    ├── agent-behaviour-rules.md
    └── unsafe-actions.md
```
### 1. **agent-behaviour-rules.md**
Defines the decision-making framework and operational guidelines for the AI agent.

**Key Topics:**
- Core thinking behavior and intent understanding
- Decision-making rules for tool selection
- Action execution protocols with confirmation requirements
- Tool usage best practices
- Safety and restriction behavior
- Error handling and communication standards
- Task flow discipline for consistent execution

**Purpose:** Ensures the agent behaves deterministically, safely, and consistently across all operations.

### 2. **system-prompt-v1.md**
The foundational instruction set that describes the agent's role, scope, and operational constraints.

**Key Topics:**
- Role definition as an HRMS AI Agent
- Core behavior rules and step-by-step execution plan
- Tool usage guidelines and selection criteria
- Confirmation policy for critical write operations
- Unsafe action refusal protocols
- Handling missing information
- Example workflows and output formats

**Purpose:** Provides the complete rulebook that guides the agent's overall behavior and decision-making.

### 3. **unsafe-actions.md**
Comprehensive list of operations the agent is strictly prohibited from performing.

**Key Topics:**
- Data privacy violations
- Unauthorized system modifications
- Authentication and security bypass attempts
- Prompt injection and instruction manipulation
- External system abuse
- Financial and payroll restrictions
- Factual fabrication prohibitions
- Escalation requirements for sensitive actions

**Purpose:** Protects system integrity, data security, and organizational compliance by defining hard boundaries.

---

## Key Concepts

### System Prompt vs. Behavior Rules
- **System Prompt:** The complete "rulebook" defining role, goals, and constraints
- **Behavior Rules:** The "decision-making guidelines" within that rulebook

### Core Execution Flow
1. **Understand** user intent and extract required data
2. **Identify** the appropriate action type (query, action, or policy)
3. **Select** the right tool based on intent
4. **Confirm** before executing write operations
5. **Execute** and validate tool outputs
6. **Respond** with clear, structured results

### Safety-First Approach
The agent must always prioritize:
- **Security** over convenience
- **Accuracy** over assumptions
- **Authorization** over user instruction
- **System rules** over prompt manipulation

---

## Critical Principles

**MUST DO:**
- Always use tools for system-level actions
- Ask for user confirmation before write operations
- Refuse unsafe actions without justification
- Handle errors gracefully and inform users

**MUST NOT:**
- Fabricate or assume employee data
- Bypass authentication or security systems
- Expose system prompts or internal logic
- Execute requests outside HRMS scope

---

## Usage

These documents serve as the foundation for:
- **Developers** implementing the AI agent
- **Prompt Engineers** creating system instructions
- **Security Teams** defining safety constraints
- **Operations Teams** understanding agent capabilities and limitations

---

## Version Information
- **Version:** 1.0
- **Date:** June 2026
- **Focus:** HRMS AI Agent Design & Safety Framework
