# Agentci-AI-Expense-Tracker
A demo project for demonstrating how we can use Agentic AI approach in SDLC for expense tracker web application

## Run the FastAPI + Bootstrap application

```powershell
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>.

## Run the Streamlit interface

Install the dependencies in `requirements.txt`, then run:

```powershell
streamlit run streamlit_app.py
```

Open <http://localhost:8501>. Both interfaces use the same service, validation rules, repository, and SQLite database. The default local database is `data/expenses.sqlite`.

## Deploy the Streamlit interface

Push the repository branch to GitHub, then create an app in Streamlit Community Cloud using this repository, the branch containing `streamlit_app.py`, and `streamlit_app.py` as the entry point. Streamlit Cloud installs dependencies from `requirements.txt`.

The app uses local SQLite by default. Streamlit Community Cloud does not guarantee persistence of files written by the running app, so expenses may be lost when the app restarts or its environment changes. Use an external persistent database before relying on it for real records. The shared app has no sign-in; treat the URL as public and do not enter confidential expenses.

The existing Dockerfile continues to run the FastAPI application.
