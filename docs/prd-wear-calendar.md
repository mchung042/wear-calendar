# Wear Calendar — Final PRD

**Status:** Ready with assumptions  
**Source:** PRD duel Mix (A problem/needs/metrics/non-goals + B wash counter & tech/privacy)  
**Date:** 2026-07-11  
**Owners:** Product (Matthew) · Design · Eng · GTM  
**Target proof window:** 90 days after first 20 real users  

## 1. Problem Statement

Students and young adults often can’t reliably recall what they wore over the past few days, or whether a garment was worn again without washing. Today they rely on memory or scrolling a camera roll, which is slow and doesn’t answer “what have I worn most?” or “have I reworn this dirty?”

### P-1 — Primary problem
- **Who:** Students and young adults conscious about day-to-day outfit patterns and garment hygiene  
- **Situation:** Choosing clothes or reflecting on the last few days  
- **Failure today:** Memory is unreliable; camera roll is slow; no per-item wear/wash history  
- **Cost of inaction:** Accidental dirty rewears, weak sense of “what I’ve been living in,” possible unnecessary purchases  
- **Evidence:** E-1, E-2  

## Evidence pack
| ID | Type | Source | What it shows | Strength |
|----|------|--------|---------------|----------|
| E-1 | quote | friend | Wants past couple of days + what worn most | H |
| E-2 | quote | friend | Wonders if shirt worn multiple times without washing | H |
| E-3 | alternative | status quo | Memory / camera roll / buy more | M |

## 2. Users and needs

| ID | Segment | Context | Priority |
|----|---------|---------|----------|
| S-1 | Students / young adults | Peer visibility + laundry reality | P0 |

| ID | Need | Segment | Evidence | Priority |
|----|------|---------|----------|----------|
| N-1 | When I look back a few days, I want to see what I wore each day so I know my recent pattern | S-1 | E-1 | P0 |
| N-2 | When I consider a piece, I want to know how often I wore it recently and whether I’ve washed it since, so I can avoid overuse / dirty rewear | S-1 | E-1, E-2 | P0 |
| N-3 | When the day starts or ends, I want to log today’s outfit in under one minute so the calendar stays truthful | S-1 | E-1 | P0 |

## 3. Alternatives and wedge

| Alternative | Does well | Fails | Our wedge |
|-------------|-----------|-------|-----------|
| Memory | Zero friction | Unreliable | Structured history |
| Camera roll | Already there | Not queryable by item/date | Calendar + item counts |
| Buy more clothes | Social safety | Cost / waste | Insight before purchase |
| Heavy closet apps | Deep catalog | High setup | Log-first calendar MVP |

**Differentiation thesis:** Fast **date × item** wear log with **most-worn** and **wears-since-last-wash** — not a social fashion network.

## 4. Goals, non-goals, metrics

| ID | Goal | Links |
|----|------|-------|
| G-1 | Users can answer “what did I wear the last few days?” inside the product | P-1, N-1 |
| G-2 | Users can see frequency + wash gap per item | P-1, N-2 |
| G-3 | Daily logging is light enough to stick for a week | N-3 |

| ID | Non-goal | Why |
|----|----------|-----|
| NG-1 | Social feed / sharing | Scope trap for solo |
| NG-2 | Shopping / affiliate | Wrong job |
| NG-3 | AI stylist | Not evidenced |
| NG-4 | Native iOS/Android | Web-first |
| NG-5 | Smart-laundry hardware | Out of scope |

| Metric | Type | Baseline | Target | Timeframe | Source |
|--------|------|----------|--------|-----------|--------|
| % of users who add ≥1 item and create ≥5 wear logs within 7 days | north star input | 0 | ≥40% | 90 days post first 20 users | analytics |
| Median time to log “today’s outfit” (after ≥1 item exists) | input | ASSUMPTION | ≤60s | proof window | client timing event |
| Time to answer “last 3 days” via calendar | outcome | ASSUMPTION &gt;2 min camera/memory | ≤30s in-app | qualitative / task | self-report / test |
| Public/unauthenticated closet views | guardrail | 0 | stay 0 | always | security check |

## 5. Solution thesis
**Bet:** A private web calendar of wears beats memory and camera roll for this job.  
**Rejected:** Social closet, AI outfits, marketplace.  
**MVP:** Items + wear logs on dates + calendar views + most-worn + wears-since-wash.  
**Not in MVP:** Reminders, custom wash rules beyond mark-washed, tags/outfits-as-entities (multi-item day log is enough).

