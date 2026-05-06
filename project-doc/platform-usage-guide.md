# University Assignment Portal - Platform Usage Guide

## Purpose

This document explains how the platform currently works based on the implemented code.
It is intended for UX and product teams who need to understand the real user journeys,
role behavior, and current platform constraints before designing or demonstrating flows.

This guide describes the platform **as it exists now in code**, not future-state ideas.

---

## Platform Summary

The platform is a role-aware university portal where:

- Staff create course offerings for a specific term
- Assigned course instructors can assign other staff to a course offering
- Assigned staff can add assignments and enroll students
- Students can upload assignment submissions only after they are enrolled in a
  course offering and the assignment exists

The current course model is:

- `courseId` + `termId` identifies a course offering
- there is no `sectionId` in this phase

Example:

- `courseId = CS101`
- `termId = 2026-SPRING`

On the website, staff do not type a term ID when creating a course. They choose from
standard terms for the current calendar year and one year back, such as:

- `2026-SPRING`
- `2026-SUMMER`
- `2026-FALL`
- `2026-WINTER`

---

## Current Roles

The platform currently recognizes these Cognito groups:

- `Students`
- `Staff`

There is also an ungrouped state:

- authenticated users with no recognized group are blocked from using the platform

Role handling is implemented in the portal and backend authorization logic.

---

## Current Website Navigation

The current website has three possible views depending on role:

### 1. Dashboard

Visible to:

- Students
- Staff

Purpose:

- Students see their own submissions
- Staff see submissions for a selected course offering

### 2. Upload Assignment

Visible to:

- Students only

Purpose:

- students select one enrolled course offering
- students select an assignment in that course offering
- students upload and confirm a file submission

### 3. Courses

Visible to:

- Staff

Purpose:

- create course offerings
- add assignments
- enroll students
- assign staff

Important:

- any `Staff` user can create a course offering
- the creating staff user becomes the course `INSTRUCTOR`
- only an assigned course instructor can assign additional staff to that course

---

## Core Platform Concepts

### Course Offering

A course offering is identified by:

- `courseId`
- `termId`

Example:

- `CS101`
- `2026-SPRING`

This means the same course code can be reused in another term without collision.

### Assignment

Assignments belong to one course offering.

Example:

- Course offering: `CS101` in `2026-SPRING`
- Assignment: `A1`

### Enrollment

A student must be enrolled in a course offering before they can submit to it.

### Staff Assignment

A staff user must be assigned to a course offering before they can manage it.

---

## User Journeys

## Unauthenticated User

What they see:

- landing page
- sign-in button

What they can do:

- start Cognito sign-in

What they cannot do:

- view any portal data
- use any dashboard, upload, or course management features

---

## Authenticated but Ungrouped User

What they see:

- a message that role assignment is pending

What they can do:

- sign out

What they cannot do:

- access dashboard features
- upload assignments
- manage courses

This is intentional. Group membership is required before any role-based action is allowed.

---

## Student Experience

### What a student sees

Students see:

- `Dashboard`
- `Upload Assignment`

They do **not** see:

- `Courses`

### Student dashboard behavior

The Dashboard loads the student's own submissions.

Each row currently shows:

- submission ID
- assignment ID
- status
- created date

### Student upload flow

The Upload page is the main student action.

The flow is:

1. Student opens `Upload Assignment`
2. Website loads the student's enrolled course offerings
3. Student selects a course offering from a dropdown
4. Website loads assignments for that course offering
5. Student selects an assignment
6. Student enters a submission title
7. Student chooses a file
8. Website requests an upload URL from the backend
9. Browser uploads the file directly to S3
10. Website confirms the upload with the backend

### What must exist before a student can upload

For upload to work:

- the course offering must exist
- the course offering must be active
- the assignment must exist
- the assignment must be active
- the student must be enrolled in that course offering

If any of those conditions fail, the upload is blocked.

### Student empty states

If a student has no enrolled courses:

- the course dropdown is disabled
- assignment selection is disabled
- upload is effectively blocked

---

## Staff Experience

### What a staff user sees

Staff users see:

- `Dashboard`
- `Courses`

They do **not** see:

- `Upload Assignment`

