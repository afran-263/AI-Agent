"""LangGraph tool definitions for the Attendance Agent.

Each tool is decorated with @tool and receives the JWT token + employee_id
from the LangGraph RunnableConfig — they are NEVER taken from model arguments,
preventing prompt-injection attacks from accessing another user's data.
"""
from __future__ import annotations

import calendar as _cal
import json
import logging
import re
from datetime import date
from typing import Optional

from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from src.api.hrms_client import HrmsClient, HrmsApiError

logger = logging.getLogger(__name__)


def _today() -> str:
    return date.today().isoformat()


def _get_auth(config: RunnableConfig) -> tuple[str, int]:
    """Extract jwt_token and employee_id from graph config."""
    cfg = config.get("configurable", {})
    jwt_token: str = cfg.get("jwt_token", "")
    employee_id: int = cfg.get("employee_id", 0)
    if not jwt_token:
        raise ValueError("No JWT token in graph config — user is not authenticated.")
    return jwt_token, employee_id


def _safe_json(data) -> str:
    """Serialize API response to JSON string for the LLM."""
    try:
        return json.dumps(data, ensure_ascii=False, default=str)
    except Exception:
        return str(data)


def _extract_emp_list(data) -> list:
    """Normalise team-attendance API response to a flat list of employee dicts.

    Voyon returns a ReturnModel:
      { "Response": { "EmployeeDetails": [...], "ReportedEmployees": N, ... } }
    """
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []

    # TeamAttendanceSummary — employees are nested here
    for key in ("EmployeeDetails", "employeeDetails"):
        inner = data.get(key)
        if isinstance(inner, list):
            return inner

    # ReturnModel wrapper or other nested containers
    for key in ("Response", "response", "data", "Data",
                "employees", "Employees", "teamAttendance"):
        inner = data.get(key)
        if inner is None:
            continue
        if isinstance(inner, list):
            return inner
        if isinstance(inner, dict):
            nested = _extract_emp_list(inner)
            if nested:
                return nested

    return []


def _extract_summary_counts(data) -> dict | None:
    """Read pre-computed counts from TeamAttendanceSummary if present."""
    if not isinstance(data, dict):
        return None
    inner = data.get("Response") or data.get("response") or data
    if not isinstance(inner, dict):
        return None
    if "EmployeeDetails" not in inner and "employeeDetails" not in inner:
        return None
    return {
        "Present": inner.get("ReportedEmployees", 0),
        "Leave": inner.get("OnLeave", 0),
        "WeeklyOff/Holiday": inner.get("onWeeklyOff", 0),
        "Absent": inner.get("NotReported", 0),
    }


def _emp_status(emp: dict) -> str:
    """Derive status from TeamAttendanceViewModel boolean flags."""
    if emp.get("IsLeave") or emp.get("isLeave"):
        return "Leave"
    if emp.get("IsPublicHoliday") or emp.get("isPublicHoliday"):
        return "Holiday"
    if emp.get("IsWeeklyOff") or emp.get("isWeeklyOff"):
        return "WeeklyOff"
    checkin = emp.get("CheckinTime") or emp.get("checkinTime")
    is_absent = emp.get("IsAbsent") if emp.get("IsAbsent") is not None else emp.get("isAbsent")
    if is_absent is False or checkin:
        return "Present"
    status_str = str(emp.get("Status", emp.get("status", ""))).strip()
    if status_str:
        return status_str
    return "Absent"


def _extract_numeric_id(emp: dict) -> int | None:
    """
    Safely extract the numeric employee ID from a search result dict.

    Tries EmployeeId / employeeId first (always the real database PK),
    then falls back to Id / id only if the value is actually numeric.
    Using explicit None checks instead of `or` prevents 0 (falsy) from
    causing the chain to fall through to string codes like 'dcfv'.
    """
    for key in ("EmployeeId", "employeeId"):
        val = emp.get(key)
        if val is not None:
            try:
                result = int(val)
                if result > 0:
                    return result
            except (ValueError, TypeError):
                pass
    # Only use Id/id if it looks numeric — employee codes ('dcfv') are skipped
    for key in ("Id", "id"):
        val = emp.get(key)
        if val is not None:
            try:
                result = int(val)
                if result > 0:
                    return result
            except (ValueError, TypeError):
                pass
    return None


def _employee_matches(emp: dict, query_lower: str) -> bool:
    """Return True if the employee dict matches the search query."""
    name = str(
        emp.get("EmployeeName") or emp.get("employeeName") or
        emp.get("FullName") or emp.get("fullName") or
        emp.get("Name") or emp.get("name") or ""
    ).lower()
    code = str(
        emp.get("EmployeeCode") or emp.get("employeeCode") or
        emp.get("Code") or emp.get("code") or ""
    ).lower()
    numeric_id = _extract_numeric_id(emp)
    eid = str(numeric_id) if numeric_id else ""
    return query_lower in name or query_lower in code or eid == query_lower


def _emp_display_name(emp: dict) -> str:
    """Extract a display name from a team-attendance or search employee dict."""
    for key in (
        "EmployeeName", "employeeName", "FullName", "fullName",
        "Name", "name", "ShortName", "shortName",
    ):
        val = emp.get(key)
        if val and str(val).strip():
            return str(val).strip()
    return "Unknown"