## 6. Scope

### In scope (MVP)
| Req ID | Requirement | N-# | P-# | Priority |
|--------|-------------|-----|-----|----------|
| R-1 | Create/edit/delete clothing items (name required; optional photo; optional type) | N-3 | P-1 | P0 |
| R-2 | Log one or more items as worn on a specific date | N-1, N-3 | P-1 | P0 |
| R-3 | Calendar (week + month) shows items worn each day | N-1 | P-1 | P0 |
| R-4 | Item detail: wear dates + counts for last 7 / 14 / 30 days | N-2 | P-1 | P0 |
| R-5 | Most-worn list for selected range (default 7 days) | N-1, N-2 | P-1 | P0 |
| R-6 | Mark item washed; show **wears since last wash** (counter from B) | N-2 | P-1 | P0 |
| R-7 | Auth + private-by-default closet (from B) | N-3 | P-1 | P0 |
| R-8 | Edit/delete a wear log | N-3 | P-1 | P0 |

### Out of scope
| Item | Why | Revisit when |
|------|-----|--------------|
| Social / public profiles | NG-1 | Retention proven |
| Push reminders | Habit unproven | After activation metrics |
| AI suggestions | NG-3 | Explicit demand |

## 7. Requirements detail (P0 AC)

**R-3 — Calendar** (N-1, P-1)  
- Given wear logs on Mon–Wed, When user opens week calendar, Then those days list the logged item names or thumbnails.  
- Given a day with no logs, When viewed, Then empty state “Nothing logged” with CTA to log.

**R-5 — Most worn** (N-1, N-2, P-1)  
- Given multiple wears in range, When user opens Most worn (7 days), Then items sort by wear count descending with counts visible.

**R-6 — Wash counter** (N-2, P-1)  
- Given item X worn on 3 dates after last wash mark, When user opens X, Then “Wears since last wash: 3” is shown.  
- Given that state, When user marks washed, Then counter returns to 0 until a new wear is logged.

**R-2 / R-3 logging** (N-3)  
- Given ≥1 item exists, When user logs today’s outfit with multi-select save, Then calendar today updates without full page dead-end errors.

**R-7 — Privacy**  
- Given user A’s items, When user B is authenticated as someone else (or logged out), Then A’s closet returns 401/403 / no data.

## 8. UX / design constraints
- Home = calendar (week default).  
- Primary action = Log today.  
- States: empty closet, empty day, loading, auth error.  
- Mobile-responsive web required (students on phones).  
- Design gate still required before build (POLICY A).

## 9. Technical & operational constraints (PM-level, from B)
- Web app with accounts (magic link or email/password).  
- Data model: `items`, `wear_events` (item_id, date, user_id), `wash_events` or `items.last_washed_at`.  
- Optional image upload to object storage; name-only items must work without photos.  
- Solo-maintainable stack preferred (e.g. Next.js + Postgres).  
- OPEN: exact stack choice left to eng.

## 10. GTM / adoption (pointer — growth owns detail)
- Activation = first item + first wear log + return to view calendar within 48h.  
- Launch: friends first, then campus / online communities that discuss outfit repeating.

## 11. Risks, assumptions, open questions
| ID | Assumption | If wrong | Validation |
|----|------------|----------|------------|
| A-1 | Users will log daily for a week if logging ≤60s | Retention dies | Activation metric |
| A-2 | Name-only items are enough to start | Want photos first | Observe photo attach rate |
| A-3 | Wash mark is understood without laundry education | Confusion | First-run copy test |

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Logging friction | H | M | Name-only + today-first UI |
| Privacy leak | H | L | Private default + authz tests |

| ID | Question | Blocking? | Owner |
|----|----------|-----------|-------|
| Q-1 | Magic link vs password for MVP? | N | eng |
| Q-2 | Week vs month as default home? | N | design |

## 12. Launch / proof criteria
- [ ] P0 AC verified  
- [ ] Instrumentation: item_create, wear_log_create, calendar_view, most_worn_view, wash_mark  
- [ ] Guardrail: closets private  
- [ ] Kill/iterate date: **90 days after 20 real users** — if &lt;40% of item-adders reach 5 logs in 7 days → simplify logging or kill bet  

## Critique (prd-maker)
**Verdict:** Ready with assumptions  
**Gates:** Problem/needs/traceability/metrics/diff/non-goals/AC/assumptions/ship criteria Pass; evidence Pass via E-1/E-2; language Pass.  
**Assumptions to validate:** A-1–A-3, baseline times.  
