"""Wear Calendar MVP — FastAPI app (closet + drag-drop calendar)."""
from __future__ import annotations

import os
import uuid
from calendar import monthcalendar
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

import db

BASE = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("WEAR_DATA_DIR", BASE / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
FEATURE_ON = os.environ.get("FEATURE_WEAR_CALENDAR", "1") != "0"
ALLOW_SIGNUPS = os.environ.get("ALLOW_SIGNUPS", "1") != "0"
SESSION_SECRET = os.environ.get("SESSION_SECRET", "dev-only-change-me")
# Secure cookies on Railway / HTTPS hosts
_SESSION_HTTPS = os.environ.get("SESSION_HTTPS", "").lower() in {"1", "true", "yes"} or bool(
    os.environ.get("RAILWAY_ENVIRONMENT")
)

CLOTHING_TYPES = [
    "Hat",
    "Accessory",
    "Shirt",
    "T-shirt",
    "Sweater",
    "Jacket",
    "Dress",
    "Skirt",
    "Pants",
    "Jeans",
    "Shorts",
    "Shoes",
    "Other",
]

# Head-to-toe stack on a calendar day (lower = higher on the pile)
TYPE_STACK_ORDER = {
    "Hat": 0,
    "Accessory": 1,
    "Shirt": 2,
    "T-shirt": 2,
    "Sweater": 3,
    "Jacket": 4,
    "Dress": 5,
    "Skirt": 6,
    "Pants": 7,
    "Jeans": 7,
    "Shorts": 7,
    "Shoes": 8,
    "Other": 9,
}


def stack_key(wear) -> tuple:
    t = (wear["type"] or "Other").strip()
    return (TYPE_STACK_ORDER.get(t, 50), (wear["name"] or "").lower())


def sort_day_wears(wears: list) -> list:
    return sorted(wears, key=stack_key)

app = FastAPI(title="Wear Calendar")
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=_SESSION_HTTPS,
)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
templates = Jinja2Templates(directory=str(BASE / "templates"))


@app.on_event("startup")
def _startup() -> None:
    db.init_db()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def current_user_id(request: Request) -> Optional[int]:
    uid = request.session.get("user_id")
    return int(uid) if uid else None


def require_user(request: Request) -> int:
    if not FEATURE_ON:
        raise HTTPException(status_code=503, detail="Feature disabled")
    uid = current_user_id(request)
    if not uid:
        raise HTTPException(status_code=401, detail="login_required")
    return uid


@app.exception_handler(HTTPException)
async def http_exc_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401 and exc.detail == "login_required":
        return RedirectResponse("/login", status_code=303)
    if exc.status_code == 503:
        return HTMLResponse("<h1>Temporarily offline</h1><p>Feature flag disabled.</p>", status_code=503)
    return HTMLResponse(f"<h1>{exc.status_code}</h1><p>{exc.detail}</p>", status_code=exc.status_code)


def render(request: Request, name: str, **ctx):
    ctx.setdefault("user_email", request.session.get("email"))
    ctx.setdefault("feature_on", FEATURE_ON)
    ctx.setdefault("clothing_types", CLOTHING_TYPES)
    return templates.TemplateResponse(name, {"request": request, **ctx})


async def save_upload(photo: Optional[UploadFile]) -> Optional[str]:
    if not photo or not photo.filename:
        return None
    ext = Path(photo.filename).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        ext = ".jpg"
    name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / name
    data = await photo.read()
    if not data:
        return None
    dest.write_bytes(data)
    return name


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if not current_user_id(request):
        return RedirectResponse("/login", status_code=303)
    return RedirectResponse("/calendar", status_code=303)


@app.get("/signup", response_class=HTMLResponse)
def signup_form(request: Request):
    if not ALLOW_SIGNUPS:
        return render(request, "auth.html", mode="login", error="Signups are closed right now.")
    return render(request, "auth.html", mode="signup", error=None)