def _normalize_team_employee(emp: dict) -> dict:
    """Normalize HRMS employee record to a consistent id + name shape for lists."""
    emp_id = _extract_numeric_id(emp)
    return {
        "employee_id": emp_id,
        "employee_name": _emp_display_name(emp),
        "employee_code": (
            emp.get("EmployeeCode") or emp.get("employeeCode") or
            emp.get("Code") or emp.get("code")
        ),
        "status": _emp_status(emp),
        "check_in": emp.get("CheckinTime") or emp.get("checkinTime"),
        "check_out": emp.get("CheckOutTime") or emp.get("checkOutTime"),
        "department": emp.get("EmployeeCategory") or emp.get("employeeCategory"),
        "location": emp.get("Location") or emp.get("location"),
    }


def _normalize_employee_list(employees: list) -> list[dict]:
    """Normalize a list of raw HRMS employee dicts."""
    return [
        _normalize_team_employee(e)
        for e in employees
        if isinstance(e, dict)
    ]


def format_employee_list_markdown(
    employees: list[dict],
    *,
    title: str,
    date_str: str = "",
    empty_message: str = "No employees found.",
) -> str:
    """Build a markdown table with Employee ID and Name for team list responses."""
    if not employees:
        date_part = f" on **{date_str}**" if date_str else ""
        return f"{title}{date_part}\n\n{empty_message}"

    lines = [title]
    if date_str:
        lines.append(f"**Date:** {date_str}")
    lines.append("")
    lines.append(f"**Total:** {len(employees)}")
    lines.append("")
    lines.append("| Employee ID | Name |")
    lines.append("|------------:|------|")
    for emp in employees:
        eid = emp.get("employee_id") or "—"
        name = emp.get("employee_name") or "—"
        lines.append(f"| {eid} | {name} |")
    return "\n".join(lines)


def format_tool_list_response(tool_name: str, raw_json: str) -> str | None:
    """
    Build a deterministic markdown employee list from present/absent/search tool JSON.
    Returns None if the tool result is not a list-style response.
    """
    try:
        data = json.loads(raw_json)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(data, dict) or data.get("error"):
        return None

    date_str = str(data.get("date") or "")

    if tool_name == "get_present_employees":
        if "present_count" not in data:
            return None
        employees = data.get("employees") or []
        return format_employee_list_markdown(
            employees,
            title="### Employees present in your team",
            date_str=date_str,
            empty_message="No employees are marked present for this date.",
        )

    if tool_name == "get_absent_employees":
        if "absent_count" not in data:
            return None
        employees = data.get("employees") or []
        return format_employee_list_markdown(
            employees,
            title="### Employees absent / not reported in your team",
            date_str=date_str,
            empty_message="No absent employees for this date.",
        )

    if tool_name == "search_employee":
        if "matches" not in data:
            return None
        matches = data.get("matches") or []
        query = data.get("query") or ""
        return format_employee_list_markdown(
            matches,
            title=f"### Search results for \"{query}\"",
            date_str=date_str if data.get("date") else "",
            empty_message=f"No employees found matching \"{query}\".",
        )

    if tool_name == "get_team_employee_list":
        if "total_count" not in data:
            return None
        employees = data.get("employees") or []
        return format_employee_list_markdown(
            employees,
            title="### All employees in your team",
            date_str=date_str,
            empty_message="No employees found in your team for this date.",
        )

    return None


def _attendance_field(att: dict, *keys: str) -> str | None:
    for key in keys:
        val = att.get(key)
        if val is not None and str(val).strip() and str(val).strip() != "--:--":
            return str(val).strip()
    return None


def _parse_attendance_blob(att) -> dict[str, str | None]:
    """Extract status/times from AttendanceBasedOnDate or team-attendance record."""
    if isinstance(att, str):
        try:
            att = json.loads(att)
        except (json.JSONDecodeError, TypeError):
            return {}
    if not isinstance(att, dict):
        return {}

    inner = att.get("Response") or att.get("response")
    if isinstance(inner, dict):
        att = inner

    status = _attendance_field(att, "Status", "status", "StatusCode", "statusCode")
    if not status and isinstance(att, dict):
        derived = _emp_status(att)
        if derived not in ("Absent",):
            status = derived
        elif att.get("IsAbsent") is True or att.get("isAbsent") is True:
            status = "Absent"
        elif att.get("CheckinTime") or att.get("checkinTime"):
            status = "Present"

    return {
        "status": status,
        "check_in": _attendance_field(
            att, "CheckinTime", "checkinTime", "FirstCheckIn", "firstCheckIn", "CheckIn"
        ),
        "check_out": _attendance_field(
            att, "CheckOutTime", "checkOutTime", "LastCheckOut", "lastCheckOut", "CheckOut"
        ),
        "worked_hours": _attendance_field(att, "WorkedHours", "workedHours"),
    }


def format_my_attendance_response(raw_json: str) -> str | None:
    """Plain-text response for the logged-in user's attendance — no tables."""
    try:
        data = json.loads(raw_json)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(data, dict):
        return None
    if data.get("error"):
        return f"I couldn't retrieve your attendance: {data['error']}"
    if "attendance" not in data:
        return None

    date_str = str(data.get("date") or _today())
    fields = _parse_attendance_blob(data.get("attendance"))

    lines = [f"**Your attendance for {date_str}**", ""]
    status = fields.get("status")
    if status:
        lines.append(f"Status: **{status}**")
    if fields.get("check_in"):
        lines.append(f"Check-in: {fields['check_in']}")
    if fields.get("check_out"):
        lines.append(f"Check-out: {fields['check_out']}")
    if fields.get("worked_hours"):
        lines.append(f"Worked hours: {fields['worked_hours']}")

    if len(lines) <= 2:
        lines.append("No attendance record found for today yet.")

    return "\n".join(lines)


