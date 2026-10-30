# Feature Specification 001 — Package and Attendance Management

**Status:** Draft for validation

## 1. Problem definition

The yoga studio currently uses paper cards to track class packages. These cards can be lost, and students and instructors may disagree about the number of remaining classes.

The studio needs a reliable way to register attendance, deduct classes from purchased packages, and allow students to verify their balances.

## 2. Goal

Implement a digital class package and attendance management feature that maintains accurate balances, prevents duplicate deductions, and preserves an auditable history.

## 3. Users

- **Administrator:** Creates packages, manages records, and corrects attendance errors.
- **Instructor:** Views the shared student directory and confirms attendance for authorized sessions.
- **Student:** Views personal package balances and attendance history.

## 4. Proposed solution

### 4.1 Package management

- The administrator can assign a new package to a student.
- The default package contains 10 classes.
- The administrator can select a different positive integer as the package size.
- Each package receives a unique identifier and creation timestamp.
- Each package maintains its original class quantity and remaining balance.
- Students may have multiple independent packages.

### 4.2 Attendance registration

- Attendance must be linked to an identifiable class session.
- The instructor or administrator selects a student and confirms their attendance.
- The system checks whether the student has an available class balance.
- If multiple packages are available, the system deducts one class from the oldest available package.
- Successful confirmation reduces the selected package's balance by exactly one.
- The system records the student, session, package, responsible user, and confirmation timestamp.
- The application prevents duplicate active attendance records for the same student and session.

### 4.3 Validation

- Attendance cannot be confirmed without an available package balance.
- Package balances cannot become negative.
- An attendance confirmation must not deduct more than one class.
- Simultaneous requests must not result in duplicate deductions or inconsistent balances.
- Unauthorized users cannot modify attendance or package balances.

### 4.4 Corrections

- Only the administrator can reverse an attendance record.
- A correction must include a reason.
- Reversing attendance restores one class to the original package.
- The original record and correction remain available in the audit history.
- An already reversed attendance record cannot be reversed again.

### 4.5 Student view

Students can consult:

- Their available class balance.
- Individual package information.
- Their attendance history.
- Any recorded attendance corrections affecting their packages.

Students cannot modify these records or access another student's information.

## 5. Acceptance criteria

**AC-01 — Package creation**

Given an administrator creates a new package for a student, when the administrator confirms a valid positive integer quantity, then the system creates an independent package with that initial and remaining balance. When no custom quantity is provided, the default is 10 classes.

**AC-02 — Correct attendance deduction**

Given a student has available classes, when an authorized instructor confirms attendance for a specific session, then exactly one class is deducted from the oldest package with available balance, and an attendance record is saved with the responsible user and timestamp.

**AC-03 — Invalid or duplicate attendance**

Given a student has no available classes or already has an active attendance record for a session, when another confirmation is attempted, then the operation is rejected without changing package balances. Concurrent duplicate requests must not create multiple deductions.

**AC-04 — Auditable correction**

Given a previously confirmed attendance record, when the administrator reverses it with a reason, then one class is restored to the original package, the correction is logged, and the original attendance information remains available. A second reversal is rejected.

**AC-05 — Authorized access and consultation**

Given an authenticated student, when the student accesses the application, then they can view only their own packages, available balances, and attendance history. They cannot modify those records or retrieve another student's records.

## 6. Out of scope

- Class reservations.
- Waiting lists.
- Automated notifications.
- Payment processing.
- Package expiration.
- Video lessons and online store.

## 7. Open decisions

- Whether the administrator and instructors can confirm attendance for past or future sessions.
- Whether corrected attendance can be registered again for the same student and session.
- How class sessions will be created and identified in the initial implementation.

These questions must be resolved before implementation.
