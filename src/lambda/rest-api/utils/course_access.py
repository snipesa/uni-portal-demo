"""
utils/course_access.py — Shared helpers for term-aware course access.
"""
from __future__ import annotations

import os
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.types import TypeDeserializer

from utils.auth import is_staff

_TABLE_NAME = os.environ["MAIN_TABLE_NAME"]
_dynamodb = boto3.resource("dynamodb")
_dynamodb_client = boto3.client("dynamodb")
_table = _dynamodb.Table(_TABLE_NAME)
_deserializer = TypeDeserializer()


def normalize_course_id(value: str | None) -> str:
    return (value or "").strip().upper()


def normalize_term_id(value: str | None) -> str:
    return (value or "").strip().upper()


def normalize_assignment_id(value: str | None) -> str:
    return (value or "").strip().upper()


def build_course_pk(course_id: str, term_id: str) -> str:
    return f"COURSE#{normalize_course_id(course_id)}#TERM#{normalize_term_id(term_id)}"


def get_course_item(course_id: str, term_id: str) -> dict[str, Any] | None:
    result = _table.get_item(
        Key={"PK": build_course_pk(course_id, term_id), "SK": "METADATA"}
    )
    return result.get("Item")


def get_assignment_item(
    course_id: str,
    term_id: str,
    assignment_id: str,
) -> dict[str, Any] | None:
    result = _table.get_item(
        Key={
            "PK": build_course_pk(course_id, term_id),
            "SK": f"ASSIGNMENT#{normalize_assignment_id(assignment_id)}",
        }
    )
    return result.get("Item")


def get_enrollment_item(
    course_id: str,
    term_id: str,
    student_id: str,
) -> dict[str, Any] | None:
    result = _table.get_item(
        Key={
            "PK": build_course_pk(course_id, term_id),
            "SK": f"STUDENT#{student_id}",
        }
    )
    return result.get("Item")


def get_staff_assignment_item(
    course_id: str,
    term_id: str,
    staff_id: str,
) -> dict[str, Any] | None:
    result = _table.get_item(
        Key={
            "PK": build_course_pk(course_id, term_id),
            "SK": f"STAFF#{staff_id}",
        }
    )
    return result.get("Item")


def list_course_staff_assignments(course_id: str, term_id: str) -> list[dict[str, Any]]:
    result = _table.query(
        KeyConditionExpression=Key("PK").eq(build_course_pk(course_id, term_id))
        & Key("SK").begins_with("STAFF#")
    )
    return result.get("Items", [])


def student_is_enrolled(course_id: str, term_id: str, student_id: str) -> bool:
    return bool(get_enrollment_item(course_id, term_id, student_id))


def staff_is_assigned(course_id: str, term_id: str, staff_id: str) -> bool:
    return bool(get_staff_assignment_item(course_id, term_id, staff_id))


def staff_is_course_instructor(course_id: str, term_id: str, staff_id: str) -> bool:
    assignment = get_staff_assignment_item(course_id, term_id, staff_id)
    return bool(assignment and assignment.get("staffRole") == "INSTRUCTOR")


def caller_can_access_course(caller: dict[str, Any], course_id: str, term_id: str) -> bool:
    if is_staff(caller):
        return staff_is_assigned(course_id, term_id, caller["sub"])
    return student_is_enrolled(course_id, term_id, caller["sub"])


def caller_can_access_submission(
    caller: dict[str, Any],
    submission: dict[str, Any],
) -> bool:
    if is_staff(caller):
        course_id = submission.get("courseId")
        term_id = submission.get("termId")
        if not course_id or not term_id:
            return False
        return staff_is_assigned(str(course_id), str(term_id), caller["sub"])
    return submission.get("studentId") == caller["sub"]


def list_enrolled_courses(student_id: str) -> list[dict[str, Any]]:
    result = _table.query(
        IndexName="GSI3-StudentEnrollments",
        KeyConditionExpression=Key("GSI3PK").eq(f"STUDENT#{student_id}"),
    )
    return result.get("Items", [])


def list_staff_courses(staff_id: str) -> list[dict[str, Any]]:
    result = _table.query(
        IndexName="GSI4-StaffCourses",
        KeyConditionExpression=Key("GSI4PK").eq(f"STAFF#{staff_id}"),
    )
    return result.get("Items", [])


def batch_get_course_items(course_refs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not course_refs:
        return []

    keys = []
    seen: set[tuple[str, str]] = set()
    for ref in course_refs:
        course_id = normalize_course_id(ref.get("courseId"))
        term_id = normalize_term_id(ref.get("termId"))
        if not course_id or not term_id:
            continue
        key = (course_id, term_id)
        if key in seen:
            continue
        seen.add(key)
        keys.append(
            {
                "PK": {"S": build_course_pk(course_id, term_id)},
                "SK": {"S": "METADATA"},
            }
        )

    if not keys:
        return []

    response = _dynamodb_client.batch_get_item(
        RequestItems={_TABLE_NAME: {"Keys": keys}}
    )
    raw_items = response.get("Responses", {}).get(_TABLE_NAME, [])
    items = [
        {key: _deserializer.deserialize(value) for key, value in item.items()}
        for item in raw_items
    ]
    items.sort(key=lambda item: (item.get("courseId", ""), item.get("termId", "")))
    return items
