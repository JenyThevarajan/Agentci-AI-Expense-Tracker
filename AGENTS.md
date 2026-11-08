Read rules.md and docs/ (prd, requirements, architecture) before any task.
Stack: FastAPI, SQLAlchemy, SQLite, Jinja2 + Bootstrap, pytest.
Layers: routers -> service -> repository. No SQL in routers, no HTTP in service.
Run: uvicorn app.main:app --reload
Test: pytest -v
Rules: tests for every feature, validate all input, never commit secrets, never push to main, ask before deleting files, update docs for any scope change.