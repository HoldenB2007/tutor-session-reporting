# Tutor Session Reporting

**Live:** https://tutor-session-reporting-css.up.railway.app · **Repo:** https://github.com/HoldenB2007/tutor-session-reporting

A web app for **LVAEP** (Literacy Volunteers of America, Essex/Passaic County) that replaces the paper
*Student Monthly Attendance & Achievement Form*. Tutors log each session the moment it happens; students
can see their own progress; staff generate monthly (or any-range) reports from live data with one click
and export them as PDF.

---

## Why this exists

The prompt:

> LVAEP runs a tutoring program in which tutors are assigned students and meet with them over the course of a term. Tutors are responsible for recording each session they hold, including the date, the student, and the number of hours. Staff then need those records collected into monthly reports. The current reporting form is attached. Build a system to replace the old workflow and make it more efficient/intuitive.

The paper form ([`docs/`](docs/)) is one sheet per tutor–student pair per fiscal year: a 31 × 12 grid of hours,
absence codes (TA / SA / H), a checklist of achievement goals, a "stopped" box, and the tutoring site/days/times.
Tutors fill it in from memory at month-end; staff then re-key and total everything by hand. Two problems:
data arrives late and lossy, and the monthly report is manual work every single month.

This app fixes both. Sessions are recorded at the point of contact and reports are a query, not a chore.

---

## Try it

Log in at the live URL. The login page lists the demo accounts — every one uses password **`demo1234`**.

| Role | Username | What you'll see |
|---|---|---|
| Staff | `staff` | Report generator (landing page), email subscriptions, Django admin |
| Tutor | `tutor.maria` | 2 students; `tutor.james` has 3 incl. one ended assignment |
| Student | `student.wei` | Two tutors in the sidebar; `student.fatima` shows an ended assignment |

Suggested click-through: log in as **`staff`** → generate the *Everything* report for August 2026 → Export PDF.
Then **`tutor.maria`** → click a student card → log a session → check a goal → try *End tutoring* (it asks you to confirm).
Then **`student.wei`** → switch between tutors in the sidebar.

---

## What each role gets

**Tutor** — the most important user; this is the paper form, made live.
- Home is a grid of *my students* with search, A→Z / most-recent sort, and a "met between" date filter.
- Click a student → popup with four actions, each ending in **Update**:
  1. **Log session** — date is required; then hours tutored *or* an absence (tutor absent / student absent / holiday).
  2. **Update goal progress** — the form's fixed goal checklist, grouped by category; starred = federally reported.
  3. **Update site / days / times**
  4. **End tutoring** — red, at the bottom, needs last day + reason + a confirmation checkbox before **END** works.
- Ended students stay visible (dimmed) so history isn't lost. Email a student from their popup; contact staff from the page.

**Student** — added beyond the prompt because the data is *about* them.
- Left sidebar lists every tutor they have (ended ones dimmed). Main panel: where/when they meet, hours so far,
  goals achieved, recent sessions. **Email tutor** and **Contact LVAEP staff** buttons. Profile photo + pronouns.

**Staff** — one shared account, no profile; every staff member has the same powers.
- Landing page is the **report generator**: pick a report, a single month or a date range, **Generate**, **Export PDF**.
- Four reports: *All tutors* · *One tutor and their students* · *One student* · *Everything*.
  Tutor and Everything reports include a **session-detail section** — every session, grouped tutor → student → date —
  the electronic version of the paper grid.
- **Email subscriptions** (placeholder): sign an address up for a report category. Stored, not yet sent.
- **Django admin** for account and assignment management.

---

## Architecture

```
Browser ──HTTPS──▶ Railway (Gunicorn + Django 6) ──▶ Railway Postgres
                        │  WhiteNoise serves /static
                        │  Railway Volume at /app/media holds profile photos
                        └─ HTMX for the tutor popup flows (no JS build step)
```

### Apps

| App | Owns |
|---|---|
| `accounts` | `Profile` (role, pronouns, photo), login/logout, `role_required`, post-login routing, profile page, login-gated media serving, `seed_demo` |
| `tutoring` | `Assignment`, `Session`, `Goal`, `GoalAchievement`; tutor grid + popup actions; student dashboard |
| `reports` | `queries.py` (report builders), HTML report view, `pdf.py` (ReportLab), `ReportSubscription` + dry-run delivery command |
| `config` | Settings (all environment-driven), URL root, health check |

### Data model

```
User ──1:1── Profile(role ∈ {student, tutor, staff}, pronouns, image)

Assignment(tutor→User, student→User, subject, site, days, times, started_on, ended_on, end_reason)
   │  one row = one paper form; a student may have several (different tutors/subjects)
   ├── Session(date, hours | absence ∈ {TA, SA, H}, note)   ← DB constraint: exactly one of hours/absence
   └── GoalAchievement(goal→Goal, achieved_on)              ← unique per (assignment, goal)

Goal(category A–E, label, federally_reported, order)        ← seeded from the PDF by a data migration
ReportSubscription(email, kind)                             ← placeholder
```

Fiscal year (Jul–Jun) is derived from dates, never stored.

### Request flow worth knowing