def format_employee_attendance_details_response(raw_json: str) -> str | None:
    """Plain-text attendance details for a specific employee on a date."""
    try:
        data = json.loads(raw_json)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(data, dict):
        return None
    if data.get("error"):
        return f"I couldn't retrieve attendance details: {data['error']}"
    if "attendance" not in data:
        return None

    date_str = str(data.get("date") or _today())
    emp_name = data.get("employee_name") or f"Employee {data.get('employee_id', '')}"
    fields = _parse_attendance_blob(data.get("attendance"))

    lines = [f"**Attendance for {emp_name} on {date_str}**", ""]
    status = fields.get("status")
    if status:
        lines.append(f"Status: **{status}**")
    if fields.get("check_in"):
        lines.append(f"Check-in: {fields['check_in']}")
    if fields.get("check_out"):
        lines.append(f"Check-out: {fields['check_out']}")
    if fields.get("worked_hours"):
        lines.append(f"Worked hours: {fields['worked_hours']}")

    if len(lines) <= 2:
        lines.append("No attendance record found for this date yet.")

    return "\n".join(lines)


def try_format_employee_detail_from_turn(
    tool_results: dict | None,
    turn_messages: list,
) -> str | None:
    """Format a specific employee's attendance details as plain text."""
    for tool_name, raw in (tool_results or {}).items():
        if tool_name == "get_employee_attendance_details":
            formatted = format_employee_attendance_details_response(raw)
            if formatted:
                return formatted

    from langchain_core.messages import AIMessage, ToolMessage

    tool_names_by_id: dict[str, str] = {}
    for msg in turn_messages:
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                tc_id = tc.get("id")
                tc_name = tc.get("name")
                if tc_id and tc_name:
                    tool_names_by_id[tc_id] = tc_name

    for msg in turn_messages:
        if not isinstance(msg, ToolMessage) or not msg.content:
            continue
        tool_name = tool_names_by_id.get(msg.tool_call_id, "")
        if tool_name == "get_employee_attendance_details":
            formatted = format_employee_attendance_details_response(str(msg.content))
            if formatted:
                return formatted

    return None


def _normalize_date_str(val) -> str:
    if not val:
        return ""
    s = str(val)
    if "T" in s:
        s = s.split("T")[0]
    return s[:10]


def _status_label_from_detail(det) -> str:
    """Map a daily attendance record to Present, Absent, Leave, etc."""
    if not isinstance(det, dict):
        return "Unknown"
    inner = det.get("Response") or det.get("response")
    if isinstance(inner, dict):
        det = inner

    day_type = str(det.get("DayType") or det.get("dayType") or "").strip()
    status = str(
        det.get("AttendanceStatus") or det.get("attendanceStatus") or
        det.get("Status") or det.get("status") or ""
    ).strip()
    leave = str(det.get("LeaveTypeName") or det.get("leaveTypeName") or "").strip()

    if day_type.lower() in ("holiday", "publicholiday"):
        return "Holiday"
    if day_type.lower() in ("weeklyoff", "weekoff", "weekly off", "nightoff"):
        return "Weekly Off"
    if leave or status.lower() in ("leave", "halfday leave", "half day leave"):
        return "Leave"
    if status.lower() in ("present", "halfdaypresent", "half day present", "p"):
        return "Present"
    if status.lower() in ("absent", "a", "notyetreported", "not reported"):
        return "Absent"
    if det.get("IsPresent") is True or det.get("isPresent") is True:
        return "Present"
    if det.get("IsAbsent") is True or det.get("isAbsent") is True:
        return "Absent"
    if det.get("CheckinTime") or det.get("checkinTime"):
        return "Present"
    if status:
        return status
    return "Unknown"


def _extract_history_days(data: dict) -> list[dict]:
    """Parse monthly or day-by-day history JSON into [{date, status}, ...]."""
    if data.get("daily_records"):
        return list(data["daily_records"])

    rows: list[dict] = []
    attendance = data.get("attendance")

    if isinstance(attendance, list) and attendance:
        first = attendance[0] if isinstance(attendance[0], dict) else {}
        if "details" in first or (first.get("date") and "Date" not in first):
            for rec in attendance:
                if not isinstance(rec, dict):
                    continue
                rows.append({
                    "date": _normalize_date_str(rec.get("date")),
                    "status": _status_label_from_detail(rec.get("details") or {}),
                })
            return sorted(rows, key=lambda r: r["date"])

        for rec in attendance:
            if not isinstance(rec, dict):
                continue
            d = _normalize_date_str(rec.get("Date") or rec.get("date"))
            if d:
                rows.append({"date": d, "status": _status_label_from_detail(rec)})
        if rows:
            return sorted(rows, key=lambda r: r["date"])

    if isinstance(attendance, dict):
        inner = attendance.get("Response") or attendance.get("response") or attendance
        if isinstance(inner, dict):
            monthly = inner.get("MonthlyAttendance") or inner.get("monthlyAttendance") or []
            for rec in monthly:
                if not isinstance(rec, dict):
                    continue
                d = _normalize_date_str(rec.get("Date") or rec.get("date"))
                if d:
                    rows.append({"date": d, "status": _status_label_from_detail(rec)})

    return sorted(rows, key=lambda r: r["date"])


def _filter_days_through_today(
    days: list[dict],
    month: int | None,
    year: int | None,
) -> list[dict]:
    """For the current calendar month, keep only dates up to today."""
    if not days or month is None or year is None:
        return days
    try:
        month_i, year_i = int(month), int(year)
    except (ValueError, TypeError):
        return days

    today = date.today()
    if month_i != today.month or year_i != today.year:
        return days

    cutoff = today.isoformat()
    return [d for d in days if (d.get("date") or "") <= cutoff]


