# Wear Calendar

Private web MVP: closet + calendar of what you wore each day (drag-and-drop), most-worn, wears-since-wash.

Product agents / orchestrator live in a separate repo ([product-dev-team](https://github.com/mchung042/product-dev-team)) and in `~/.cursor/` — open this folder in Cursor and they still work.

## Local

```bash
python3 -m pip install -r requirements.txt
SESSION_SECRET='change-me' python3 -m uvicorn main:app --reload --port 8000
```

Open http://127.0.0.1:8000

## Railway

1. New project → deploy this GitHub repo (root = repo root, no subdirectory).
2. Variables: `SESSION_SECRET` (required), `ALLOW_SIGNUPS=1`
3. Volume mounted at `/data`
4. Generate a public domain

See `Dockerfile` and `railway.toml`.

## Docs
- `docs/prd-wear-calendar.md`
- `docs/done-wear-calendar.md`
- `docs/sre-wear-calendar.md`