- **Authorization is query scoping, not just decorators.** Every tutor view starts from
  `Assignment.objects.filter(tutor=request.user)` and every student view from `filter(student=request.user)`;
  `get_object_or_404` on that scoped queryset means guessing another tutor's assignment ID yields 404.
- **Popups are HTMX partials** swapped into one `<dialog>`. A successful action returns `204` with
  `HX-Trigger: closeModal, refreshGrid`; the page closes the dialog and re-fetches the grid.
- **Reports are pure functions.** `reports/queries.py::build_report()` returns plain dicts; the HTML view and the
  PDF view both call it with the same query string, so screen and export can't disagree. Nothing is cached or stored.

---

## Design decisions

Numbered so they can be referenced.

### Product
1. **Three account types — Student, Tutor, Staff.** Student wasn't in the prompt; it was added because the data is about them and giving them a read-only window (hours, goals, where/when, email tutor) costs little and builds engagement.
2. **Strict scoping.** Students see only their own data; tutors only their assigned students; staff see everything.
3. **Tutor home is a grid + search + filters**, not a form. Tutors think in students, not spreadsheets.
4. **Four actions per student in a popup**, every one ending in **Update**. Fewer screens, one mental model.
5. **Date is mandatory; then hours *or* absence.** Keeps the form's TA/SA/H codes but prevents an empty or contradictory record — enforced by a database check constraint, not just the form.
6. **Goals are the form's fixed list**, seeded from the PDF; only staff edit it (admin). Tutors check, never invent.
7. **End tutoring requires a second confirmation** with a checkbox. It's the one irreversible-feeling action, and it's visually separated in red at the bottom.
8. **Ended assignments remain visible everywhere** — dimmed on the tutor grid, badged on the student page, flagged in reports. History is data.
9. **Staff landing page is the report generator.** Reports are computed live on every request and **never stored** — the only way to guarantee a report is current. A single month or a rolling date range.
10. **Four report types** (all tutors / one tutor / one student / everything), plus per-session detail grouped by tutor and student so staff can see exactly what the paper grid showed.
11. **Staff is one shared login with no profile.** Every staff member has identical capability; there's nothing to personalize.
12. **Contact is `mailto:`, not in-app messaging.** Students → their tutor(s) or the general staff address; tutors → students or the general staff address. Nobody emails an individual staff member. Zero email infrastructure, zero moderation surface.
13. **Report-subscription placeholder.** Addresses and categories are stored and a dry-run command shows what would be sent; actual delivery (email backend + cron) is deliberately deferred.
14. **Profiles (photo + pronouns) for students and tutors**, reachable from the avatar top-right.
15. **Security scope:** Django's defaults (hashed passwords, CSRF, secure cookies, HSTS in production) plus role scoping. Field-level encryption of student data was considered and deferred as out of scope for an MVP.
16. **No self-signup.** Staff create accounts in the admin. Demo accounts are seeded and listed on the login page so the app can be reviewed unattended.
17. **Functionality before styling.** The UI is deliberately plain until the workflows are right; hover/focus states exist so clickable things read as clickable.

### Technical
18. **Django + HTMX** over Flask / FastAPI / Next.js. Auth, ORM, migrations, and the admin come built in, so build time went to the product. HTMX gives popup flows without a JavaScript toolchain.
19. **Railway** for hosting and Postgres — always-on, so a reviewer opening the link never hits a cold start. One vendor, one dashboard.
20. **ReportLab** for PDFs — pure Python, no system libraries to break a deploy.
21. **Goals via data migration**, not a fixture file — they exist on every fresh database with no manual step.
22. **Profile photos on a Railway Volume**, served through a `login_required` view. `MEDIA_ROOT` resolves `MEDIA_ROOT` env → `RAILWAY_VOLUME_MOUNT_PATH` → local `./media`.
23. **Every change on a branch → PR → merge to `main`**, which is what Railway deploys. Commits are small and imperative.

---

## Local development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open http://localhost:8000 — health check at `/healthz/`.

### Environment variables

| Variable | Purpose | Local default |
|---|---|---|
| `SECRET_KEY` | Django secret | insecure dev key |
| `DEBUG` | `1` on / `0` off | `0` |
| `DATABASE_URL` | Postgres URL; unset → SQLite | unset |
| `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` | comma-separated | localhost |
| `SHOW_DEMO_CREDENTIALS` | list demo logins on the login page | `0` |
| `STAFF_CONTACT_EMAIL` | general staff address for `mailto:` links | `info@lvaep.org` |
| `MEDIA_ROOT` | upload dir (falls back to Railway volume mount) | `./media` |

`RAILWAY_PUBLIC_DOMAIN` and `RAILWAY_VOLUME_MOUNT_PATH` are picked up automatically.

## Deployment

Railway builds `main` on every merge. The `Procfile` runs `migrate`, `collectstatic`, then Gunicorn.
Services: `web` (this repo) + `Postgres` + a Volume mounted at `/app/media`. After the first deploy — or after
changing the seed — run `python manage.py seed_demo` once from the service shell. Changing the public domain
requires a redeploy so `ALLOWED_HOSTS` picks it up.

## Not built (yet)

- Actual email delivery for subscriptions (needs an email backend + scheduler)
- Printable replica of the original paper form (funders may want the familiar layout)
- Visual design pass
- Field-level encryption of student PII