def _history_days_for_display(data: dict) -> list[dict]:
    """Extract daily rows and limit current-month views to today."""
    days = _extract_history_days(data)
    return _filter_days_through_today(days, data.get("month"), data.get("year"))


def _summary_from_days(days: list[dict]) -> dict:
    counts = {"present": 0, "absent": 0, "leave": 0, "holiday": 0, "weekoff": 0}
    for row in days:
        label = (row.get("status") or "").lower()
        if label == "present":
            counts["present"] += 1
        elif label == "absent":
            counts["absent"] += 1
        elif label == "leave":
            counts["leave"] += 1
        elif label == "holiday":
            counts["holiday"] += 1
        elif label in ("weekly off", "weekoff"):
            counts["weekoff"] += 1
    counts["total_days"] = len(days)
    return counts


def _enrich_history_payload(payload: dict) -> dict:
    """Add normalized daily_records and summary to history tool JSON."""
    days = _filter_days_through_today(
        _extract_history_days(payload),
        payload.get("month"),
        payload.get("year"),
    )
    payload["daily_records"] = days
    if days:
        payload["summary"] = _summary_from_days(days)
    return payload


def _history_period_label(month, year, days: list[dict]) -> str:
    """Human-readable period, including 'till today' for the current month."""
    if not month or not year:
        return ""
    try:
        month_i, year_i = int(month), int(year)
        base = f"{_cal.month_name[month_i]} {year_i}"
    except (ValueError, TypeError):
        return f"{month}/{year}"

    today = date.today()
    if month_i == today.month and year_i == today.year:
        return f"{base} (till {today.strftime('%d %b %Y')})"
    if days:
        return f"{base} (1–{len(days)} days)"
    return base


def format_monthly_attendance_summary_response(raw_json: str) -> str | None:
    """Month-to-date summary counts + per-day Present/Absent table."""
    try:
        data = json.loads(raw_json)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(data, dict):
        return None
    if data.get("error"):
        return f"I couldn't retrieve attendance summary: {data['error']}"
    if "attendance" not in data and "daily_records" not in data:
        return None

    days = _history_days_for_display(data)
    if not days:
        return None

    month = data.get("month")
    year = data.get("year")
    emp_name = data.get("employee_name")
    emp_id = data.get("employee_id")
    who = emp_name or (f"Employee {emp_id}" if emp_id else "Employee")
    period = _history_period_label(month, year, days)
    summary = _summary_from_days(days)
    holiday_off = summary.get("holiday", 0) + summary.get("weekoff", 0)
    total = summary.get("total_days", len(days))

    lines = [f"### Attendance summary — {who}"]
    if period:
        lines.append(f"**Period:** {period}")
    lines.append("")
    lines.append("| Status | Days |")
    lines.append("|--------|-----:|")
    lines.append(f"| Present | {summary.get('present', 0)} |")
    lines.append(f"| Absent | {summary.get('absent', 0)} |")
    lines.append(f"| Leave | {summary.get('leave', 0)} |")
    lines.append(f"| Holiday/Off | {holiday_off} |")
    lines.append(f"| **Total** | **{total}** |")
    lines.append("")
    lines.append("| Date | Status |")
    lines.append("|------|--------|")
    for row in days:
        lines.append(f"| {row.get('date', '—')} | {row.get('status') or '—'} |")

    return "\n".join(lines)


def format_attendance_history_response(raw_json: str) -> str | None:
    """Markdown table: each date marked Present, Absent, Leave, etc."""
    try:
        data = json.loads(raw_json)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(data, dict):
        return None
    if data.get("error"):
        return f"I couldn't retrieve attendance history: {data['error']}"
    if "attendance" not in data and "daily_records" not in data:
        return None

    days = _history_days_for_display(data)
    if not days:
        return None

    month = data.get("month")
    year = data.get("year")
    emp_name = data.get("employee_name")
    emp_id = data.get("employee_id")
    who = emp_name or (f"Employee {emp_id}" if emp_id else "Employee")

    period = _history_period_label(month, year, days)
    summary = _summary_from_days(days)

    lines = [f"### Attendance history — {who}"]
    if period:
        lines.append(f"**Period:** {period}")
    lines.append("")
    lines.append(
        f"**Summary:** Present **{summary.get('present', 0)}** | "
        f"Absent **{summary.get('absent', 0)}** | "
        f"Leave **{summary.get('leave', 0)}** | "
        f"Holiday/Off **{summary.get('holiday', 0) + summary.get('weekoff', 0)}**"
    )
    lines.append("")
    lines.append("| Date | Status |")
    lines.append("|------|--------|")
    for row in days:
        status = row.get("status") or "—"
        lines.append(f"| {row.get('date', '—')} | {status} |")

    return "\n".join(lines)


def try_format_history_from_turn(
    tool_results: dict | None,
    turn_messages: list,
    *,
    summary_style: bool = False,
) -> str | None:
    """Format monthly history — summary table or day-by-day history."""
    formatter = (
        format_monthly_attendance_summary_response
        if summary_style
        else format_attendance_history_response
    )

    for tool_name, raw in (tool_results or {}).items():
        if tool_name == "get_attendance_history":
            formatted = formatter(raw)
            if formatted:
                return formatted

    from langchain_core.messages import AIMessage, ToolMessage

    tool_names_by_id: dict[str, str] = {}
    for msg in turn_messages:
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                tc_id = tc.get("id")
                tc_name = tc.get("name")
                if tc_id and tc_name:
                    tool_names_by_id[tc_id] = tc_name

    for msg in turn_messages:
        if not isinstance(msg, ToolMessage) or not msg.content:
            continue
        tool_name = tool_names_by_id.get(msg.tool_call_id, "")
        if tool_name == "get_attendance_history":
            formatted = formatter(str(msg.content))
            if formatted:
                return formatted

    return None


