"""
utils/auth.py — JWT claim extraction and role-guard helpers.

API Gateway HTTP API (JWT authorizer) injects verified claims into:
  event["requestContext"]["authorizer"]["jwt"]["claims"]

Cognito groups are available as the "cognito:groups" claim.
Self-registration is open (Story 2), so a signed-in user with no group
must be blocked here before reaching any route handler.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from utils.response import forbidden

logger = logging.getLogger(__name__)

_ROLE_ORDER = ["Admin", "Staff", "Students"]
_ALLOWED_GROUPS = set(_ROLE_ORDER)
_STAFF_GROUPS = {"Staff"}
_ADMIN_GROUPS = {"Admin"}


def _normalize_groups_claim(raw_groups: Any) -> list[str]:
    """
    Normalize the Cognito groups claim from API Gateway.

    HTTP API JWT authorizers may surface the claim as:
    - a native list
    - a comma-separated string
    - a JSON-encoded array string such as '["Staff","Students"]'
    """
    if isinstance(raw_groups, list):
        return [g for g in raw_groups if g in _ALLOWED_GROUPS]

    if raw_groups is None:
        return []

    value = str(raw_groups).strip()
    if not value:
        return []

    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return [str(g).strip() for g in parsed if str(g).strip() in _ALLOWED_GROUPS]
        inner = value[1:-1].strip()
        if inner:
            tokens = [
                token.strip().strip('"').strip("'")
                for token in inner.replace(",", " ").split()
            ]
            return [token for token in tokens if token in _ALLOWED_GROUPS]

    return [g.strip() for g in value.split(",") if g.strip() in _ALLOWED_GROUPS]


def build_caller_context(event: dict[str, Any]) -> dict[str, Any] | None:
    """
    Extract caller identity from the API Gateway JWT authorizer context.

    Returns a dict:
        sub           – Cognito user UUID (immutable identifier)
        email         – user's email address
        groups        – list of known Cognito groups the caller belongs to
        primary_group – first recognised group (lowest precedence index wins)

    Returns None if the JWT claims block is absent (unauthenticated request
    that somehow bypassed the authorizer).
    """
    try:
        claims: dict = event["requestContext"]["authorizer"]["jwt"]["claims"]
    except (KeyError, TypeError):
        return None

    sub = claims.get("sub", "").strip()
    if not sub:
        return None

    raw_groups = claims.get("cognito:groups", "")
    groups = _normalize_groups_claim(raw_groups)
    primary_group = next((role for role in _ROLE_ORDER if role in groups), None)

    return {
        "sub": sub,
        "email": claims.get("email", ""),
        "groups": groups,
        "primary_group": primary_group,
    }


def require_auth(event: dict[str, Any]) -> tuple[dict[str, Any] | None, dict | None]:
    """
    Gate function called at the top of every Lambda invocation.

    Returns (caller, None)          — authentication and group assignment OK.
    Returns (None, error_response)  — authentication failed or user ungrouped.

    Usage::

        caller, err = require_auth(event)
        if err:
            return err
    """
    caller = build_caller_context(event)

    if not caller:
        logger.warning("auth_context_missing")
        return None, forbidden("Authentication context is missing.")

    if not caller["groups"]:
        logger.warning("ungrouped_user", extra={"sub": caller["sub"]})
        return None, forbidden(
            "Your account is pending role assignment. "
            "Please contact an administrator."
        )

    return caller, None


def is_staff(caller: dict[str, Any]) -> bool:
    """True for Staff users; False for Students."""
    return bool(set(caller["groups"]) & _STAFF_GROUPS)


def is_admin(caller: dict[str, Any]) -> bool:
    """True for Admin users."""
    return bool(set(caller["groups"]) & _ADMIN_GROUPS)


def is_student(caller: dict[str, Any]) -> bool:
    """True when the caller's primary role is Student."""
    return "Students" in caller["groups"]
