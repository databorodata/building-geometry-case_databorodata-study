# Design note

> This is a template. Replace each section with your thinking. We read this first —
> it matters more than line count. Keep it sharp; bullet points are fine.

## Problem interpretation

How you read the problem. What "massing under constraints" means to you, and the
scope you chose to tackle (and not).

## Domain model

The core types — site, constraints, massing/option — and how the saved options form
a decision tree. Include the persistence schema (tables / relationships).

## Algorithm

How you turn a site polygon + constraints into a massing: setback inset, floor
stacking, metrics (footprint area, GFA, floor count), feasibility. Note the geometry
library or approach and why.

## API contract

The endpoints you exposed and their request/response shapes (create, branch, list,
get, …).

## Visualization

What you render and why you chose that approach.

## Assumptions & trade-offs

The decisions you made under ambiguity, and what you consciously traded away.

## Edge cases

How you handle concave plots, an inset that collapses to zero/splits, infeasible
constraint sets, self-intersection, an unreachable GFA target.

## What I'd do next

With another week: what you'd build, in what order, and why.