def wants_monthly_summary_style(user_message: str) -> bool:
    """True when the user asks for a month-to-date summary (not a single-day team summary)."""
    text = (user_message or "").lower()
    if re.search(
        r"\b(this month|current month|month so far|till now|until now|to date)\b",
        text,
    ) and re.search(r"\b(summary|overview|attendance)\b", text):
        return True
    if re.search(r"\battendance summary\b.*\bmonth\b", text):
        return True
    if re.search(r"\bmonth\b.*\battendance summary\b", text):
        return True
    return False


def try_format_my_attendance_from_turn(
    tool_results: dict | None,
    turn_messages: list,
) -> str | None:
    """Format personal attendance as plain text (no table)."""
    for tool_name, raw in (tool_results or {}).items():
        if tool_name == "get_my_attendance_today":
            formatted = format_my_attendance_response(raw)
            if formatted:
                return formatted

    from langchain_core.messages import AIMessage, ToolMessage

    tool_names_by_id: dict[str, str] = {}
    for msg in turn_messages:
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                tc_id = tc.get("id")
                tc_name = tc.get("name")
                if tc_id and tc_name:
                    tool_names_by_id[tc_id] = tc_name

    for msg in turn_messages:
        if not isinstance(msg, ToolMessage) or not msg.content:
            continue
        tool_name = tool_names_by_id.get(msg.tool_call_id, "")
        if tool_name == "get_my_attendance_today":
            formatted = format_my_attendance_response(str(msg.content))
            if formatted:
                return formatted

    return None


def try_format_list_from_turn(
    tool_results: dict | None,
    turn_messages: list,
) -> str | None:
    """Format employee ID + name table from direct tool_results or ReAct ToolMessages."""
    for tool_name, raw in (tool_results or {}).items():
        formatted = format_tool_list_response(tool_name, raw)
        if formatted:
            return formatted

    from langchain_core.messages import AIMessage, ToolMessage

    tool_names_by_id: dict[str, str] = {}
    for msg in turn_messages:
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                tc_id = tc.get("id")
                tc_name = tc.get("name")
                if tc_id and tc_name:
                    tool_names_by_id[tc_id] = tc_name

    for msg in turn_messages:
        if not isinstance(msg, ToolMessage) or not msg.content:
            continue
        raw = str(msg.content)
        tool_name = tool_names_by_id.get(msg.tool_call_id, "")
        if tool_name:
            formatted = format_tool_list_response(tool_name, raw)
            if formatted:
                return formatted
        for name in (
            "get_team_employee_list",
            "get_present_employees",
            "get_absent_employees",
            "search_employee",
        ):
            formatted = format_tool_list_response(name, raw)
            if formatted:
                return formatted

    return None


# ── Tool 1: Get present employees ─────────────────────────────────────────────

@tool
async def get_present_employees(
    date_str: Optional[str] = None,
    reporting_type: int = 0,
    config: RunnableConfig = None,
) -> str:
    """
    Get the list of employees who are PRESENT on a given date.

    Args:
        date_str: Date in YYYY-MM-DD format. Defaults to today if not provided.
        reporting_type: 0 = all team, 1 = direct reports, 2 = indirect reports.

    Returns:
        JSON string with the list of present employees and their check-in/out times.
    """
    token, emp_id = _get_auth(config)
    target_date = date_str or _today()

    try:
        data = await HrmsClient.get_team_attendance(token, emp_id, target_date, reporting_type)
        raw = _extract_emp_list(data)
        present = [e for e in raw if isinstance(e, dict) and _emp_status(e) == "Present"]
        normalized = _normalize_employee_list(present)
        result = {
            "date": target_date,
            "present_count": len(normalized),
            "employees": normalized,
        }
        return _safe_json(result)
    except HrmsApiError as exc:
        logger.error("get_present_employees failed: %s", exc)
        return _safe_json({"error": str(exc)})


# ── Tool 2: Get absent employees ──────────────────────────────────────────────

@tool
async def get_absent_employees(
    date_str: Optional[str] = None,
    reporting_type: int = 0,
    config: RunnableConfig = None,
) -> str:
    """
    Get the list of employees who are ABSENT on a given date.

    Args:
        date_str: Date in YYYY-MM-DD format. Defaults to today if not provided.
        reporting_type: 0 = all team, 1 = direct reports, 2 = indirect reports.

    Returns:
        JSON string with the list of absent employees.
    """
    token, emp_id = _get_auth(config)
    target_date = date_str or _today()

    try:
        data = await HrmsClient.get_team_attendance(token, emp_id, target_date, reporting_type)
        raw = _extract_emp_list(data)
        absent = [
            e for e in raw
            if isinstance(e, dict) and _emp_status(e) not in ("Present", "Holiday", "WeeklyOff")
        ]
        normalized = _normalize_employee_list(absent)
        result = {
            "date": target_date,
            "absent_count": len(normalized),
            "employees": normalized,
        }
        return _safe_json(result)
    except HrmsApiError as exc:
        logger.error("get_absent_employees failed: %s", exc)
        return _safe_json({"error": str(exc)})


# ── Tool 2b: Full team employee list (all statuses) ─────────────────────────────

