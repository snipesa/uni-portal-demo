"""
utils/response.py — Standard HTTP response helpers.

Every route module returns one of these so the response shape is
consistent across the whole API.
"""
from __future__ import annotations

import json
from typing import Any


def _build(body: Any, status: int) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str),
    }


def ok(body: Any, status: int = 200) -> dict:
    return _build(body, status)


def _error(message: str, status: int, code: str) -> dict:
    return _build({"error": message, "code": code}, status)


def bad_request(message: str) -> dict:
    return _error(message, 400, "BAD_REQUEST")


def unauthorized(message: str = "Unauthorized") -> dict:
    return _error(message, 401, "UNAUTHORIZED")


def forbidden(message: str = "Forbidden") -> dict:
    return _error(message, 403, "FORBIDDEN")


def not_found(resource: str = "Resource") -> dict:
    return _error(f"{resource} not found.", 404, "NOT_FOUND")


def conflict(message: str) -> dict:
    return _error(message, 409, "CONFLICT")


def service_unavailable(message: str) -> dict:
    return _error(message, 503, "SERVICE_UNAVAILABLE")


def internal_error(correlation_id: str | None = None) -> dict:
    msg = "An unexpected error occurred."
    if correlation_id:
        msg += f" Reference: {correlation_id}"
    return _error(msg, 500, "INTERNAL_ERROR")
