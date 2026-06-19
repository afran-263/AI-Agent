"""Async HTTP client for the Voyon HRMS REST APIs.

All data retrieval goes through these methods — no direct DB access.
The JWT token from the authenticated session is passed with every request.
"""
from __future__ import annotations

import logging
from typing import Any, Optional
from datetime import date

import httpx

from src.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = 30.0


def _make_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.hrms_base_url,
        verify=settings.hrms_ssl_verify,
        timeout=_TIMEOUT,
    )


class HrmsApiError(Exception):
    """Raised when an HRMS API call fails."""

    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


class HrmsClient:
    """Thin async wrapper around the Voyon HRMS REST APIs."""

    # ── Authentication ────────────────────────────────────────────────────────

    @staticmethod
    async def login(username: str, password: str) -> dict:
        """POST /m/api/Login/LoginUser → returns token + employee info."""
        async with _make_client() as client:
            resp = await client.post(
                settings.hrms_login_path,
                json={
                    "UserName": username,
                    "Password": password,
                    "DeviceId": "web-attend-agent",
                    "DeviceType": "Web",
                },
            )
        if resp.status_code != 200:
            logger.warning("HRMS login failed for %s: HTTP %s", username, resp.status_code)
            raise HrmsApiError("Invalid username or password.", resp.status_code)

        data = resp.json()
        logger.debug("HRMS login raw keys: %s", list(data.keys()) if isinstance(data, dict) else type(data))

        # ASP.NET Core may return PascalCase or camelCase depending on serialiser settings
        token = data.get("token") or data.get("Token")
        if not token:
            msg = data.get("message") or data.get("Message") or "No token returned."
            logger.warning("HRMS login for %s returned no token. Message: %s  Keys: %s",
                           username, msg, list(data.keys()) if isinstance(data, dict) else "?")
            raise HrmsApiError(f"Login failed: {msg}")

        # Normalise to lowercase keys so the rest of the code is consistent
        return {
            "token":        token,
            "refreshToken": data.get("refreshToken") or data.get("RefreshToken", ""),
            "employeeId":   data.get("employeeId") or data.get("EmployeeId", 0),
            "userId":       data.get("userId") or data.get("UserId", 0),
            "userName":     data.get("userName") or data.get("UserName") or data.get("FullName") or username,
        }

    # ── Generic helpers ───────────────────────────────────────────────────────

    @staticmethod
    async def _get(path: str, token: str, params: Optional[dict] = None) -> Any:
        """Authenticated GET helper."""
        async with _make_client() as client:
            resp = await client.get(
                path,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
            )
        if resp.status_code == 401:
            raise HrmsApiError("Authentication expired. Please log in again.", 401)
        if not resp.is_success:
            body_preview = resp.text[:300] if resp.text else ""
            logger.warning(
                "HRMS GET %s failed: HTTP %s | body: %s",
                path, resp.status_code, body_preview,
            )
            raise HrmsApiError(
                f"HRMS API returned HTTP {resp.status_code} for {path}. Details: {body_preview}",
                resp.status_code,
            )
        return resp.json()

    # ── Attendance APIs ───────────────────────────────────────────────────────

    @staticmethod
    async def get_team_attendance(
        token: str,
        employee_id: int,
        date_str: str,
        reporting_type: int = 0,
    ) -> Any:
        """GET /m/api/Attendance/team-attendance
        Returns attendance data for the entire team under the given manager.
        reporting_type: 0=All, 1=Direct, 2=Indirect
        """
        return await HrmsClient._get(
            "/m/api/Attendance/team-attendance",
            token,
            params={
                "employeeId": employee_id,
                "date": date_str,
                "reportingType": reporting_type,
            },
        )

    @staticmethod
    async def get_attendance_by_date(
        token: str,
        employee_id: int,
        date_str: str,
    ) -> Any:
        """GET /m/api/Attendance/AttendanceBasedOnDate
        Returns a single employee's attendance details for a given date.
        """
        return await HrmsClient._get(
            "/m/api/Attendance/AttendanceBasedOnDate",
            token,
            params={"employeeId": employee_id, "date": date_str},
        )

    @staticmethod
    async def get_monthly_attendance(
        token: str,
        employee_id: int,
        month: int,
        year: int,
    ) -> Any:
        """GET /m/api/Attendance/MonthlyAttendance
        Returns a monthly attendance summary (calendar view) for an employee.
        """
        return await HrmsClient._get(
            "/m/api/Attendance/MonthlyAttendance",
            token,
            params={"employeeId": employee_id, "month": month, "year": year},
        )

    @staticmethod
    async def search_employees(token: str, search_value: str, page: int = 1) -> Any:
        """GET /m/api/Employee/search-employees/{searchValue}/{currentPage}
        Dedicated mobile employee search — returns employees matching the search term.
        """
        from urllib.parse import quote
        encoded = quote(str(search_value), safe="")
        return await HrmsClient._get(
            f"/m/api/Employee/search-employees/{encoded}/{page}",
            token,
        )

    @staticmethod
    async def get_employee_details(token: str, employee_id: int) -> Any:
        """GET /m/api/Employee/GetEmployeeDetails?employeeId={id}"""
        return await HrmsClient._get(
            "/m/api/Employee/GetEmployeeDetails",
            token,
            params={"employeeId": employee_id},
        )