@tool
async def get_team_employee_list(
    date_str: Optional[str] = None,
    reporting_type: int = 0,
    config: RunnableConfig = None,
) -> str:
    """
    Get ALL employees in the user's team for a date, with attendance status.

    Use when the user asks for:
    - "list of employees", "show all employees", "team roster"
    - "get all details" / "full list" after a team count or summary
    - every team member with their ID, name, and status

    Args:
        date_str: Date in YYYY-MM-DD format. Defaults to today.
        reporting_type: 0 = all team, 1 = direct reports, 2 = indirect reports.

    Returns:
        JSON with every team member (employee_id, employee_name, status, check-in).
    """
    token, emp_id = _get_auth(config)
    target_date = date_str or _today()

    try:
        data = await HrmsClient.get_team_attendance(token, emp_id, target_date, reporting_type)
        raw = _extract_emp_list(data)
        normalized = _normalize_employee_list(raw)
        result = {
            "date": target_date,
            "total_count": len(normalized),
            "employees": normalized,
        }
        return _safe_json(result)
    except HrmsApiError as exc:
        logger.error("get_team_employee_list failed: %s", exc)
        return _safe_json({"error": str(exc)})


# ── Tool 3: Get attendance summary ────────────────────────────────────────────

@tool
async def get_attendance_summary(
    date_str: Optional[str] = None,
    reporting_type: int = 0,
    config: RunnableConfig = None,
) -> str:
    """
    Get TEAM attendance summary (present / absent / on-leave / holiday counts)
    for a given date.

    Use this tool when the user asks for:
    - "Show attendance summary for today"
    - "How many employees are in my team today?"
    - "Attendance overview" or status counts for the team

    Do NOT use this for the logged-in user's own check-in/out only — use
    get_my_attendance_today for that.

    Args:
        date_str: Date in YYYY-MM-DD format. Defaults to today if not provided.
        reporting_type: 0 = all team, 1 = direct reports, 2 = indirect reports.

    Returns:
        JSON string with total_employees and counts by attendance status.
    """
    token, emp_id = _get_auth(config)
    target_date = date_str or _today()

    try:
        data = await HrmsClient.get_team_attendance(token, emp_id, target_date, reporting_type)
        raw = _extract_emp_list(data)
        logger.info("get_attendance_summary: parsed %d employee records", len(raw))

        # Prefer pre-computed counts from TeamAttendanceSummary when available
        summary = _extract_summary_counts(data)
        if summary is None:
            summary = {}
            for emp in raw:
                if not isinstance(emp, dict):
                    continue
                status = _emp_status(emp)
                summary[status] = summary.get(status, 0) + 1

        result = {
            "date": target_date,
            "total_employees": len(raw),
            "summary_by_status": summary,
        }
        return _safe_json(result)
    except HrmsApiError as exc:
        logger.error("get_attendance_summary failed: %s", exc)
        return _safe_json({"error": str(exc)})


# ── Tool 4: Get attendance history ────────────────────────────────────────────

@tool
async def get_attendance_history(
    month: Optional[int] = None,
    year: Optional[int] = None,
    employee_id: Optional[int] = None,
    employee_name: Optional[str] = None,
    config: RunnableConfig = None,
) -> str:
    """
    Get the monthly attendance history (calendar view) for an employee.

    If you know the employee's name but not their ID, pass `employee_name`
    and the tool will automatically search for their ID first.
    If neither name nor ID is provided, returns the logged-in user's history.

    Args:
        month: Month number (1-12). Defaults to current month.
        year: Four-digit year. Defaults to current year.
        employee_id: Target employee's numeric ID (preferred over name).
        employee_name: Employee's name to search for when ID is not known.

    Returns:
        JSON string with daily attendance records for the month.
    """
    token, session_emp_id = _get_auth(config)

    today = date.today()
    target_month = month or today.month
    target_year = year or today.year

    # ── Resolve employee_id from name when only name is available ─────────────
    target_emp = employee_id
    resolved_name: str | None = None

    _SELF_PRONOUNS = {"my", "mine", "i", "me", "myself", "our", "we"}
    if employee_name and employee_name.strip().lower() in _SELF_PRONOUNS:
        employee_name = None

    if not target_emp and employee_name:
        logger.info("get_attendance_history: searching for employee '%s'", employee_name)
        try:
            search_data = await HrmsClient.search_employees(token, employee_name.strip())
            emp_list = _extract_emp_list(search_data)
            if emp_list:
                # Pick the first result (best match from HRMS search)
                first = emp_list[0]
                found_id = _extract_numeric_id(first)
                if found_id:
                    target_emp = found_id
                    resolved_name = (
                        first.get("EmployeeName") or first.get("employeeName") or
                        first.get("FullName") or first.get("fullName") or
                        first.get("Name") or employee_name
                    )
                    logger.info(
                        "get_attendance_history: resolved '%s' → employee_id=%s",
                        employee_name, target_emp,
                    )
                else:
                    return _safe_json({
                        "error": f"Could not find employee named '{employee_name}'. "
                                 "Please check the name or use the employee ID.",
                    })
            else:
                return _safe_json({
                    "error": f"No employee found matching '{employee_name}'. "
                             "Please check the name or use the employee ID.",
                })
        except HrmsApiError as exc:
            logger.warning("get_attendance_history: search failed for '%s': %s", employee_name, exc)
            return _safe_json({
                "error": f"Could not search for employee '{employee_name}': {exc}",
            })

    if not target_emp:
        target_emp = session_emp_id

    # ── Strategy 1: monthly summary endpoint ──────────────────────────────────
    try:
        data = await HrmsClient.get_monthly_attendance(token, target_emp, target_month, target_year)
        return _safe_json(_enrich_history_payload({
            "employee_id": target_emp,
            "employee_name": resolved_name or employee_name,
            "month": target_month,
            "year": target_year,
            "attendance": data,
        }))
    except HrmsApiError as exc:
        logger.warning(
            "get_attendance_history: MonthlyAttendance failed for emp %s (%s) — "
            "falling back to day-by-day AttendanceBasedOnDate",
            target_emp, exc,
        )

    # ── Strategy 2: day-by-day fallback using AttendanceBasedOnDate ───────────
    # Same API that powers the per-day attendance queries (always works).
    today = date.today()
    last_day = _cal.monthrange(target_year, target_month)[1]
    end_day = min(last_day, today.day if (target_year == today.year and target_month == today.month) else last_day)

    daily_records = []
    for day in range(1, end_day + 1):
        day_str = f"{target_year}-{target_month:02d}-{day:02d}"
        try:
            day_data = await HrmsClient.get_attendance_by_date(token, target_emp, day_str)
            daily_records.append({"date": day_str, "details": day_data})
        except HrmsApiError:
            daily_records.append({"date": day_str, "details": None})

    # ── Compute summary counts from the daily records ─────────────────────────
    counts = {"present": 0, "absent": 0, "leave": 0, "holiday": 0, "weekoff": 0, "unknown": 0}
    for rec in daily_records:
        det = rec.get("details") or {}
        day_type = str(det.get("DayType") or det.get("dayType") or "").strip()
        status   = str(det.get("Status")  or det.get("status")  or "").strip()
        leave_name = str(det.get("LeaveTypeName") or det.get("leaveTypeName") or "").strip()

        if day_type.lower() in ("holiday", "publicholiday"):
            counts["holiday"] += 1
        elif day_type.lower() in ("weeklyoff", "weekoff", "weekly off", "week off"):
            counts["weekoff"] += 1
        elif leave_name or status.lower() in ("leave", "halfday leave", "half day leave"):
            counts["leave"] += 1
        elif status.lower() in ("present", "halfdaypresent", "half day present"):
            counts["present"] += 1
        elif status.lower() == "absent":
            counts["absent"] += 1
        else:
            counts["unknown"] += 1

    logger.info(
        "get_attendance_history (day-by-day fallback): fetched %d days for emp %s — %s",
        len(daily_records), target_emp, counts,
    )
    return _safe_json(_enrich_history_payload({
        "employee_id": target_emp,
        "employee_name": resolved_name or employee_name,
        "month": target_month,
        "year": target_year,
        "summary": {
            "total_days": len(daily_records),
            "present": counts["present"],
            "absent": counts["absent"],
            "leave": counts["leave"],
            "holiday": counts["holiday"],
            "weekoff": counts["weekoff"],
        },
        "attendance": daily_records,
    }))


