# Smart University Academic Management System (SUAMS)

[![SUAMS CI Pipeline](https://github.com/shafi/SAUMS/actions/workflows/ci.yml/badge.svg)](https://github.com/shafi/SAUMS/actions)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Coverage: 95%](https://img.shields.io/badge/coverage-95%25-brightgreen.svg)](https://github.com/shafi/SAUMS)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.124.4-009688.svg)](https://fastapi.tiangolo.com)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org/)

SUAMS is a modular, high-reliability university academic management system engineered following the full Software Development Lifecycle (SDLC) for **CSE 3206 (Software Engineering)** at Rajshahi University of Engineering & Technology (RUET).

The application digitizes student admissions, semester advising, exam clearance form generation, teacher evaluation (Continuous Assessment & Final Exam marks), automated GPA processing, and multi-channel academic notifications.

---

## 1. System Architecture & Clean Separation of Concerns

The codebase enforces strict layered architectural boundaries:
```
                      ┌────────────────────────────┐
                      │    FastAPI HTTP Routers    │  (HTTP handling & parameter parsing)
                      │    (src/suams/*/router.py) │
                      └─────────────┬──────────────┘
                                    │ Pydantic Schemas (src/suams/schemas/)
                                    ▼
                      ┌────────────────────────────┐
                      │  Business Logic Services   │  (Domain validation & workflows)
                      │   (src/suams/*/service.py) │
                      └─────────────┬──────────────┘
                                    │
           ┌────────────────────────┴────────────────────────┐
           ▼                                                 ▼
┌───────────────────────────┐                     ┌───────────────────────────┐
│     Design Patterns       │                     │     SQLAlchemy ORM        │
│ (Factory, Strategy, Obs)  │                     │   (src/suams/models/)     │
└───────────────────────────┘                     └─────────────┬─────────────┘
                                                                ▼
                                                  ┌───────────────────────────┐
                                                  │ SQLite / PostgreSQL DB    │
                                                  └───────────────────────────┘
```

- **`routers/`**: HTTP transport layer, request validation, response serialization, and RBAC security dependencies.
- **`services/`**: Core academic rules, credit limit enforcement, basis-path evaluation, and state transition workflows.
- **`models/`**: SQLAlchemy 2.0 declarative database entities with relationships and constraints.
- **`schemas/`**: Pydantic v2 schemas for strongly-typed data validation and serialization.

---

## 2. Mandatory Design Patterns

The system incorporates three design patterns spanning two Gang of Four (GoF) categories:

### 1. Creational: Factory Pattern (`src/suams/users/factory.py`)
- **Role:** Decouples user dashboard creation from client endpoints.
- **Implementation:** `UserDashboardFactory.create_dashboard(user)` instantiates role-specialized payloads (`StudentDashboard`, `TeacherDashboard`, `AdminDashboard`, `ControllerDashboard`) based on the authenticated user's `UserRole`.
- **Extensibility:** New roles can be introduced without altering existing dashboard consumption logic.

### 2. Behavioral: Strategy Pattern (`src/suams/results/grading.py`)
- **Role:** Encapsulates interchangeable grading scale algorithms.
- **Implementation:**
  - `GradingStrategy` (Abstract Base Strategy).
  - `StandardRUETGradingStrategy`: Standard 4.00 CGPA RUET scale ($A+$ down to $F$).
  - `PassFailGradingStrategy`: Binary evaluation scale ($P$ / $F$) for audit and non-credit courses.
  - `calculateGPA(ca_marks, final_marks, strategy)`: Injects strategies at runtime without modifying result processors.

### 3. Behavioral: Observer Pattern (`src/suams/notifications/publisher.py`)
- **Role:** Broadcasts academic events asynchronously to decoupled subscribers.
- **Implementation:**
  - `AcademicEventPublisher` (Subject): Manages observer subscriptions via `attach()` and `detach()`, and broadcasts via `notify()`.
  - `InAppObserver`: Persists in-app notification logs to the database.
  - `EmailObserver`: Formats academic emails and routes them via `EmailDispatcher` (mocked in tests).
  - `AnalyticsObserver`: Ingests operational telemetry.
- **Triggers:** Automatically invoked on `RESULT_PUBLISHED` and `REGISTRATION_APPROVED`.

---

## 3. Quickstart & Installation

### Prerequisites
- Python 3.12+
- Google Chrome or Chromium (for Selenium E2E tests)

### Local Environment Setup

```bash
# 1. Clone the repository
git clone https://github.com/shafi/SAUMS.git
cd SAUMS

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
# Start FastAPI application with live reload
uvicorn suams.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Specifications:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Interactive Student Web Portal:** [http://127.0.0.1:8000/portal](http://127.0.0.1:8000/portal)
- **OpenAPI 3.1 JSON Export:** [docs/openapi.json](docs/openapi.json)

---

## 4. Test-Driven Development (TDD) & Quality Assurance

The project strictly follows the **Red-Green-Refactor** cycle with isolated unit, integration, and E2E test suites.

```bash
# Run full test suite with coverage
pytest --cov=src/suams --cov-report=term-missing
```

### Coverage Report Summary (95% Total Coverage)
```text
Name                                   Stmts   Miss  Cover
----------------------------------------------------------
src/suams/__init__.py                      1      0   100%
src/suams/auth/dependencies.py            36      7    81%
src/suams/auth/router.py                  18      1    94%
src/suams/auth/security.py                25      2    92%
src/suams/auth/service.py                 18      0   100%
src/suams/config.py                       11      0   100%
src/suams/database.py                     15      0   100%
src/suams/exams/router.py                 26      2    92%
src/suams/exams/service.py                50      5    90%
src/suams/main.py                         26      2    92%
src/suams/models/* (all models)          118      0   100%
src/suams/notifications/publisher.py      77      1    99%
src/suams/portal.py                        4      0   100%
src/suams/registration/router.py          42      5    88%
src/suams/registration/service.py         75      9    88%
src/suams/results/grading.py              43      2    95%
src/suams/results/router.py               17      0   100%
src/suams/results/service.py              27      1    96%
src/suams/schemas/* (all schemas)         87      0   100%
src/suams/users/factory.py                51      0   100%
src/suams/users/router.py                 14      1    93%
src/suams/users/service.py                13      0   100%
----------------------------------------------------------
TOTAL                                    824     38    95%
======================= 80 passed in 26.35s ========================
```

### White-Box & Black-Box Testing Methodologies
1. **White-Box Basis-Path Testing:**
   - Evaluates all 4 linearly independent paths of `evaluateResult(is_enrolled, attendance, total_marks)` ($V(G) = 4$).
   - `TC-WB-01` (`NOT_ENROLLED`), `TC-WB-02` (`DISQUALIFIED`), `TC-WB-03` (`PASS`), `TC-WB-04` (`FAIL`).
2. **Boundary-Value Analysis (BVA):**
   - Credit limit load: $11.0$ (invalid), $12.0$ (min valid), $24.0$ (max valid), $25.0$ (invalid).
   - GPA boundary evaluation: $-5.0$ (invalid), $39.0$ ($F$), $40.0$ ($D$), $80.0$ ($A+$), $105.0$ (invalid).
3. **Equivalence Partitioning (EP):**
   - Valid pass/fail grade partitions across standard RUET scales and pass/fail audit scales.
4. **End-to-End (E2E) Browser Testing with Selenium:**
   - Automated headless browser test (`tests/e2e/test_student_journey.py`) verifying user login, course registration, and academic results clearance.

---

## 5. CI/CD Pipeline

Continuous Integration is automated via GitHub Actions ([.github/workflows/ci.yml](.github/workflows/ci.yml)):
- Triggers on every push and pull request to `main` and `feature/**`.
- Sets up Python 3.12 and Google Chrome headless environment.
- Executes `pytest --cov=src/suams --cov-report=term --cov-report=xml`.
- Preserves coverage artifacts for verification.

---

## 6. Git Branching Strategy & Protocol

Development adheres strictly to isolated feature branch workflows:
- `feature/auth-rbac`: Milestone 1 — Project scaffolding, database models, JWT RBAC, and Factory pattern.
- `feature/course-reg`: Milestone 2 — Boundary-Value Analysis and course registration workflow.
- `feature/exam-eval`: Milestone 3 — White-Box Basis-Path testing and exam form generation.
- `feature/results-notify`: Milestone 4 — Strategy pattern, Equivalence Partitioning, and Observer pattern.
- `feature/ci-docs`: Milestone 5 — GitHub Actions CI, Selenium E2E testing, and technical documentation.
