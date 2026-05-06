"""
utils/cognito_users.py — Resolve Cognito users for course and submission workflows.
"""
from __future__ import annotations

import os
from typing import Any

import boto3

_USER_POOL_ID = os.environ["USER_POOL_ID"]
_cognito = boto3.client("cognito-idp")
_ROLE_ORDER = ["Admin", "Staff", "Students"]
MANAGEABLE_GROUPS = {"Students", "Staff"}


def _sort_groups(groups: list[str]) -> list[str]:
    ordered = [group for group in _ROLE_ORDER if group in groups]
    remaining = sorted(group for group in groups if group not in _ROLE_ORDER)
    return ordered + remaining


def _normalize_manageable_group_name(group_name: str) -> str:
    candidate = (group_name or "").strip().lower()
    mapping = {group.lower(): group for group in MANAGEABLE_GROUPS}
    return mapping.get(candidate, "")


def _list_groups_for_username(username: str) -> list[str]:
    groups_response = _cognito.admin_list_groups_for_user(
        UserPoolId=_USER_POOL_ID,
        Username=username,
    )
    groups = [
        item.get("GroupName", "").strip()
        for item in groups_response.get("Groups", [])
        if item.get("GroupName")
    ]
    return _sort_groups(groups)


def _build_user_profile(user: dict[str, Any], fallback_email: str = "") -> dict[str, Any] | None:
    username = user.get("Username", "").strip()
    attributes = {
        item.get("Name"): item.get("Value", "")
        for item in user.get("Attributes", [])
    }
    sub = attributes.get("sub", "").strip()
    resolved_email = attributes.get("email", "").strip().lower()
    if not username or not sub:
        return None

    return {
        "username": username,
        "sub": sub,
        "email": resolved_email or fallback_email,
        "groups": _list_groups_for_username(username),
        "displayName": (
            attributes.get("name", "").strip()
            or " ".join(
                part for part in [
                    attributes.get("given_name", "").strip(),
                    attributes.get("family_name", "").strip(),
                ] if part
            ).strip()
        ),
    }


def find_user_by_email(email: str) -> dict[str, Any] | None:
    """
    Resolve a Cognito user by email.

    Returns:
      {
        "username": "...",
        "sub": "...",
        "email": "...",
        "groups": ["Students" | "Staff", ...],
      }
    """
    lookup_email = (email or "").strip()
    if not lookup_email:
        return None

    normalized_email = lookup_email.lower()

    users: list[dict[str, Any]] = []
    for candidate in dict.fromkeys([lookup_email, normalized_email]):
        response = _cognito.list_users(
            UserPoolId=_USER_POOL_ID,
            Filter=f'email = "{candidate}"',
            Limit=2,
        )
        users = response.get("Users", [])
        if users:
            break

    if len(users) != 1:
        return None

    profile = _build_user_profile(users[0], fallback_email=normalized_email)
    if not profile:
        return None
    return {
        "username": profile["username"],
        "sub": profile["sub"],
        "email": profile["email"],
        "groups": profile["groups"],
    }


def find_user_by_sub(user_sub: str) -> dict[str, Any] | None:
    """
    Resolve a Cognito user by immutable sub/username for display purposes.

    Returns:
      {
        "username": "...",
        "sub": "...",
        "email": "...",
        "displayName": "...",
        "groups": ["Students" | "Staff", ...],
      }
    """
    lookup_sub = (user_sub or "").strip()
    if not lookup_sub:
        return None

    response = _cognito.list_users(
        UserPoolId=_USER_POOL_ID,
        Filter=f'sub = "{lookup_sub}"',
        Limit=2,
    )
    users = response.get("Users", [])
    if len(users) != 1:
        return None

    profile = _build_user_profile(users[0])
    if not profile:
        return None

    return {
        "username": profile["username"],
        "sub": profile["sub"],
        "email": profile["email"],
        "displayName": profile["displayName"],
        "groups": profile["groups"],
    }


def normalize_manageable_group_name(group_name: str) -> str:
    """Return the canonical manageable Cognito group name, or empty string."""
    return _normalize_manageable_group_name(group_name)


def add_user_to_group(username: str, group_name: str) -> None:
    """Add a Cognito user to a manageable group."""
    _cognito.admin_add_user_to_group(
        UserPoolId=_USER_POOL_ID,
        Username=username,
        GroupName=group_name,
    )


def remove_user_from_group(username: str, group_name: str) -> None:
    """Remove a Cognito user from a manageable group."""
    _cognito.admin_remove_user_from_group(
        UserPoolId=_USER_POOL_ID,
        Username=username,
        GroupName=group_name,
    )