# ── Tool 5: Search employee ───────────────────────────────────────────────────

@tool
async def search_employee(
    query: str,
    date_str: Optional[str] = None,
    config: RunnableConfig = None,
) -> str:
    """
    Search for an employee by name, employee code, or employee ID.

    Tries the dedicated mobile employee search API first; falls back to
    scanning team-attendance data if that fails.

    Args:
        query: Search term — partial name, employee code, or numeric ID.
        date_str: Used only for the team-attendance fallback (YYYY-MM-DD).
                  Defaults to today.

    Returns:
        JSON string with matching employees (id, name, code, department, etc.).
    """
    token, emp_id = _get_auth(config)

    # ── Strategy 1: dedicated mobile search endpoint ──────────────────────────
    try:
        data = await HrmsClient.search_employees(token, query.strip())
        emp_list = _extract_emp_list(data)

        query_lower = query.strip().lower()
        # If the API already filters, keep all; otherwise filter client-side
        if emp_list and _employee_matches(emp_list[0], query_lower):
            matches = emp_list
        else:
            matches = [e for e in emp_list if isinstance(e, dict) and _employee_matches(e, query_lower)]

        logger.info(
            "search_employee (mobile API) query=%r found %d results", query, len(matches)
        )
        normalized = _normalize_employee_list(matches)
        return _safe_json({"query": query, "matches": normalized, "total": len(normalized)})
    except HrmsApiError as exc1:
        logger.warning(
            "search_employee: mobile search API failed (%s) — falling back to team-attendance",
            exc1,
        )

    # ── Strategy 2: team-attendance fallback ──────────────────────────────────
    target_date = date_str or _today()
    try:
        data = await HrmsClient.get_team_attendance(token, emp_id, target_date, 0)
        emp_list = _extract_emp_list(data)

        query_lower = query.strip().lower()
        matches = [e for e in emp_list if isinstance(e, dict) and _employee_matches(e, query_lower)]
        logger.info(
            "search_employee (team-attendance fallback) query=%r date=%s found %d/%d",
            query, target_date, len(matches), len(emp_list),
        )
        normalized = _normalize_employee_list(matches)
        return _safe_json({
            "query": query,
            "date": target_date,
            "matches": normalized,
            "total": len(normalized),
        })
    except HrmsApiError as exc2:
        logger.error("search_employee: both strategies failed. Last error: %s", exc2)
        return _safe_json({"error": str(exc2)})


# ── Tool 6: Get today's attendance for current user ───────────────────────────

@tool
async def get_my_attendance_today(config: RunnableConfig = None) -> str:
    """
    Get ONLY the currently logged-in user's own attendance for today.

    Use ONLY when the user explicitly asks about THEIR OWN attendance, e.g.
    "What is my attendance today?" or "Did I check in?"

    Do NOT use for team summaries, employee counts, or "attendance summary
    for today" — use get_attendance_summary instead.

    Returns:
        JSON with check-in time, check-out time, status, and worked hours.
    """
    token, emp_id = _get_auth(config)
    today_str = _today()

    try:
        data = await HrmsClient.get_attendance_by_date(token, emp_id, today_str)
        return _safe_json({"date": today_str, "employee_id": emp_id, "attendance": data})
    except HrmsApiError as exc:
        logger.error("get_my_attendance_today failed: %s", exc)
        return _safe_json({"error": str(exc)})