@app.post("/signup")
def signup(request: Request, email: str = Form(...), password: str = Form(...)):
    if not ALLOW_SIGNUPS:
        return render(request, "auth.html", mode="signup", error="Signups are closed.")
    if len(password) < 8:
        return render(request, "auth.html", mode="signup", error="Password must be at least 8 characters.")
    try:
        uid = db.create_user(email, password)
    except Exception:
        return render(request, "auth.html", mode="signup", error="Email already registered.")
    request.session["user_id"] = uid
    request.session["email"] = email.lower().strip()
    return RedirectResponse("/closet?welcome=1", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return render(request, "auth.html", mode="login", error=None)


@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = db.authenticate(email, password)
    if not user:
        return render(request, "auth.html", mode="login", error="Invalid email or password.")
    request.session["user_id"] = user["id"]
    request.session["email"] = user["email"]
    return RedirectResponse("/calendar", status_code=303)


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@app.get("/calendar", response_class=HTMLResponse)
def calendar_view(
    request: Request,
    view: str = "week",
    ym: Optional[str] = None,
    week_offset: int = 0,
):
    uid = require_user(request)
    today = date.today()
    if view == "month":
        if ym:
            y, m = map(int, ym.split("-"))
            anchor = date(y, m, 1)
        else:
            anchor = date(today.year, today.month, 1)
        start = date(anchor.year, anchor.month, 1)
        if anchor.month == 12:
            end = date(anchor.year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(anchor.year, anchor.month + 1, 1) - timedelta(days=1)
        weeks = monthcalendar(anchor.year, anchor.month)
        prev_m = (anchor.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        next_m = (end + timedelta(days=1)).strftime("%Y-%m")
        week_days: list[date] = []
        week_offset = 0
    else:
        start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
        end = start + timedelta(days=6)
        weeks = []
        week_days = [start + timedelta(days=i) for i in range(7)]
        anchor = start
        prev_m = next_m = None

    wears = db.wears_for_range(uid, start.isoformat(), end.isoformat())
    by_day: dict[str, list] = {}
    for w in wears:
        by_day.setdefault(w["worn_on"], []).append(w)
    by_day = {d: sort_day_wears(ws) for d, ws in by_day.items()}

    db.track_view(uid, "calendar_view", f"range={view}")
    return render(
        request,
        "calendar.html",
        view=view,
        today=today.isoformat(),
        start=start,
        end=end,
        anchor=anchor,
        weeks=weeks,
        week_days=week_days,
        by_day=by_day,
        prev_m=prev_m,
        next_m=next_m,
        week_offset=week_offset,
        closet=db.list_items(uid),
    )


@app.post("/api/log")
async def api_log(request: Request):
    """Drag-drop: log one clothing piece onto any date (past/today/future)."""
    uid = require_user(request)
    payload = await request.json()
    worn_on = str(payload.get("worn_on", ""))
    item_id = int(payload.get("item_id", 0))
    if not worn_on or not item_id:
        return JSONResponse({"ok": False, "reason": "missing"}, status_code=400)
    try:
        date.fromisoformat(worn_on)
    except ValueError:
        return JSONResponse({"ok": False, "reason": "bad_date"}, status_code=400)
    n = db.log_wears(uid, worn_on, [item_id])
    if n == 0:
        return JSONResponse({"ok": False, "reason": "duplicate"})
    return JSONResponse({"ok": True})


@app.post("/log")
def log_wear(
    request: Request,
    worn_on: str = Form(...),
    item_ids: list[int] = Form(default=[]),
):
    uid = require_user(request)
    if not item_ids:
        return RedirectResponse("/calendar?error=pick", status_code=303)
    db.log_wears(uid, worn_on, item_ids)
    return RedirectResponse("/calendar", status_code=303)


@app.post("/wear/{wear_id}/delete")
def wear_delete(request: Request, wear_id: int):
    uid = require_user(request)
    db.delete_wear(uid, wear_id)
    return RedirectResponse(request.headers.get("referer") or "/calendar", status_code=303)


@app.get("/closet", response_class=HTMLResponse)
@app.get("/items", response_class=HTMLResponse)
def closet_page(request: Request, welcome: Optional[str] = None, error: Optional[str] = None):
    uid = require_user(request)
    return render(
        request,
        "closet.html",
        closet=db.list_items(uid),
        welcome=bool(welcome),
        error=error,
    )


@app.post("/closet")
@app.post("/items")
async def closet_create(
    request: Request,
    name: str = Form(...),
    type: str = Form(...),
    photo: Optional[UploadFile] = File(None),
):
    uid = require_user(request)
    if not name.strip() or not type.strip():
        return RedirectResponse("/closet?error=required", status_code=303)
    photo_name = await save_upload(photo)
    db.create_item(uid, name, type, photo_name)
    return RedirectResponse("/closet", status_code=303)


@app.post("/closet/{item_id}/delete")
@app.post("/items/{item_id}/delete")
def closet_delete(request: Request, item_id: int):
    uid = require_user(request)
    item = db.get_item(uid, item_id)
    if item and item["photo_path"]:
        path = UPLOAD_DIR / item["photo_path"]
        if path.exists():
            path.unlink()
    db.delete_item(uid, item_id)
    return RedirectResponse("/closet", status_code=303)


@app.get("/closet/{item_id}/edit", response_class=HTMLResponse)
def closet_edit_form(request: Request, item_id: int):
    uid = require_user(request)
    item = db.get_item(uid, item_id)
    if not item:
        raise HTTPException(404)
    return render(request, "closet_edit.html", item=item, error=None)


@app.post("/closet/{item_id}/edit")
async def closet_edit_save(
    request: Request,
    item_id: int,
    name: str = Form(...),
    type: str = Form(...),
    photo: Optional[UploadFile] = File(None),
    remove_photo: Optional[str] = Form(None),
):
    uid = require_user(request)
    item = db.get_item(uid, item_id)
    if not item:
        raise HTTPException(404)
    if not name.strip() or not type.strip():
        return render(
            request,
            "closet_edit.html",
            item=item,
            error="Type and name are required.",
        )
    clear = remove_photo == "1"
    new_photo = await save_upload(photo)
    old_photo = item["photo_path"]
    ok = db.update_item(
        uid,
        item_id,
        name,
        type,
        photo_path=new_photo,
        clear_photo=clear and not new_photo,
    )
    if ok and (new_photo or clear) and old_photo:
        path = UPLOAD_DIR / old_photo
        if path.exists() and (new_photo or clear):
            # only delete old file if replaced or cleared
            if new_photo or clear:
                path.unlink(missing_ok=True)
    return RedirectResponse(f"/closet/{item_id}", status_code=303)


@app.get("/closet/{item_id}", response_class=HTMLResponse)
@app.get("/items/{item_id}", response_class=HTMLResponse)
def closet_detail(request: Request, item_id: int):
    uid = require_user(request)
    item = db.get_item(uid, item_id)
    if not item:
        raise HTTPException(404)
    history = db.item_wear_history(uid, item_id)
    since = db.wears_since_wash(uid, item_id)
    today = date.today()

    def count_since(days: int) -> int:
        start = (today - timedelta(days=days - 1)).isoformat()
        return sum(1 for h in history if h["worn_on"] >= start)

    db.track_view(uid, "item_detail_view", f"wears_since_wash={since}")
    return render(
        request,
        "item_detail.html",
        item=item,
        history=history,
        wears_since_wash=since,
        c7=count_since(7),
        c14=count_since(14),
        c30=count_since(30),
    )


@app.post("/closet/{item_id}/wash")
@app.post("/items/{item_id}/wash")
def item_wash(request: Request, item_id: int):
    uid = require_user(request)
    if not db.mark_washed(uid, item_id):
        raise HTTPException(404)
    return RedirectResponse(f"/closet/{item_id}", status_code=303)


@app.get("/most-worn", response_class=HTMLResponse)
def most_worn_page(request: Request, days: int = 7):
    uid = require_user(request)
    days = days if days in (7, 14, 30) else 7
    return render(request, "most_worn.html", days=days, rows=db.most_worn(uid, days))


@app.get("/health")
def health():
    return {"ok": True, "feature": FEATURE_ON, "signups": ALLOW_SIGNUPS}
