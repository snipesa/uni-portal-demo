"""
routes/courses.py — Term-aware course, assignment, and access management APIs.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.types import TypeSerializer
from botocore.exceptions import ClientError

from utils import response as resp
from utils.auth import is_staff
from utils.cognito_users import find_user_by_email
from utils.course_access import (
    batch_get_course_items,
    build_course_pk,
    caller_can_access_course,
    get_course_item,
    get_enrollment_item,
    get_staff_assignment_item,
    list_course_staff_assignments,
    normalize_assignment_id,
    normalize_course_id,
    normalize_term_id,
    staff_is_assigned,
    staff_is_course_instructor,
)

logger = logging.getLogger(__name__)

_TABLE = os.environ["MAIN_TABLE_NAME"]
_dynamodb = boto3.resource("dynamodb")
_dynamodb_client = boto3.client("dynamodb")
_table = _dynamodb.Table(_TABLE)
_type_serializer = TypeSerializer()
_VALID_STAFF_ROLES = {"INSTRUCTOR", "TA"}


def _ddb_item(item: dict[str, Any]) -> dict[str, Any]:
    return {key: _type_serializer.serialize(value) for key, value in item.items()}


def _load_json_body(event: dict) -> tuple[dict[str, Any] | None, dict | None]:
    try:
        return json.loads(event.get("body") or "{}"), None
    except (json.JSONDecodeError, TypeError):
        return None, resp.bad_request("Request body must be valid JSON.")


def handle_list_courses(event: dict, caller: dict, path_params: dict) -> dict:
    """GET /courses"""
    if is_staff(caller):
        memberships = _table.query(
            IndexName="GSI4-StaffCourses",
            KeyConditionExpression=Key("GSI4PK").eq(f"STAFF#{caller['sub']}"),
        ).get("Items", [])
    else:
        memberships = _table.query(
            IndexName="GSI3-StudentEnrollments",
            KeyConditionExpression=Key("GSI3PK").eq(f"STUDENT#{caller['sub']}"),
        ).get("Items", [])

    courses = batch_get_course_items(memberships)
    return resp.ok({"courses": courses, "count": len(courses)})


def handle_create_course(event: dict, caller: dict, path_params: dict) -> dict:
    """POST /courses"""
    if not is_staff(caller):
        return resp.forbidden("Only staff can create courses.")

    body, error = _load_json_body(event)
    if error:
        return error

    course_id = normalize_course_id(body.get("courseId"))
    term_id = normalize_term_id(body.get("termId"))
    name = (body.get("name") or "").strip()
    description = (body.get("description") or "").strip()
    if not course_id or not term_id or not name:
        return resp.bad_request("courseId, termId, and name are required.")

    now = datetime.now(timezone.utc).isoformat()
    course_pk = build_course_pk(course_id, term_id)
    course_item: dict[str, Any] = {
        "PK": course_pk,
        "SK": "METADATA",
        "EntityType": "COURSE",
        "courseId": course_id,
        "termId": term_id,
        "name": name,
        "description": description,
        "createdBy": caller["sub"],
        "createdAt": now,
        "updatedAt": now,
        "active": True,
    }
    staff_item: dict[str, Any] = {
        "PK": course_pk,
        "SK": f"STAFF#{caller['sub']}",
        "EntityType": "STAFF_ASSIGNMENT",
        "courseId": course_id,
        "termId": term_id,
        "staffId": caller["sub"],
        "staffRole": "INSTRUCTOR",
        "assignedAt": now,
        "assignedBy": caller["sub"],
        "GSI4PK": f"STAFF#{caller['sub']}",
        "GSI4SK": course_pk,
    }

    try:
        _dynamodb_client.transact_write_items(
            TransactItems=[
                {
                    "Put": {
                        "TableName": _TABLE,
                        "Item": _ddb_item(course_item),
                        "ConditionExpression": "attribute_not_exists(PK) AND attribute_not_exists(SK)",
                    }
                },
                {
                    "Put": {
                        "TableName": _TABLE,
                        "Item": _ddb_item(staff_item),
                        "ConditionExpression": "attribute_not_exists(PK) AND attribute_not_exists(SK)",
                    }
                },
            ]
        )
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"TransactionCanceledException", "ConditionalCheckFailedException"}:
            return resp.conflict("That course already exists for the selected term.")
        raise

    return resp.ok(course_item, status=201)


def handle_get_course(event: dict, caller: dict, path_params: dict) -> dict:
    """GET /courses/{courseId}/terms/{termId}"""
    course_id = normalize_course_id(path_params.get("courseId"))
    term_id = normalize_term_id(path_params.get("termId"))
    if not course_id or not term_id:
        return resp.bad_request("courseId and termId path parameters are required.")

    course = get_course_item(course_id, term_id)
    if not course:
        return resp.not_found("Course")
    if not caller_can_access_course(caller, course_id, term_id):
        return resp.forbidden("You do not have access to this course.")
    return resp.ok(course)


def handle_list_assignments(event: dict, caller: dict, path_params: dict) -> dict:
    """GET /courses/{courseId}/terms/{termId}/assignments"""
    course_id = normalize_course_id(path_params.get("courseId"))
    term_id = normalize_term_id(path_params.get("termId"))
    if not course_id or not term_id:
        return resp.bad_request("courseId and termId path parameters are required.")
    if not get_course_item(course_id, term_id):
        return resp.not_found("Course")
    if not caller_can_access_course(caller, course_id, term_id):
        return resp.forbidden("You do not have access to this course.")

    result = _table.query(
        KeyConditionExpression=Key("PK").eq(build_course_pk(course_id, term_id))
        & Key("SK").begins_with("ASSIGNMENT#")
    )
    assignments = result.get("Items", [])
    return resp.ok({"assignments": assignments, "count": len(assignments)})


def handle_create_assignment(event: dict, caller: dict, path_params: dict) -> dict:
    """POST /courses/{courseId}/terms/{termId}/assignments"""
    if not is_staff(caller):
        return resp.forbidden("Only staff can create assignments.")

    course_id = normalize_course_id(path_params.get("courseId"))
    term_id = normalize_term_id(path_params.get("termId"))
    if not course_id or not term_id:
        return resp.bad_request("courseId and termId path parameters are required.")
    if not get_course_item(course_id, term_id):
        return resp.not_found("Course")
    if not staff_is_assigned(course_id, term_id, caller["sub"]):
        return resp.forbidden("You are not assigned to this course.")

    body, error = _load_json_body(event)
    if error:
        return error

    assignment_id = normalize_assignment_id(body.get("assignmentId"))
    title = (body.get("title") or "").strip()
    description = (body.get("description") or "").strip()
    due_date = (body.get("dueDate") or "").strip()
    if not assignment_id or not title:
        return resp.bad_request("assignmentId and title are required.")

    now = datetime.now(timezone.utc).isoformat()
    item: dict[str, Any] = {
        "PK": build_course_pk(course_id, term_id),
        "SK": f"ASSIGNMENT#{assignment_id}",
        "EntityType": "ASSIGNMENT",
        "assignmentId": assignment_id,
        "courseId": course_id,
        "termId": term_id,
        "title": title,
        "description": description,
        "createdAt": now,
        "updatedAt": now,
        "active": True,
    }
    if due_date:
        item["dueDate"] = due_date

    try:
        _table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)",
        )
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            return resp.conflict("That assignment already exists for this course.")
        raise

    return resp.ok(item, status=201)


def handle_enroll_student(event: dict, caller: dict, path_params: dict) -> dict:
    """POST /courses/{courseId}/terms/{termId}/enrollments"""
    if not is_staff(caller):
        return resp.forbidden("Only staff can enroll students.")

    course_id = normalize_course_id(path_params.get("courseId"))
    term_id = normalize_term_id(path_params.get("termId"))
    if not course_id or not term_id:
        return resp.bad_request("courseId and termId path parameters are required.")
    if not get_course_item(course_id, term_id):
        return resp.not_found("Course")
    if not staff_is_assigned(course_id, term_id, caller["sub"]):
        return resp.forbidden("You are not assigned to this course.")

    body, error = _load_json_body(event)
    if error:
        return error

    student_email = (body.get("studentEmail") or "").strip()
    if not student_email:
        return resp.bad_request("studentEmail is required.")

    student = find_user_by_email(student_email)
    if not student:
        return resp.not_found("Student")
    if "Students" not in student.get("groups", []):
        return resp.bad_request("That email does not belong to a student account.")

    student_id = student["sub"]

    now = datetime.now(timezone.utc).isoformat()
    course_pk = build_course_pk(course_id, term_id)
    item: dict[str, Any] = {
        "PK": course_pk,
        "SK": f"STUDENT#{student_id}",
        "EntityType": "ENROLLMENT",
        "courseId": course_id,
        "termId": term_id,
        "studentId": student_id,
        "studentEmail": student["email"],
        "enrolledAt": now,
        "enrolledBy": caller["sub"],
        "GSI3PK": f"STUDENT#{student_id}",
        "GSI3SK": course_pk,
    }

    try:
        _table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)",
        )
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            return resp.conflict("That student is already enrolled in this course.")
        raise

    return resp.ok(item, status=201)


def handle_assign_staff(event: dict, caller: dict, path_params: dict) -> dict:
    """POST /courses/{courseId}/terms/{termId}/staff"""
    if not is_staff(caller):
        return resp.forbidden("Only staff can assign staff.")

    course_id = normalize_course_id(path_params.get("courseId"))
    term_id = normalize_term_id(path_params.get("termId"))
    if not course_id or not term_id:
        return resp.bad_request("courseId and termId path parameters are required.")
    if not get_course_item(course_id, term_id):
        return resp.not_found("Course")
    if not staff_is_course_instructor(course_id, term_id, caller["sub"]):
        return resp.forbidden("Only assigned instructors can manage staff for this course.")

    body, error = _load_json_body(event)
    if error:
        return error

    staff_email = (body.get("staffEmail") or "").strip()
    staff_role = (body.get("staffRole") or "").strip().upper()
    if not staff_email or staff_role not in _VALID_STAFF_ROLES:
        return resp.bad_request("staffEmail and a valid staffRole are required.")

    staff_user = find_user_by_email(staff_email)
    if not staff_user:
        return resp.not_found("Staff user")
    if "Staff" not in staff_user.get("groups", []):
        return resp.bad_request("That email does not belong to a staff account.")

    staff_id = staff_user["sub"]

    now = datetime.now(timezone.utc).isoformat()
    course_pk = build_course_pk(course_id, term_id)
    item: dict[str, Any] = {
        "PK": course_pk,
        "SK": f"STAFF#{staff_id}",
        "EntityType": "STAFF_ASSIGNMENT",
        "courseId": course_id,
        "termId": term_id,
        "staffId": staff_id,
        "staffEmail": staff_user["email"],
        "staffRole": staff_role,
        "assignedAt": now,
        "assignedBy": caller["sub"],
        "GSI4PK": f"STAFF#{staff_id}",
        "GSI4SK": course_pk,
    }

    try:
        _table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)",
        )
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            return resp.conflict("That staff member is already assigned to this course.")
        raise

    return resp.ok(item, status=201)


def handle_unenroll_student(event: dict, caller: dict, path_params: dict) -> dict:
    """DELETE /courses/{courseId}/terms/{termId}/enrollments"""
    if not is_staff(caller):
        return resp.forbidden("Only staff can unenroll students.")

    course_id = normalize_course_id(path_params.get("courseId"))
    term_id = normalize_term_id(path_params.get("termId"))
    if not course_id or not term_id:
        return resp.bad_request("courseId and termId path parameters are required.")
    if not get_course_item(course_id, term_id):
        return resp.not_found("Course")
    if not staff_is_assigned(course_id, term_id, caller["sub"]):
        return resp.forbidden("You are not assigned to this course.")

    body, error = _load_json_body(event)
    if error:
        return error

    student_email = (body.get("studentEmail") or "").strip()
    if not student_email:
        return resp.bad_request("studentEmail is required.")

    student = find_user_by_email(student_email)
    if not student:
        return resp.not_found("Student")

    student_id = student["sub"]
    enrollment = get_enrollment_item(course_id, term_id, student_id)
    if not enrollment:
        return resp.not_found("Enrollment")

    _table.delete_item(
        Key={
            "PK": build_course_pk(course_id, term_id),
            "SK": f"STUDENT#{student_id}",
        }
    )

    return resp.ok(
        {
            "courseId": course_id,
            "termId": term_id,
            "studentId": student_id,
            "studentEmail": student.get("email", student_email),
            "removed": True,
        }
    )


def handle_unassign_staff(event: dict, caller: dict, path_params: dict) -> dict:
    """DELETE /courses/{courseId}/terms/{termId}/staff"""
    if not is_staff(caller):
        return resp.forbidden("Only staff can unassign staff.")

    course_id = normalize_course_id(path_params.get("courseId"))
    term_id = normalize_term_id(path_params.get("termId"))
    if not course_id or not term_id:
        return resp.bad_request("courseId and termId path parameters are required.")
    if not get_course_item(course_id, term_id):
        return resp.not_found("Course")
    if not staff_is_course_instructor(course_id, term_id, caller["sub"]):
        return resp.forbidden("Only assigned instructors can manage staff for this course.")

    body, error = _load_json_body(event)
    if error:
        return error

    staff_email = (body.get("staffEmail") or "").strip()
    if not staff_email:
        return resp.bad_request("staffEmail is required.")

    staff_user = find_user_by_email(staff_email)
    if not staff_user:
        return resp.not_found("Staff user")

    staff_id = staff_user["sub"]
    assignment = get_staff_assignment_item(course_id, term_id, staff_id)
    if not assignment:
        return resp.not_found("Staff assignment")

    if assignment.get("staffRole") == "INSTRUCTOR":
        instructors = [
            item for item in list_course_staff_assignments(course_id, term_id)
            if item.get("staffRole") == "INSTRUCTOR"
        ]
        if len(instructors) <= 1:
            return resp.conflict("At least one instructor must remain assigned to the course.")

    _table.delete_item(
        Key={
            "PK": build_course_pk(course_id, term_id),
            "SK": f"STAFF#{staff_id}",
        }
    )

    return resp.ok(
        {
            "courseId": course_id,
            "termId": term_id,
            "staffId": staff_id,
            "staffEmail": staff_user.get("email", staff_email),
            "removed": True,
        }
    )
