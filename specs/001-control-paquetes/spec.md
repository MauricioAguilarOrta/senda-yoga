# Feature Specification 001 — Package and Attendance Management

**Status:** Ready for implementation  
**Product:** Senda Yoga  
**Feature:** Digital class packages and attendance validation

## 1. Problem

The studio currently tracks class packages with paper cards, which can be lost and make attendance and remaining balances difficult to verify.

## 2. Goal

Maintain independent class packages, deduct only confirmed attendance, prevent duplicate charges and negative balances, preserve corrections, and let students verify their own records.

## 3. Roles

- **Administrator:** Registers students, creates packages and sessions, may confirm attendance for any session, and may reverse incorrect attendance with a reason.
- **Instructor:** Consults the shared student directory and balances; confirms attendance only for sessions assigned to them. Cannot create packages or reverse attendance.
- **Student:** Consults only their own packages, balances, and attendance history; cannot modify records.

## 4. Functional design

### 4.1 Student records and access accounts

- The administrator can register a student through a basic interface.
- A student record can exist without a user account. Creating a student does not automatically grant application access.
- Store only the minimum personal data required for this MVP: the student's name and an optional email address.
- Email may remain blank until an access account is activated. The account activation workflow is outside this feature.
- Demo accounts and development records must use fictitious data.

### 4.2 Packages

- Each package belongs to exactly one student and has a unique ID, creation timestamp, original quantity, and remaining quantity.
- Default quantity: **10 classes**; administrators can enter another positive integer.
- Each acquisition creates a **separate package**; a student may own several.
- Show both individual package balances and a total available balance.
- Packages have **no expiration** in this MVP.

### 4.3 Previously created sessions

- The administrator creates each session before attendance can be registered.
- A session has a unique ID, title, scheduled start date/time, and assigned instructor.
- Two sessions may occur on the same day; they are still distinct.
- Attendance cannot be confirmed before the session's scheduled start.
- Once a session has any attendance record, including a subsequently reversed attendance, its scheduled start and assigned instructor cannot be changed.
- Use the studio's configured time zone (default for this project: `America/Mexico_City`).

### 4.4 Attendance confirmation

- An authorized instructor or administrator selects an existing session and a student.
- Check permissions, session start, available balance, and whether the student already has an active confirmed attendance for that session.
- Deduct **exactly one class** from the oldest package with a positive balance, ordered by creation timestamp and then package ID (FIFO).
- Persist student ID, session ID, charged package ID, authorizing user ID, and confirmation timestamp.
- Deduction and attendance creation must be **atomic**: both succeed or neither succeeds.
- Concurrent requests must not create duplicate active attendance records or allow balance below zero.
- Confirmation and reversal operations must use one consistent database row-locking order: student first, session second, relevant attendance records third (ordered by attendance ID when more than one is inspected), and package last. A reversal may read the immutable student and session identifiers needed to acquire those locks, but must revalidate the attendance after locking.
- Database uniqueness and balance constraints remain the final safeguard if concurrent requests race despite application-level checks.
- Booking a session does not deduct a class; reservations are outside this feature.

### 4.5 Corrections

- Only the administrator may reverse a confirmed attendance; a nonblank reason is mandatory.
- Restore exactly one class to the **same package** originally charged.
- Preserve the original attendance and append a correction record including reason, administrator, and timestamp.
- Reject a repeated reversal of the same attendance record.
- Once reversed, a new confirmation for the same student and session is allowed if all normal validation rules pass; retain the entire history.

### 4.6 Student consultation

- Students can view their total balance, individual package original and remaining quantities, attendance history, and corrections affecting their packages.
- Enforce student data isolation and authorization on the server, not just in the interface.
- Return `404 Not Found` when an authenticated user requests a private record belonging to another student, so the response does not disclose whether that record exists.
- Return `403 Forbidden` for an explicit operation that the authenticated role is not permitted to perform, such as an instructor attempting to reverse attendance or create a package.

## 5. Acceptance criteria (verifiable)

**AC-01 — Package creation and consultation.** Given an administrator assigns a package to a student, when a valid positive integer is submitted, then create a separate package with equal original and remaining quantities; default to 10 if no custom quantity is provided. The student's total and package-level balances reflect the new record.

**AC-02 — Authorized attendance with FIFO.** Given a previously created session has reached its scheduled start and an authorized instructor or administrator confirms a student with available classes, exactly one class is deducted from the oldest available package and a confirmation is saved with the student, session, charged package, actor, and timestamp.

**AC-03 — Validation and consistency.** Given an unauthorized actor, a future session, insufficient balance, or an existing active attendance for the same student and session, confirmation is rejected without changing balances or creating an active attendance record. Concurrent requests cannot cause duplicate deductions or negative balances.

**AC-04 — Auditable reversal.** Given a confirmed attendance, when the administrator reverses it with a nonblank reason, one class is restored to the originally charged package while both original and correction records remain available. A second reversal is rejected; a new otherwise-valid confirmation can be made.

**AC-05 — Private student records.** An authenticated student can view only their own packages, total balance, attendance, and related corrections; requests to view or modify other students' records are denied.

## 6. Example tests

- Create packages with default 10 and custom 5; verify independent records and aggregated balance.
- With balances 2 and 10, confirm attendance and verify the first becomes 1, the other stays 10, and the audit record identifies the charged package.
- Reject duplicate student-session confirmation, zero balance, future session, and an unauthorized instructor.
- Simulate simultaneous duplicate confirmations and verify no double deduction.
- Exercise confirmation and reversal concurrently and verify that the consistent lock order prevents deadlocks while preserving the correct balance and audit history.
- Reverse an attendance and verify the original package is restored, a reason and actor are logged, and repeated reversal is rejected.
- Verify a student receives `404 Not Found` when requesting another student's private record and `403 Forbidden` when attempting an explicitly prohibited operation.
- Register a student with only a name and another with a name and optional email; verify neither registration requires an access account.
- Verify that a session's scheduled start and assigned instructor cannot change after any attendance has been recorded, including after reversal.

## 7. Out of scope

Reservations, waiting lists, notifications, online payments, package expiration, recurring session generation, videos, and e-commerce.

## 8. Delivery evidence

Provide an executable application, documented local setup, fictitious seed data or demo accounts, automated tests mapped to AC-01 through AC-05, their actual execution results, and known limitations.

Do not claim tests passed unless they were executed successfully.
