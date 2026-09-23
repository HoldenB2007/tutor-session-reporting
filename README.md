# Tutor Session Reporting

A web app for LVAEP (Literacy Volunteers of America, Essex/Passaic County) that replaces the paper
**Student Monthly Attendance & Achievement Form** ([`docs/`](docs/)). Tutors log sessions as they happen;
staff generate live monthly reports instead of aggregating paper forms by hand.

## Prompt

> LVAEP runs a tutoring program in which tutors are assigned students and meet with them over the course of a term. Tutors are responsible for recording each session they hold, including the date, the student, and the number of hours. Staff then need those records collected into monthly reports. The current reporting form is attached. Build a system to replace the old workflow and make it more efficient/intuitive.

## Stack

- **Django 6 + HTMX** — server-rendered pages; HTMX for popup flows without a JS build step
- **PostgreSQL** on Railway (SQLite locally)
- **ReportLab** for PDF export
- **Gunicorn + WhiteNoise** for serving on Railway

## Local development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Then open http://localhost:8000. Health check: http://localhost:8000/healthz/

## Demo accounts

`python manage.py seed_demo` creates one account per role plus sample assignments, ~2.5 months of
sessions (including absences), a few achieved goals, and one ended assignment. It is safe to re-run.
With `SHOW_DEMO_CREDENTIALS=1` the login page lists these accounts.

| Role | Username | Password |
|---|---|---|
| Staff | `staff` | `demo1234` |
| Tutor | `tutor.maria`, `tutor.james` | `demo1234` |
| Student | `student.ana`, `student.wei`, `student.samuel`, `student.fatima` | `demo1234` |

The staff account also has access to the Django admin at `/admin/` for creating real accounts and assignments.

## Environment variables

| Variable | Purpose | Local default |
|---|---|---|
| `SECRET_KEY` | Django secret | insecure dev key |
| `DEBUG` | `1` on, `0` off | `0` |
| `DATABASE_URL` | Postgres URL; unset → SQLite | unset |
| `ALLOWED_HOSTS` | comma-separated | `localhost,127.0.0.1` |
| `CSRF_TRUSTED_ORIGINS` | comma-separated origins | empty |
| `SHOW_DEMO_CREDENTIALS` | show seeded demo logins on the login page | `0` |
| `STAFF_CONTACT_EMAIL` | general staff address used in `mailto:` links | `info@lvaep.org` |
| `MEDIA_ROOT` | upload directory (Railway volume mount) | `./media` |

`RAILWAY_PUBLIC_DOMAIN` is picked up automatically when present.

## Deployment

Railway builds from `main`. The `Procfile` runs migrations and `collectstatic`, then starts Gunicorn.
Add a Postgres service and reference its `DATABASE_URL` in the web service's variables.
After the first deploy, run `python manage.py seed_demo` once from the service shell.

## Design decisions

### Product
1. **Three account types: Student, Tutor, Staff.** The Student role isn't in the prompt — it was added so students can see their own hours, goals achieved, and where/when they meet, and email their tutor. A student with multiple tutors sees each one listed.
2. **Strict data scoping.** Students see only their own data; tutors only their assigned students; staff see everything.
3. **Tutor home = a grid of their students** with search and filters (alphabetical, most recent, or by session date). Clicking a student opens a popup with four actions: Log session, Update goal progress, Update site/days/times, and End tutoring (visually separated, at the bottom).
4. **Logging a session requires a date**, then either hours tutored *or* an absence mark (tutor absent / student absent / holiday — the form's TA/SA/H codes).
5. **Goals are the form's fixed checklist** (Economic, Educational, Family, Societal/Community, Other), seeded from the PDF. Tutors check them off; only staff can edit the list.
6. **Ending tutoring needs a second confirmation** with a checkbox so it can't happen by accident. An ended assignment is reflected in the student's view, in staff reports, and in the tutor's future lookups.
7. **Staff home = report generator.** Reports are computed on demand from live data, shown on screen, and exportable as PDF. They are deliberately **not stored** — a report is always current.
8. **Four report types:** all tutors; one tutor and their students; one student; everything.
9. **Staff is a single shared login** with no profile — every staff member has identical capabilities.
10. **Profiles for students and tutors** (image, pronouns) via the top-right icon.
11. **Contact is via `mailto:` links**, not server-sent email. Students reach their specific tutor(s) or the general staff address; tutors reach specific students or the general staff address. No one emails an individual staff member.
12. **Placeholder for report subscriptions:** an email can be signed up to receive a category of monthly reports. Addresses are stored; automated sending is a future step.
13. **Security scope:** Django's defaults (hashed passwords, CSRF, sessions) plus role-based authorization. Field-level encryption of student data was considered and deliberately deferred.

### Technical
14. **Django + HTMX** over Flask/FastAPI/Next.js — auth, ORM, migrations, and the admin panel come built in, so build time goes to the product rather than plumbing.
15. **Railway** for hosting and Postgres — always-on, so reviewers opening the link never hit a cold start.
16. **ReportLab** for PDFs — pure Python, no system dependencies to break the deploy.
17. **No self-signup.** Staff create accounts in the admin. Demo accounts are seeded and shown on the login page so the app can be reviewed unattended.
18. **Functionality before styling.** The UI stays plain until the workflows are right.
