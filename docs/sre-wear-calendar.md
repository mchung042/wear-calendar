# SRE / launch ops — Wear Calendar MVP

## Counterpart research — sre
**Counterpart:** SRE / platform for solo consumer web apps  
**Analogs:** Soft-launch habit apps with auth walls; feature-flagged MVPs  
**Steal:** Default-deny data access; single kill switch; simple rollback = redeploy previous + flag off  
**Reject:** Multi-region complexity for friends-first launch  
**Sources:** Google SRE practices (rollback, SLOs) adapted to solo scale  

## Blast radius
Friends-only users; private closet data (PII: email, optional clothing photos later). No payments.

## Flags / progressive delivery
| Flag | Default | Purpose |
|------|---------|---------|
| `FEATURE_WEAR_CALENDAR` | on in prod once ready | Master kill for app routes |
| `ALLOW_SIGNUPS` | on | Set off to freeze new accounts |

## Rollback
1. Set `FEATURE_WEAR_CALENDAR=0` or `ALLOW_SIGNUPS=0`  
2. Redeploy previous git tag  
3. Time-to-undo target: **&lt;15 min**  

## SLIs / SLOs (MVP-honest)
| SLI | SLO |
|-----|-----|
| HTTP 5xx rate | &lt;1% over 24h |
| Authz isolation | 0 cross-user closet leaks (guardrail) |
| p95 HTML/API latency (local/small VPS) | &lt;500ms for calendar read |

## Monitoring (launch day)
- App logs: errors, failed logins, 403s  
- Manual: signup → log today → calendar → wash mark checklist  

## Runbook
| Failure | Mitigate |
|---------|----------|
| DB corrupt | Restore SQLite backup (`data/wear.db.bak`) |
| Auth broken | Disable signups; fix session secret |
| Leak suspected | Take app offline; rotate session secret; audit queries |

## Ops launch checklist
- [ ] Session secret set via env  
- [ ] SQLite path writable + backup script  
- [ ] FEATURE flag documented  
- [ ] Private-by-default verified (QA)  

**Launch ops gate: READY-WITH-WAIVER** (no hosted APM yet; logs + manual checks)
