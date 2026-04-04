from __future__ import annotations

import subprocess
from datetime import datetime
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from awscope.cache import read_cache
from awscope.config import build_session, load_config
from awscope.exporter import build_excel
from awscope.object_store import upload_export

app = FastAPI(title="awscope")

_STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")


# ── dashboard data ─────────────────────────────────────────────────────────

@app.get("/")
async def index():
    from fastapi.responses import FileResponse
    return FileResponse(str(_STATIC / "index.html"))


@app.get("/api/summary")
async def summary():
    result = read_cache()
    return {
        "scanned_at": result.scanned_at,
        "accounts": result.accounts,
        "group_count": len(result.groups),
        "resource_count": len(result.resources),
    }


@app.get("/api/groups")
async def groups():
    result = read_cache()
    return [
        {
            "group_name": g.group_name,
            "resource_count": len(g.resources),
            "resource_types": sorted({r.resource_type for r in g.resources}),
            "accounts": sorted({r.account_alias for r in g.resources}),
        }
        for g in sorted(result.groups, key=lambda x: x.group_name)
    ]


@app.get("/api/groups/{group_name}")
async def group_detail(group_name: str):
    result = read_cache()
    matched = next((g for g in result.groups if g.group_name.lower() == group_name.lower()), None)
    if not matched:
        raise HTTPException(status_code=404, detail=f"Group '{group_name}' not found")
    return {
        "group_name": matched.group_name,
        "resources": [
            {
                "resource_id": r.resource_id,
                "name": r.name,
                "resource_type": r.resource_type,
                "arn": r.arn,
                "region": r.region,
                "account_alias": r.account_alias,
                "account_id": r.account_id,
                "status": r.status,
                "tags": r.tags,
            }
            for r in sorted(matched.resources, key=lambda x: (x.resource_type, x.name))
        ],
    }


@app.get("/api/export")
async def export():
    result = read_cache()
    buf: BytesIO = build_excel(result)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"awscope_export_{ts}.xlsx"
    object_key = f"exports/{datetime.now().strftime('%Y-%m-%d')}/{filename}"
    upload_export(buf, object_key)

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── account management ─────────────────────────────────────────────────────

@app.get("/api/accounts")
async def list_accounts():
    try:
        configs = load_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    result = []
    for acc in configs:
        try:
            session = build_session(acc)
            identity = session.client("sts", region_name="us-east-1").get_caller_identity()
            result.append({
                "alias": acc.alias,
                "auth_type": acc.auth_type,
                "account_id": identity["Account"],
                "arn": identity["Arn"],
                "status": "connected",
            })
        except Exception as e:
            result.append({
                "alias": acc.alias,
                "auth_type": acc.auth_type,
                "account_id": "",
                "arn": "",
                "status": f"error: {e}",
            })
    return result


@app.get("/api/accounts/{alias}/status")
async def account_status(alias: str):
    try:
        configs = load_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    acc = next((c for c in configs if c.alias == alias), None)
    if not acc:
        raise HTTPException(status_code=404, detail=f"Account '{alias}' not found")

    try:
        session = build_session(acc)
        identity = session.client("sts", region_name="us-east-1").get_caller_identity()
        return {"alias": alias, "status": "connected", "account_id": identity["Account"]}
    except Exception as e:
        return {"alias": alias, "status": f"error: {e}", "account_id": ""}


@app.post("/api/accounts/{alias}/sso-login")
async def sso_login(alias: str):
    try:
        configs = load_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    acc = next((c for c in configs if c.alias == alias), None)
    if not acc:
        raise HTTPException(status_code=404, detail=f"Account '{alias}' not found")
    if acc.auth_type != "sso":
        raise HTTPException(status_code=400, detail=f"Account '{alias}' is not an SSO account")

    try:
        subprocess.Popen(
            ["aws", "sso", "login", "--profile", acc.profile],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return {"alias": alias, "status": "browser_opened"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to launch sso login: {e}")
