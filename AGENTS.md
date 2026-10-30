# AGENTS.md — Senda Yoga

## 1. Project overview

Senda Yoga is a web application for a small yoga studio managed by one administrator and two instructors.

The application will replace paper-based class packages with reliable digital records. Future versions may support class reservations, waiting lists, and notifications.

The first feature is **Package and Attendance Management**.

## 2. User roles and permissions

The application supports three roles:

### Administrator
- Manages the studio, instructors, students, and class packages.
- Can view all student records and attendance histories.
- Can perform authorized administrative corrections.

### Instructor
- Can consult the shared student directory.
- Can view students' class packages and available balances.
- Can register attendance for authorized sessions.
- Does not own individual student records or packages.

### Student
- Can view their own packages, available balance, and attendance history.
- Cannot directly modify packages, attendance records, or balances.
- Cannot access another student's information.

## 3. Shared student model

- Students belong to the studio, not to individual instructors.
- Students may attend classes with either instructor.
- Both instructors use the same authoritative student records, packages, and attendance history.
- Access to student information must follow role-based permissions.

## 4. Class package model

- Each package acquisition creates an independent record.
- Each package maintains its own original class quantity and remaining balance.
- The default package size is 10 classes, but authorized users may create packages with a different positive number of classes.
- A student may have multiple packages.
- The application may display an aggregated balance while preserving individual package records.
- Package balances must remain consistent and cannot become negative.
- Changes affecting balances must be traceable.

Detailed consumption order, attendance confirmation, and correction rules belong to the corresponding feature specification.

## 5. Product principles

- All user-facing content must be in Spanish.
- The application must be responsive, prioritizing mobile usability.
- The interface must be intuitive for users without technical experience.
- Personal information must be protected.
- The system must display understandable confirmation and error messages.
- Business records must persist across sessions.
- Critical operations must be reliable and auditable.

## 6. Development principles

- Implement only functionality included in the active specification.
- Avoid unnecessary complexity and dependencies.
- Separate business logic from presentation where practical.
- Enforce access permissions and validate inputs on the server.
- Protect operations that modify balances from duplicate or conflicting updates.
- Use fictitious student data during development.
- Never commit credentials, secret keys, or real personal data to the repository.
- Provide automated tests for critical business rules.

## 7. Brand and design

The application should convey calmness, simplicity, and trust.

Follow the project's `yoga-brand` skill for visual design instructions.

Visual styling must preserve usability, readability, and accessibility.

## 8. Agent workflow

For each new feature:

1. Read this file and the active feature specification.
2. Identify ambiguities or conflicting requirements.
3. Use the relevant skills when implementing the interface.
4. Implement only the requested feature.
5. Verify the acceptance criteria with tests.
6. Report successful tests, failures, and known limitations.
7. Do not silently invent business rules.

When a failed implementation reveals unclear requirements, clarify the specification before revising implementation instructions.

## 9. Initial scope

The first feature includes:

- Creating and assigning class packages.
- Viewing remaining classes.
- Registering attendance.
- Maintaining an auditable attendance history.
- Correcting attendance records according to defined permissions.

The first feature excludes:

- Class reservations and waiting lists.
- Automated notifications.
- Online payments.
- Video lessons and routines.
- E-commerce.

These may be developed in future iterations.
