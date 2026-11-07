# Management Demo Checklist — Smart Expense Management Portal

**Role:** QA Engineer  
**Date:** 2026-11-07  
**Branch:** `feature/date-range-filter`  
**Verdict:** Ready for a local management demo of the four shipped features. Not ready to present a date-range filter. That behavior is not in this branch.

Re-run the checks in this list the morning of the demo. The last full automated run, from the build, was 25 passed, followed by a browser pass of add, list, category filter, and dashboard.

## Before the room

1. From the project root, install dependencies if this machine has not run the app: `python -m pip install -r requirements.txt`
2. Run `python -m pytest -q` and confirm the suite passes.
3. Start the app with `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
4. Open `http://127.0.0.1:8000/`. It redirects to the dashboard.
5. Confirm the browser can load Bootstrap from `cdn.jsdelivr.net`. The layout depends on that network.
6. Use a database you control. The default file is `data/expenses.sqlite`. If old demo rows are still there, move that file aside so the story starts from an empty dashboard.
7. Do not claim a date-range filter. The expense page filters by category only.

## Demo flow

Keep dates on or before today. A future date is rejected. Amounts must be greater than zero and have at most two decimal places. Categories are Travel, Meals, Supplies, Utilities, and Other.

| Step | Do this | What the room should see |
| --- | --- | --- |
| 1 | Open `http://127.0.0.1:8000/` | Dashboard. Total is `0.00`. Copy reads "No category totals yet." |
| 2 | Choose **Add expense**. Enter title `Client visit`, amount `48.00`, category `Travel`, date `2026-11-01`. Save. | Redirect to the expense list. One row: Client visit, Travel, 2026-11-01, 48.00. |
| 3 | Add a second expense: `Team lunch`, `25.50`, `Meals`, `2026-11-06`. | List shows Team lunch first, then Client visit. Newest date is first. |
| 4 | Set the category filter to `Meals` and press **Filter**. | Only Team lunch remains. |
| 5 | Press **Clear**. | Both rows return. |
| 6 | Open **Dashboard**. | Total `73.50`. Meals `25.50`. Travel `48.00`. |
| 7 | Optional, if time allows. Start another expense with amount `0` and save. | The form stays up, the entered values remain, and the message is "Amount must be greater than 0." Nothing new appears on the list. |

Stop after the dashboard unless someone asks for the validation step. Do not open `/docs` unless asked. There is no edit or delete.

Suggested narration order if the audience cares about the build process: product note, requirements, architecture, working portal, test run, security report. Those files are `docs/prd.md`, `docs/requirements.md`, `docs/architecture.md`, `docs/security-report.md`, and `docs/agentic-sdlc-summary.md`.

## Talking points

- An employee can record an expense, review the full list, narrow it to one category, and see the total plus the total per category.
- The same rules serve the pages and the JSON API. A bad amount or category is rejected before it is stored.
- Amounts are stored as cents, so the dashboard total is the sum of the stored rows, not a separate figure.
- The category filter changes the list only. The dashboard still shows every expense.
- The portal was produced through an agentic lifecycle: requirements, architecture, implementation, automated tests, and a security review. The security review did not change the code.
- This release is a local demo. There is no login. Anyone who can open the app can read and add expenses.

## Risks

| Risk | What happens in the room | Likelihood |
| --- | --- | --- |
| Date-range question | The branch is named `feature/date-range-filter`, but the screen only filters by category. Promising a date filter will fail live. | High if the branch name is mentioned without a correction |
| No network | Bootstrap CSS and JavaScript come from a CDN. The page still works, but it will look unstyled. | Medium |
| Future date or blank amount | The form returns an error and does not save. A presenter who picks tomorrow's date will look blocked. | Medium |
| Leftover rows | An existing `data/expenses.sqlite` changes the totals and spoils the empty-dashboard opening. | Medium |
| Typo after save | There is no edit or delete. A wrong title stays on the list and in the total. | Medium |
| Port already in use | Uvicorn fails to start if something else is bound to port 8000. | Low |
| Security question | The honest answer is in `docs/security-report.md`: unauthenticated access is accepted only on the local machine. The container listens on all interfaces if that image is published. | Low unless the audience asks |

## Backup plans

1. **Seed the database before the meeting.** Add the two sample expenses above, then start the story on the list and dashboard. Skip live data entry if typing is the worry.
2. **If the page is unstyled,** continue. The labels, table, and totals are still in the HTML. Say the stylesheet host is unreachable and keep the flow.
3. **If the browser fails,** run the API from the same machine:
   - `GET http://127.0.0.1:8000/api/dashboard`
   - `GET http://127.0.0.1:8000/api/expenses?category=Meals`
   The totals and the filter use the same service as the pages.
4. **If the app will not start,** show the last passing test summary and walk `docs/agentic-sdlc-summary.md`. Do not invent a live result.
5. **If a bad row is saved,** do not hunt for a delete button. Say deletion is out of scope and continue with the filter and dashboard. The extra row will be included in the total, so announce the new total rather than the rehearsed `73.50`.
6. **If asked for a date filter,** say it is not in this build. Show the category filter and the date column instead.

## Key achievements

- The product scope is implemented: add, view, category filter, and dashboard, on FastAPI, SQLite, and Bootstrap.
- Field rules are shared. Invalid title, amount, category, and date values are rejected and are not stored.
- The list sorts by newest expense date. An unknown category does not return a partial list.
- Dashboard totals match the stored amounts. For the sample pair, the total is `73.50`.
- Automated coverage exists for the service rules, SQLite access, and the HTTP pages and API. The recorded run was 25 passed.
- A security review is written, with the access-control limit stated plainly for this local release.
- Docker packaging is defined. The database file stays on a volume and is not copied into the image.
- Human gates from `rules.md` were kept for this work: no secrets were added, `.env` was not edited, and the demo does not require a push to main.

## Demo close

End on the dashboard. The sentence to leave with the room: employees can record spending, slice it by category, and see the total from the same stored amounts. The next product decision, if the audience asks, is authentication before the app is opened beyond the local machine.