### Staff dashboard behavior

The Dashboard shows submissions for one selected course offering.

A staff user:

1. opens the Dashboard
2. selects a course offering from the course filter
3. sees submissions for that course offering

Each row currently shows:

- submission ID
- student ID
- assignment ID
- status
- created date

### Staff course management behavior

Staff users can:

- create a new course offering
- add assignments to a course offering they are assigned to
- enroll students into a course offering they are assigned to
- unenroll students from a course offering they are assigned to
- assign other staff to a course offering where they are an assigned instructor
- unassign staff from a course offering where they are an assigned instructor

### Staff course creation flow

1. Open `Courses`
2. Fill in:
   - course ID
   - course name
   - optional description
3. Select a term from the standardized dropdown
4. Submit the form

When this succeeds:

- the course offering is created
- the creating staff user is automatically assigned as the course instructor

The website term dropdown shows only:

- current calendar year terms
- one prior year of terms

The backend can still store additional normalized term IDs when needed.

### Staff assignment flow

The assigned course instructor can assign:

- another instructor
- a TA

This is currently done by entering the target staff member's email address.

---

## Current End-to-End Teaching Workflow

The intended operational flow on the platform today is:

1. Staff creates a course offering with `courseId + termId`
2. The creating staff user becomes the course instructor
3. That course instructor optionally assigns TAs or other instructors
4. Assigned staff add assignments
5. Assigned staff enroll students
6. Student sees enrolled course offerings in Upload
7. Student selects assignment and uploads a submission
8. Staff view submissions on the Dashboard for that course offering

This is the clearest "happy path" currently supported by the implemented website.

---

## Data Entry Expectations in the Current UI

### Course creation

Requires:

- course ID
- term selection from the standard dropdown
- course name

### Assignment creation

Requires:

- course offering selection
- assignment ID
- assignment title

Optional:

- due date

### Student enrollment

Requires:

- course offering selection
- student email

### Student unenrollment

Requires:

- course offering selection
- student email

### Staff assignment

Requires:

- course offering selection
- staff email
- role (`TA` or `INSTRUCTOR`)

### Staff unassignment

Requires:

- course offering selection
- staff email

---

## Important Current Constraints

These are especially important for UX and demonstrations.

### 1. User lookup is email-based, not directory-based

The website currently uses email entry for enrollment and staff assignment.

The website does **not** provide:

- a searchable student directory
- a searchable staff directory
- autocomplete or account discovery inside the page

The backend resolves the entered email to the target Cognito user and stores the
resolved `sub` internally.

This is functional for development but not a polished admin UX yet.

### 2. Submission review is now part of the website

The website now supports a review workflow from the dashboard:

- submission rows open a submission detail view
- assigned staff can add comments
- assigned staff can save draft or published grades
- staff can mark a submission as needing revision
- students can view feedback and upload a revised version when allowed
- file downloads are available per submission version

Important limitation:

- dashboard filtering by assignment and status is currently handled in the browser
  after course submissions are loaded

### 3. Course access is assignment-based, not global by role

Being in the `Staff` group is not enough by itself.

Staff must also be assigned to a course offering before they can manage it.

### 4. Upload is student-only

Staff cannot create submissions through the upload flow.

### 5. Current portal is a single-page vanilla HTML application

This matters for UX expectations:

- no multi-page app shell
- no design-system layer
- no complex component framework

Everything is currently implemented in one main `index.html` page.

---

## What the UX Team Should Treat as "Current Platform Reality"

When designing around the implemented platform, the UX team should assume:

- course offerings are term-aware
- staff users start the setup flow
- course instructors assign additional staff when needed
- students only upload after enrollment
- staff and student onboarding to a course is still operationally manual because there
  is no searchable user directory in the page
- the strongest existing web experiences are:
  - course offering creation
  - assignment setup
  - enrollment
  - student submission upload
  - submission list viewing
  - staff review comments and grading
  - student revision upload on an existing submission

---

## Recommended UX Framing for Demos

If the team needs to explain the platform simply, the clearest summary is:

> Staff create a term-based course offering, add assignments, enroll students,
> and then students submit work to those assignments through a guided upload flow.

That description best matches the current implemented website behavior.
