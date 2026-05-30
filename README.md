# Building Geometry Case Study

Turn a plot of land and a handful of rules into a building — and let an architect
explore the alternatives.

This is a take-home for **senior** engineers. There is a runnable scaffold here
(FastAPI backend, Postgres, React frontend) but the interesting part — the geometry,
the data model, the visualization — is yours to build. We care less about how much
you finish and more about **how you decompose the problem, where you draw the
boundaries, and which trade-offs you make explicit.**

---

## The domain

Early-stage building design starts with *massing*: before any rooms or facades, you
work out the rough buildable volume on a site, given the rules that apply to it. The
reasoning goes roughly:

1. Start from the **site polygon** — the plot boundary (here: planar coordinates in metres).
2. Pull in from the boundary by the required **setback** → the **buildable footprint**.
3. Stack **floor plates** on that footprint, within the **height** and **floor** limits,
   respecting **floor-to-floor** height and any **site coverage** cap.
4. Read off the **metrics** — footprint area, gross floor area (**GFA**), floor count —
   and check the result against the brief (e.g. a **GFA target**), or report that the
   constraints can't be satisfied.

In practice an architect doesn't compute one massing — they explore. "What if the
setback were smaller?" "What if we trade footprint for height?" Each variation is an
**option**, and options branch from one another, forming a **tree of decisions** the
team navigates and compares.

## The problem

> Given a 2D **site polygon** and a set of **constraints**, generate, **save**, and
> **visualize** a building massing — and let the user **branch** alternative options
> into a decision tree.

Three parts, all yours to design and build:

- **Constraint + massing algorithm.** Inset the polygon by the setback → buildable
  footprint; stack floor plates within the limits; compute metrics; report feasibility.
- **Persistence + decision tree.** Save a computed massing as an *option*; branch new
  options from an existing one (vary constraints, re-run); the saved options form a
  tree the user can navigate and compare. **You design the schema and the API.**
- **Visualization.** A frontend that lets the user set up a site + constraints, see the
  resulting massing and its metrics, and create / branch / navigate options. Rendering
  approach (2D, 3D, …) is your call — justify it.

### Constraints to consider

A starting list — **not exhaustive**, and you decide how to model them:

- setback from the boundary
- maximum height and/or maximum floor count
- floor-to-floor height
- site coverage ratio (or a maximum footprint area)
- an optional GFA / floor-area-ratio target to aim for

### Edge cases worth thinking about

- concave plots (a setback bends around reflex corners — see `data/sites/l-shaped.json`)
- a setback that collapses the footprint to zero area, or splits it in two (`notched.json`)
- infeasible constraint sets, and how you surface that
- self-intersecting or degenerate input polygons
- a GFA target that the height/floor caps make unreachable

## What we give you

Everything boring is done so your weekend goes to the real problem:

- **Backend** (`backend/`) — FastAPI + uv + Ruff + Pyright, a working `/api/v1/health`,
  and **async SQLAlchemy plumbing wired up** (engine + session dependency in
  `app/db.py`) — but **no ORM models**. The geometry domain (`app/geometry/`) is empty.
- **Database** — Postgres, brought up by `docker compose`.
- **Frontend** (`frontend/`) — minimal Vite + React that boots and already reaches the
  backend health check (CORS + wiring done). The canvas is empty.
- **Sample data** (`data/sites/`) — a few site polygons (convex, concave, notched) and
  example constraint sets, so inputs are concrete and comparable across candidates.

You design the API contract, the domain model, the persistence schema + decision-tree
model, the algorithm, the visualization, and the tests. Add any libraries you like.

## Deliverables

1. **Design note** — `docs/DESIGN.md` (a template is provided). Your interpretation,
   domain model, algorithm approach, API contract, assumptions, explicit trade-offs,
   and what you'd do next. *We read this first.*
2. **Working prototype** — the backend algorithm + persistence (save options, branch the
   decision tree) + API + tests, and the visualization to drive it.
3. **Roadmap** — what each part should grow into and in what order: richer / real zoning
   constraints, GFA optimization, 3D, multiple buildings on a site, option diffing &
   versioning, performance at scale. Tell us what you'd build, and why.

There's no hard time limit; we'd expect a senior candidate to spend somewhere between
half a day and a long weekend, depending on how far you push the prototype. Quality of
judgement beats completeness.

## Repo layout

```
.
├── backend/          FastAPI + uv + async SQLAlchemy (health works; geometry is yours)
├── frontend/         Vite + React (boots, reaches /health; canvas is yours)
├── data/sites/       sample site polygons + example constraints (metres)
├── docs/DESIGN.md    design-note template — fill this in
├── docker-compose.yml
└── README.md
```

Each app has its own `README.md` with local-dev instructions.

## Running it

```bash
docker compose up --build
```

| Service                | URL                                   |
| ---------------------- | ------------------------------------- |
| Frontend               | http://localhost:5173                 |
| Backend (OpenAPI docs) | http://localhost:8000/docs            |
| Backend health         | http://localhost:8000/api/v1/health   |
| Postgres               | `localhost:5432`, db `casestudy`, `postgres`/`postgres` |

Prefer running pieces directly? See `backend/README.md` and `frontend/README.md`.

## Handing it back

Delivered as a GitHub repo, reviewed as pull requests.

1. **Fork** this repository.
2. Work in **feature branches** off `main` — one branch per discrete piece reads best,
   e.g. `feat/massing-algorithm`, `feat/options-tree`, `feat/visualization`, `docs/design`.
3. Open **pull requests** back to your fork's `main`. Smaller, focused PRs beat one giant
   one; draft / proof-of-concept PRs are fine — just say so. In each PR description tell us:
   - what problem it addresses,
   - what's in scope vs. what you intentionally left out, and why,
   - what you'd do next with more time.
4. Keep the written design in `docs/` (or link out to Figma/Miro — make it publicly
   viewable).
5. When you're done, send the link to your fork and the PRs to `b.neterebskii@all3.com`.

We're looking for sharp judgement: a small, well-reasoned prototype with a great design
note beats a sprawling, half-working rewrite every time. Good luck.
