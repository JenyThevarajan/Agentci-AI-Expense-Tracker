# Agentic SDLC Summary — Smart Expense Management Portal

**Role:** Technical Project Manager  
**Date:** 2026-11-07  
**Sources:** `rules.md`, `docs/prd.md`, `docs/requirements.md`, `docs/architecture.md`, the application, the test suite, and `docs/security-report.md`

This project moved from a short product description to a working local portal through a sequence of agent roles. Each role consumed the previous artifacts and produced the next one. The human set the guardrails and the product scope, then directed each step.

## Lifecycle

| Step | Role | Main output |
| --- | --- | --- |
| 1 | Human | `rules.md`, `docs/prd.md` |
| 2 | Business Analyst | `docs/requirements.md` |
| 3 | Solution Architect | `docs/architecture.md` |
| 4 | Developer, with QA and DevOps deliverables | Application, tests, Docker artifacts |
| 5 | Security | `docs/security-report.md` |
| 6 | Human | Approval gates that were not crossed |

## 1. Business Analyst Agent Activities

The Business Analyst started from `docs/prd.md` and `rules.md`. The product note named four features and the stack. It did not define field limits, categories, or what “done” meant.

The analyst wrote `docs/requirements.md` and fixed the open points as explicit assumptions: one shared expense list, five categories, a positive amount, and a date that cannot be in the future. The document contains:

- In-scope and out-of-scope boundaries, including no login, edit, or delete in this release
- Functional requirements FR-1 through FR-10
- User stories US-01 through US-04 for add, view, filter, and dashboard
- Acceptance criteria for valid input, each invalid field, empty states, and dashboard totals
- Non-functional requirements for validation, OWASP practices, SQLite, Pytest, Bootstrap, and Docker
- A traceability table from stories back to the product requirements

That document became the contract for architecture, implementation, and testing.

## 2. Architect Agent Activities

The Solution Architect read the product requirements, the requirements document, and the project rules, and wrote `docs/architecture.md`. No application code was produced in that step.

The architect chose one FastAPI service that renders Bootstrap pages and exposes a JSON API, with SQLite as the only database. The design splits routes, an expense service, and a repository so the rules can be tested without HTTP or SQL. Amounts are specified as integer cents. The document records seven decisions, including no authentication in this release and keeping secrets out of the image.

It also specifies:

- The `expenses` table and the list, filter, and dashboard query shapes
- `POST /api/expenses`, `GET /api/expenses`, `GET /api/dashboard`, and `/health`
- The browser routes for the dashboard, the list, the filter, and the add form
- The error model, the security controls, the container shape, and the unit-test cases

The developer used this document as the build specification.

## 3. Developer Agent Activities

The Developer read the rules, the product requirements, the requirements, and the architecture, then built the working portal.

The application is a layered FastAPI service:

- `app/validation.py` and `app/service.py` apply the shared field rules and totals
- `app/repository.py` and `app/models.py` store expenses in SQLite through SQLAlchemy
- `app/routers/web.py` renders the Jinja2 and Bootstrap 5 pages
- `app/routers/api.py` serves the JSON API
- Unexpected failures return a generic message and keep the detail in the server log

The pages support the dashboard, add expense, view expenses, and filter by category. A valid save redirects to the list. An invalid save redisplays the form with the entered values and the field error.

The same turn also produced the test suite and the Docker artifacts, because the project rules require tests for every feature and Docker artifacts for deployment. Those contributions are described in the QA and DevOps sections.

## 4. QA Agent Activities

QA coverage was produced with the build, from the acceptance criteria and the architecture test plan. There was no separate QA-only turn.

The suite has three layers:

- `tests/test_service.py` checks add, view, filter, and dashboard rules with an in-memory store, including each invalid field
- `tests/test_repository.py` checks SQLite writes, ordering, filtering, totals, and a title that contains quotes
- `tests/test_api.py` checks the pages, the form, the JSON API, and the error responses

The automated run finished with 25 tests passed. A browser pass then walked the running portal: an invalid amount stayed on the form, a Travel expense and a Meals expense appeared in the list, the category filter and the empty filter behaved as specified, and the dashboard total was 73.50 for those two rows. An unknown category was rejected and did not show the stored expenses.

## 5. Security Agent Activities

The Security Agent reviewed the application, templates, dependency file, ignore rules, and Docker definition after the build. Application code was not changed. The result is `docs/security-report.md`.

The report maps the portal to the OWASP Top 10 and records one high finding, three medium findings, and four low findings. The high finding is that any caller who can reach the process can read and add expenses, and the container listens on all interfaces. That matches the accepted local-demo decision and becomes a release risk if the port is published.

The review also records the controls already in place: parameterized queries, an allow-listed category, escaped templates, shared validation, a CSRF cookie on the HTML form, and generic client errors.

## 6. DevOps Agent Activities

DevOps artifacts were produced with the application build. There was no separate DevOps-only turn.

The deliverables are:

- `requirements.txt` for the FastAPI runtime and the test tools
- `Dockerfile`, which runs Uvicorn and reads the SQLite path from `DATABASE_PATH`
- A Docker volume at `/data` so the database file is not baked into the image
- `.dockerignore`, which keeps `.git`, tests, docs, and local database files out of the build context
- `.gitignore`, which keeps `data/`, SQLite files, and virtual environments out of source control

The portal was started locally with Uvicorn on `127.0.0.1:8000` and used for the browser check. The image was defined and was not published.

## 7. Human Approval Activities

The human directed the lifecycle and supplied the two inputs every later role depended on.

- Wrote the ten guardrails in `rules.md`, including no secrets in source, no `.env` edits without approval, no direct push to main, tests for every feature, OWASP practices, approval before file deletion, local SQLite, documentation, Docker artifacts, and explained decisions
- Wrote the product objective, the four features, the stack, and the security expectations in `docs/prd.md`
- Asked for requirements and architecture before any code, then asked for the application, then the security report, then this summary

The approval gates were observed. No `.env` file was created or edited. No secrets were added. No files were deleted. No commit was created, and nothing was pushed to main. Those actions remain available for the human to request.

## How the roles fit together

The human defined the problem and the limits. The Business Analyst turned that problem into stories and acceptance criteria. The Architect turned the stories into a service shape, an API, and a schema. The Developer implemented that shape, and the same build carried the QA evidence and the DevOps packaging the rules required. The Security Agent reviewed the result and left the code unchanged. The next human decision is whether to accept the local demo as built or to act on the security recommendations before any wider deployment.
