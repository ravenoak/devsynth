# Sprint–EDRR Ceremony Alignment

This guide explains how sprint ceremonies map to the Expand, Differentiate,
Refine, and Retrospect (EDRR) phases.

## Ceremony Mapping

- **Planning → Expand**
- **Standups → Differentiate**
- **Review → Refine**
- **Retrospective → Retrospect**

## Integration Steps

1. Instantiate `SprintAdapter` with optional `settings` and ceremony mapping.
2. Call `get_ceremony_phase` to resolve the EDRR phase for a ceremony such as
   `planning`, `dailyStandup`, `review`, or `retrospective`.
3. Use `align_sprint_planning` to associate planning sections with their
   phases.
4. Run the sprint cycle; metrics and reports reflect the phase-aligned
   ceremonies.
