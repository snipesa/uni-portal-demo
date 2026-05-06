"""
routes/admin.py — Admin-only Cognito group-management APIs.
"""
from __future__ import annotations

import json
from typing import Any

from utils import response as resp
from utils.auth import is_admin
from utils.cognito_users import (
    add_user_to_group,
    find_user_by_email,
    normalize_manageable_group_name,
    remove_user_from_group,
)


def _require_admin(caller: dict[str, Any]) -> dict | None:
    if not is_admin(caller):
        return resp.forbidden("Only admin users can access this route.")
    return None


def _load_json_body(event: dict) -> tuple[dict[str, Any] | None, dict | None]:
    try:
        return json.loads(event.get("body") or "{}"), None
    except (json.JSONDecodeError, TypeError):
        return None, resp.bad_request("Request body must be valid JSON.")


def _read_target_email(event: dict, body: dict[str, Any] | None = None) -> str:
    if body is not None:
        return (body.get("email") or "").strip().lower()
    query_params = event.get("queryStringParameters") or {}
    return (query_params.get("email") or "").strip().lower()


def _resolve_manageable_group_name(body: dict[str, Any]) -> tuple[str, dict | None]:
    group_name = normalize_manageable_group_name(body.get("groupName") or "")
    if group_name:
        return group_name, None
    return "", resp.bad_request("Only Students and Staff can be managed from the admin portal.")


def _serialize_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "username": user["username"],
        "sub": user["sub"],
        "email": user["email"],
        "groups": user.get("groups", []),
    }


def handle_get_user_by_email(event: dict, caller: dict, path_params: dict) -> dict:
    """GET /admin/users?email=user@example.edu"""
    auth_error = _require_admin(caller)
    if auth_error:
        return auth_error

    email = _read_target_email(event)
    if not email:
        return resp.bad_request("email is required.")

    user = find_user_by_email(email)
    if not user:
        return resp.not_found("User")

    return resp.ok({"user": _serialize_user(user)})


def handle_add_user_to_group(event: dict, caller: dict, path_params: dict) -> dict:
    """POST /admin/groups/add"""
    auth_error = _require_admin(caller)
    if auth_error:
        return auth_error

    body, error = _load_json_body(event)
    if error:
        return error

    email = _read_target_email(event, body)
    group_name, error = _resolve_manageable_group_name(body or {})
    if error:
        return error
    if not email:
        return resp.bad_request("email is required.")

    user = find_user_by_email(email)
    if not user:
        return resp.not_found("User")

    if group_name not in user.get("groups", []):
        add_user_to_group(user["username"], group_name)
        user = find_user_by_email(email)
        if not user:
            return resp.not_found("User")

    return resp.ok({"user": _serialize_user(user)})


def handle_remove_user_from_group(event: dict, caller: dict, path_params: dict) -> dict:
    """POST /admin/groups/remove"""
    auth_error = _require_admin(caller)
    if auth_error:
        return auth_error

    body, error = _load_json_body(event)
    if error:
        return error

    email = _read_target_email(event, body)
    group_name, error = _resolve_manageable_group_name(body or {})
    if error:
        return error
    if not email:
        return resp.bad_request("email is required.")

    user = find_user_by_email(email)
    if not user:
        return resp.not_found("User")

    if group_name in user.get("groups", []):
        remove_user_from_group(user["username"], group_name)
        user = find_user_by_email(email)
        if not user:
            return resp.not_found("User")

    return resp.ok({"user": _serialize_user(user)})