# ── Tool 7: Get attendance details for a specific employee on a date ──────────

@tool
async def get_employee_attendance_details(
    employee_id: Optional[int] = None,
    employee_name: Optional[str] = None,
    date_str: Optional[str] = None,
    config: RunnableConfig = None,
) -> str:
    """
    Get full attendance details (check-in, check-out, status, worked hours,
    shift info) for a SPECIFIC employee on a given date.

    Use this tool when the user asks about a particular employee's attendance
    on a specific day, e.g. "What time did John check in today?" or
    "Show attendance details for Kanchana today".

    Pass `employee_name` when you only know the name — the tool resolves the ID.

    Args:
        employee_id: The numeric employee ID to look up (preferred if known).
        employee_name: Employee name to search when ID is not known.
        date_str: Date in YYYY-MM-DD format. Defaults to today if not provided.

    Returns:
        JSON with check-in time, check-out time, status, shift, and worked hours
        for the specified employee.
    """
    token, session_emp_id = _get_auth(config)
    target_date = date_str or _today()

    _SELF_PRONOUNS = {"my", "mine", "i", "me", "myself", "our", "we"}
    if employee_name and employee_name.strip().lower() in _SELF_PRONOUNS:
        employee_name = None

    target_emp = employee_id
    resolved_name: str | None = employee_name

    if not target_emp and employee_name:
        logger.info("get_employee_attendance_details: searching for '%s'", employee_name)
        try:
            search_data = await HrmsClient.search_employees(token, employee_name.strip())
            emp_list = _extract_emp_list(search_data)
            if emp_list:
                first = emp_list[0]
                found_id = _extract_numeric_id(first)
                if found_id:
                    target_emp = found_id
                    resolved_name = (
                        first.get("EmployeeName") or first.get("employeeName") or
                        first.get("FullName") or first.get("fullName") or
                        first.get("Name") or employee_name
                    )
                else:
                    return _safe_json({
                        "error": f"Could not find employee named '{employee_name}'.",
                    })
            else:
                return _safe_json({
                    "error": f"No employee found matching '{employee_name}'.",
                })
        except HrmsApiError as exc:
            return _safe_json({
                "error": f"Could not search for employee '{employee_name}': {exc}",
            })

    if not target_emp:
        return _safe_json({
            "error": "Please provide an employee name or employee ID.",
        })

    emp_name = resolved_name or f"Employee {target_emp}"
    attendance_data = None

    # ── Strategy 1: AttendanceBasedOnDate (direct lookup) ─────────────────────
    try:
        attendance_data = await HrmsClient.get_attendance_by_date(token, target_emp, target_date)
        logger.info("get_employee_attendance_details: AttendanceBasedOnDate succeeded for emp %s", target_emp)
    except HrmsApiError as exc:
        logger.warning(
            "get_employee_attendance_details: AttendanceBasedOnDate failed for emp %s: %s — falling back to team-attendance",
            target_emp, exc,
        )

    # ── Strategy 2: Team-attendance fallback ──────────────────────────────────
    if attendance_data is None:
        try:
            team_data = await HrmsClient.get_team_attendance(token, session_emp_id, target_date, 0)
            emp_list = _extract_emp_list(team_data)
            emp_id_str = str(target_emp)
            found = next(
                (
                    e for e in emp_list
                    if isinstance(e, dict) and str(
                        e.get("EmployeeId") or e.get("employeeId") or e.get("Id") or ""
                    ) == emp_id_str
                ),
                None,
            )
            if found:
                attendance_data = found
                logger.info(
                    "get_employee_attendance_details: found emp %s in team-attendance data", target_emp
                )
            else:
                return _safe_json({
                    "error": f"Employee {target_emp} not found in team attendance for {target_date}.",
                    "employee_id": target_emp,
                    "employee_name": emp_name,
                    "date": target_date,
                })
        except HrmsApiError as exc2:
            logger.error("get_employee_attendance_details: team-attendance fallback also failed: %s", exc2)
            return _safe_json({
                "error": str(exc2),
                "employee_id": target_emp,
                "employee_name": emp_name,
                "date": target_date,
            })

    # ── Try to get a display name from the attendance record itself ────────────
    if isinstance(attendance_data, dict):
        emp_name = (
            attendance_data.get("EmployeeName") or attendance_data.get("employeeName") or
            attendance_data.get("FullName") or attendance_data.get("fullName") or
            attendance_data.get("Name") or attendance_data.get("name") or emp_name
        )

    # ── Fallback: query employee profile ──────────────────────────────────────
    if emp_name == f"Employee {target_emp}":
        try:
            profile = await HrmsClient.get_employee_details(token, target_emp)
            emp_name = (
                profile.get("EmployeeName") or profile.get("employeeName") or
                profile.get("FullName") or profile.get("fullName") or
                profile.get("Name") or profile.get("name") or emp_name
            )
        except HrmsApiError:
            pass

    return _safe_json({
        "employee_id": target_emp,
        "employee_name": emp_name,
        "date": target_date,
        "attendance": attendance_data,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Exported tool list (bound to the LLM in graph.py)
# ─────────────────────────────────────────────────────────────────────────────

ATTENDANCE_TOOLS = [
    get_present_employees,
    get_absent_employees,
    get_team_employee_list,
    get_attendance_summary,
    get_attendance_history,
    search_employee,
    get_my_attendance_today,
    get_employee_attendance_details,
]
