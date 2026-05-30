"""Building-geometry domain — THIS IS WHERE THE CASE STUDY LIVES.

The module is intentionally empty. You decide the shape: the domain types
(site, constraints, massing, option), the algorithm, and the API contract.

A sketch of the problem (not a spec — make your own calls and write them down
in docs/DESIGN.md):

  - Input: a 2D site polygon (planar coordinates, metres) + a set of constraints
    (setbacks, max height / floor count, floor-to-floor height, site coverage or
    max footprint, optional GFA / floor-area-ratio target).
  - Compute: inset the polygon by the setback -> buildable footprint; stack floor
    plates within the height/area limits; report metrics (footprint area, GFA,
    floor count) and feasibility. Handle degenerate / infeasible inputs.
  - Persist: save a result as an "option", and let users branch alternative
    options from an existing one (see app/db.py). The saved options form a tree.

Sample inputs live in ../data/sites/. Suggested next steps:
  - add `app/geometry/massing.py` for the algorithm,
  - add ORM models + an `app/v1/routes/massing.py` router,
  - and tests under ../tests/.
"""
