import csv
import io
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session

from app import models
from app.auth import get_current_user, get_optional_user
from app.config import settings
from app.database import get_db
from app.templating import templates

router = APIRouter(tags=["data"])

EXPORT_VERSION = 1


# ── Serialisers ─────────────────────────────────────────────────────────────

def _links_to_dicts(links):
    return [
        {"short": lnk.short, "url": lnk.url, "description": lnk.description}
        for lnk in links
    ]


def _bundles_to_dicts(bundles):
    return [
        {
            "short": b.short,
            "name": b.name,
            "description": b.description,
            "icon": b.icon,
            "color": b.color,
            "link_shorts": [item.link_short for item in b.items],
        }
        for b in bundles
    ]


# ── Page ─────────────────────────────────────────────────────────────────────

@router.get("/import-export")
def import_export_page(
    request: Request,
    imported: int = 0,
    skipped: int = 0,
    errors: int = 0,
    user: Optional[str] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    link_count = db.query(models.Link).count()
    bundle_count = db.query(models.Bundle).count()
    return templates.TemplateResponse("import_export.html", {
        "request": request,
        "current_user": user,
        "admin_list": settings.admin_list,
        "link_count": link_count,
        "bundle_count": bundle_count,
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
        "show_result": bool(imported or skipped or errors),
    })


# ── Export ───────────────────────────────────────────────────────────────────

@router.get("/export/json")
def export_json(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    links = db.query(models.Link).order_by(models.Link.short).all()
    bundles = db.query(models.Bundle).order_by(models.Bundle.short).all()
    payload = {
        "version": EXPORT_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "links": _links_to_dicts(links),
        "bundles": _bundles_to_dicts(bundles),
    }
    content = json.dumps(payload, indent=2, ensure_ascii=False)
    filename = f"atlas-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/csv")
def export_csv(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    links = db.query(models.Link).order_by(models.Link.short).all()
    bundles = db.query(models.Bundle).order_by(models.Bundle.short).all()

    buf = io.StringIO()
    writer = csv.writer(buf)

    # ── Links section ──
    writer.writerow(["# LINKS"])
    writer.writerow(["short", "url", "description"])
    for lnk in links:
        writer.writerow([lnk.short, lnk.url, lnk.description])

    writer.writerow([])  # blank separator

    # ── Bundles section (link_shorts as pipe-separated) ──
    writer.writerow(["# BUNDLES"])
    writer.writerow(["short", "name", "description", "icon", "color", "link_shorts"])
    for b in bundles:
        link_shorts = "|".join(item.link_short for item in b.items)
        writer.writerow([b.short, b.name, b.description, b.icon, b.color, link_shorts])

    content = buf.getvalue()
    filename = f"atlas-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Import helpers ───────────────────────────────────────────────────────────

def _import_links(rows, user, db, overwrite: bool):
    created = skipped = errors = 0
    for row in rows:
        short = (row.get("short") or "").strip().lower()
        url = (row.get("url") or "").strip()
        description = (row.get("description") or "").strip()
        if not short or not url:
            errors += 1
            continue
        existing = db.query(models.Link).filter_by(short=short).first()
        if existing:
            if overwrite:
                existing.url = url
                existing.description = description
                created += 1
            else:
                skipped += 1
        else:
            db.add(models.Link(short=short, url=url, description=description, owner_email=user))
            created += 1
    return created, skipped, errors


def _import_bundles(rows, user, db, overwrite: bool):
    created = skipped = errors = 0
    for row in rows:
        short = (row.get("short") or "").strip().lower()
        name = (row.get("name") or "").strip()
        if not short or not name:
            errors += 1
            continue

        # link_shorts can be a JSON list (from JSON import) or pipe-separated string (CSV)
        raw = row.get("link_shorts") or ""
        if isinstance(raw, list):
            link_shorts = [s.strip() for s in raw if str(s).strip()]
        else:
            link_shorts = [s.strip() for s in str(raw).split("|") if s.strip()]

        new_items = [
            models.BundleItem(link_short=s, position=i)
            for i, s in enumerate(link_shorts)
        ]

        existing = db.query(models.Bundle).filter_by(short=short).first()
        if existing:
            if overwrite:
                existing.name = name
                existing.description = row.get("description") or ""
                existing.icon = row.get("icon") or "📦"
                existing.color = row.get("color") or "default"
                existing.items = new_items
                created += 1
            else:
                skipped += 1
        else:
            bundle = models.Bundle(
                short=short,
                name=name,
                description=row.get("description") or "",
                icon=row.get("icon") or "📦",
                color=row.get("color") or "default",
                owner_email=user,
            )
            bundle.items = new_items
            db.add(bundle)
            created += 1
    return created, skipped, errors


def _parse_csv(text: str):
    """Return (link_rows, bundle_rows) dicts parsed from atlas CSV format."""
    reader = csv.reader(io.StringIO(text))
    section = None
    link_header: Optional[list] = None
    bundle_header: Optional[list] = None
    link_rows = []
    bundle_rows = []

    for row in reader:
        if not row or not row[0].strip():
            continue
        first = row[0].strip()
        if first == "# LINKS":
            section = "links"
            link_header = None
            continue
        if first == "# BUNDLES":
            section = "bundles"
            bundle_header = None
            continue
        if section == "links":
            if link_header is None:
                link_header = row
            else:
                link_rows.append(dict(zip(link_header, row)))
        elif section == "bundles":
            if bundle_header is None:
                bundle_header = row
            else:
                bundle_rows.append(dict(zip(bundle_header, row)))

    return link_rows, bundle_rows


# ── Import endpoint ───────────────────────────────────────────────────────────

@router.post("/import")
async def import_data(
    file: UploadFile = File(...),
    overwrite: str = Form("skip"),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    do_overwrite = overwrite == "overwrite"
    content = await file.read()
    total_created = total_skipped = total_errors = 0
    filename = (file.filename or "").lower()

    try:
        if filename.endswith(".json"):
            payload = json.loads(content.decode("utf-8"))
            link_rows = payload.get("links", [])
            bundle_rows = payload.get("bundles", [])

            c, s, e = _import_links(link_rows, user, db, do_overwrite)
            total_created += c; total_skipped += s; total_errors += e
            db.flush()  # make newly inserted links visible for bundle ordering

            c, s, e = _import_bundles(bundle_rows, user, db, do_overwrite)
            total_created += c; total_skipped += s; total_errors += e
            db.commit()

        elif filename.endswith(".csv"):
            link_rows, bundle_rows = _parse_csv(content.decode("utf-8"))

            c, s, e = _import_links(link_rows, user, db, do_overwrite)
            total_created += c; total_skipped += s; total_errors += e
            db.flush()

            c, s, e = _import_bundles(bundle_rows, user, db, do_overwrite)
            total_created += c; total_skipped += s; total_errors += e
            db.commit()

        else:
            total_errors = 1  # unsupported format

    except Exception:
        db.rollback()
        total_errors += 1

    return RedirectResponse(
        url=f"/import-export?imported={total_created}&skipped={total_skipped}&errors={total_errors}",
        status_code=303,
    )
