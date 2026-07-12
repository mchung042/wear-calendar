# Wear Calendar — Feedback roadmap (no dates)

**Mode:** Production PM  
**Date:** 2026-07-12  
**Status:** Ordered by dependency; not time-boxed  
**Inputs:** 7 user quotes post-MVP  

## User groups

| ID | Group | Job | Evidence |
|----|-------|-----|----------|
| S-1 | Solo Logger | Log and understand *my* clothes/wears quickly and clearly | Camera, auto-type, mannequin, Beli polish |
| S-2 | Social Peer | See trusted friends’ wears and closet changes | Friends wears, new items |
| S-3 | Outfit Helper | Advise a friend’s outfit | “Help pick an outfit for them” |

## Sequenced bets

| # | Feature | Group | Size | Depends on | Why this order |
|---|---------|-------|------|------------|----------------|
| 1 | In-app camera capture | S-1 | M | — | Photo quality + less friction; feeds 2 & 4 |
| 2 | Auto clothing type from photo | S-1 | L | 1 | Needs photos; cuts type picker toil |
| 3 | Beli-caliber design system | S-1→S-2 | L | — (parallel after 1 starts) | Polish once before mannequin + social |
| 4 | Mannequin / outfit composition | S-1 | XL→split | 1, 2, 3 | Replaces weak day icons |
| 5 | Friends graph + privacy | S-2 | L | 3 | Platform for 6–8; opt-in defaults |
| 6 | Friends’ wear history | S-2 | L | 5 | Core social quote |
| 7 | Friends’ new closet items | S-2 | M | 5 | Activity on shared closets |
| 8 | Help pick outfit for a friend | S-3 | XL→split | 5–7, ideally 4 | Only valuable with shared context |

## Status

- **Wave 1 (in-app camera):** shipped US-1 on closet add + edit (Take photo / Choose photo + desktop webcam).
- **Wave 2 (auto type):** implemented but **off by default** (`FEATURE_TYPE_SUGGEST=0`, client `TYPE_SUGGEST_CLIENT=false`). Re-enable later with key + flag.
- **Wave 3 (design):** shipped — Atelier visual system (Syne + Figtree, cool canvas, teal accent, underline nav).

