# Frontend — building geometry case study

Minimal Vite + React (plain JS). It boots, calls the backend health check, and
gives you an empty canvas to build the visualization in.

## Getting started

```bash
npm install
npm run dev        # http://localhost:5173
```

The backend base URL defaults to `http://localhost:8000`; override with
`VITE_API_BASE` (see `.env.example`). With the root `docker compose up`, both run together.

## What's here / what's yours

- `src/api.js` — tiny fetch client (only `getHealth` so far).
- `src/App.jsx` — shows backend health + a placeholder canvas marked `TODO`.

You own the visualization: render the site, buildable footprint, massing, and
metrics, and let the user create / branch / navigate saved options (the decision
tree). Rendering approach is your call (2D SVG/canvas, 3D, …) — justify it in
`docs/DESIGN.md`. Add whatever libraries you need.

## Commands

```bash
npm run dev        # dev server
npm run build      # production build
npm run preview    # preview the build
```
