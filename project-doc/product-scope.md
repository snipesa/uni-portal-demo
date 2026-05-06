# University Assignment Submission and Grading Portal

## Overview
This project is to build a secure web portal where students submit assignment files and instructors or teaching assistants review, comment, and grade those submissions. The platform should support collaboration between instructors, track submission versions, and maintain clear role-based access.

## Business Use Case
The portal solves assignment workflow issues in universities by providing one secure place for submission, review, feedback, and grading with version history and auditability.

## Primary Users and Roles
### 1. Student
- Upload assignment files
- Upload revised versions (v1, v2, v3...)
- View instructor or TA comments
- View grade and grading status

### 2. Instructor / TA
- View all submissions for courses and terms they manage
- Download submitted files
- Add comments and feedback
- Assign and update grades
- Share submission access links with other authorized instructors

## Core Website Capabilities
1. Authentication and authorization with clear role separation (Student, Instructor, TA)
2. Assignment submission flow with secure file upload
3. Version history for each submission attempt
4. Commenting and collaboration on each submission
5. Grading workflow with status tracking
6. Controlled sharing for instructor-side collaboration
7. Responsive interface for desktop and mobile use
8. Audit-friendly tracking of key actions (upload, comment, grade updates)

## Why This Use Case Is Strong
1. Version control is natural and essential for assignment revisions
2. Comments and grading are core collaboration requirements
3. Role-based access boundaries are clear and realistic
4. It directly matches secure file sharing + collaboration goals

## Out of Scope for This Document
This document defines product and business scope only. Technical architecture, cloud resources, and implementation tooling are documented separately.

## References
- [Architecture Diagram (v3)](./arch-diagramv3.png)
- [Technical Architecture and Tooling](./project-technical-architecture.md)
- [Platform Usage Guide](./platform-usage-guide.md)
