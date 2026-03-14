"""5️⃣ PRESENTATION & CONTROL LAYER - FastAPI Application."""
import asyncio
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from app.config import get_settings
from app.database import (
    init_db, save_setting, get_setting, save_session_snapshot,
    get_monthly_focus, get_weekly_summary, add_log, get_recent_logs
)
from app.layers.data_collection import DataCollector
from app.layers.event_processing import SessionAggregator
from app.layers.ai_intelligence import AIInsightGenerator
from app.layers.security_intelligence import SecurityIntelligence
from app.services.pdf_service import generate_daily_pdf, generate_weekly_pdf

collector = None
aggregator = None
ai_engine = None
security = None
session_start_time = 0
focus_trend_history = []
network_history = []
connected_clients = []
_last_snapshot_time = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    global collector, aggregator, ai_engine, security, session_start_time
    try:
        init_db()
    except Exception as e:
        import logging
        logging.warning(f"DB init failed (using memory): {e}")
    settings = get_settings()
    idle = get_setting("idle_threshold_sec", settings.idle_threshold_sec)
    collector = DataCollector(idle)
    aggregator = SessionAggregator()
    ai_engine = AIInsightGenerator()
    security = SecurityIntelligence()
    session_start_time = time.time()
    try:
        add_log("INIT", "All modules initialized successfully")
    except Exception:
        pass
    yield
    collector = None
    aggregator = None
    ai_engine = None
    security = None


app = FastAPI(title="FocusAI PRO MONITOR", lifespan=lifespan)


class SettingsUpdate(BaseModel):
    idle_threshold_sec: int = None
    focus_sensitivity: str = None
    alert_sensitivity: str = None
    refresh_interval_sec: int = None
    theme: str = None


def build_dashboard_state() -> dict:
    global collector, aggregator, ai_engine, security, session_start_time, focus_trend_history, network_history, _last_snapshot_time

    if not all([collector, aggregator, ai_engine, security]):
        return _default_state()

    settings = get_settings()
    refresh = get_setting("refresh_interval_sec", settings.refresh_interval_sec)
    idle_threshold = get_setting("idle_threshold_sec", settings.idle_threshold_sec)

    raw = collector.collect_raw_event()
    aggregate = aggregator.process_event(raw, refresh)
    switch_count = aggregator.get_switch_count()

    session_sec = int(time.time() - session_start_time)
    idle_sec = collector.idle_detector.get_idle_seconds()
    idle_ratio = idle_sec / session_sec if session_sec > 0 else 0
    if collector.idle_detector.is_idle():
        idle_ratio = min(1, idle_ratio + 0.1)

    top_procs = []
    try:
        top_procs = collector.system_monitor.get_top_processes_by_cpu(5)
    except Exception:
        pass
    security_score, security_alerts = security.analyze(raw, top_procs)
    insight = ai_engine.generate(aggregate, switch_count, security_score, idle_ratio)

    focus_trend_history.append({"time": int(time.time()), "score": insight.focus_score})
    if len(focus_trend_history) > 30:
        focus_trend_history.pop(0)

    network_history.append({
        "upload": raw.network_bytes_sent,
        "download": raw.network_bytes_recv,
        "ts": int(time.time())
    })
    if len(network_history) > 30:
        network_history.pop(0)

    total = aggregate.total_active_time or 1
    productivity_split = {
        "productive": round(aggregate.session_productive_time / total * 100, 1),
        "distracting": round(aggregate.session_distracting_time / total * 100, 1),
        "neutral": round(aggregate.session_neutral_time / total * 100, 1)
    }

    threat = "low" if security_score >= 80 else "medium" if security_score >= 50 else "high"

    alerts = []
    for a in security_alerts:
        alerts.append({"type": a.type, "message": a.message, "severity": a.severity})
    if insight.focus_score < 50:
        alerts.append({"type": "focus", "message": "Low Focus", "severity": "warning"})
    if switch_count > 15:
        alerts.append({"type": "switching", "message": "Excessive App Switching", "severity": "warning"})
    if raw.cpu_usage > 80:
        alerts.append({"type": "cpu", "message": "High CPU usage", "severity": "critical"})

    top_apps_with_category = []
    for a in aggregate.top_apps[:10]:
        cat = aggregator._classify_app(a["name"])
        top_apps_with_category.append({**a, "category": cat})

    processes = []
    for p in top_procs[:5]:
        cpu = round(p.get("cpu_percent", 0) or 0, 1)
        risk = "low" if cpu < 30 else "medium" if cpu < 70 else "high"
        processes.append({"name": p.get("name", "unknown"), "cpu_percent": cpu, "risk": risk})

    if time.time() - _last_snapshot_time > 60:
        _last_snapshot_time = time.time()
        add_log("SYNC", "Dashboard snapshot saved")
        save_session_snapshot({
            "focus_score": insight.focus_score,
            "session_time_sec": session_sec,
            "productive_sec": aggregate.session_productive_time,
            "distracting_sec": aggregate.session_distracting_time,
            "switch_count": switch_count,
            "idle_sec": int(idle_sec),
        })

    risk_score = security_score

    return {
        "system_state": "idle" if collector.idle_detector.is_idle() else "active",
        "ai_engine_status": "running",
        "threat_level": threat,
        "session_time_sec": session_sec,
        "sync_status": "synced",
        "focus_score": insight.focus_score,
        "productivity_grade": insight.productivity_grade,
        "ai_suggestion": insight.suggestion,
        "work_mode": insight.mode,
        "health_index": insight.health_index,
        "trend": insight.trend,
        "top_apps": top_apps_with_category,
        "productivity_split": productivity_split,
        "focus_trend": list(focus_trend_history),
        "alerts": alerts,
        "cpu_usage": round(raw.cpu_usage, 1),
        "ram_usage": round(raw.ram_usage, 1),
        "network_upload": raw.network_bytes_sent,
        "network_download": raw.network_bytes_recv,
        "active_processes": collector.system_monitor.get_process_count(),
        "top_processes": processes,
        "network_history": list(network_history),
        "timestamp": raw.timestamp,
        "productive_sec": aggregate.session_productive_time,
        "distracting_sec": aggregate.session_distracting_time,
        "neutral_sec": aggregate.session_neutral_time,
        "switch_count": switch_count,
        "idle_ratio": round(idle_ratio * 100, 1),
        "risk_score": risk_score,
    }


def _default_state() -> dict:
    return {
        "system_state": "active",
        "ai_engine_status": "running",
        "threat_level": "low",
        "session_time_sec": 0,
        "sync_status": "connecting",
        "focus_score": 0,
        "productivity_grade": "-",
        "ai_suggestion": "Initializing...",
        "work_mode": "Balanced Work",
        "health_index": 0,
        "trend": "Stable",
        "top_apps": [],
        "productivity_split": {"productive": 0, "distracting": 0, "neutral": 100},
        "focus_trend": [],
        "alerts": [],
        "cpu_usage": 0,
        "ram_usage": 0,
        "network_upload": 0,
        "network_download": 0,
        "active_processes": 0,
        "top_processes": [],
        "network_history": [],
        "timestamp": "",
        "productive_sec": 0,
        "distracting_sec": 0,
        "neutral_sec": 0,
        "switch_count": 0,
        "idle_ratio": 0,
        "risk_score": 100,
    }


@app.get("/api/dashboard")
async def get_dashboard():
    return build_dashboard_state()


@app.get("/api/settings")
async def get_settings_api():
    s = get_settings()
    return {
        "idle_threshold_sec": get_setting("idle_threshold_sec", s.idle_threshold_sec),
        "focus_sensitivity": get_setting("focus_sensitivity", s.focus_sensitivity),
        "alert_sensitivity": get_setting("alert_sensitivity", s.alert_sensitivity),
        "refresh_interval_sec": get_setting("refresh_interval_sec", s.refresh_interval_sec),
        "theme": get_setting("theme", "dark"),
    }


@app.post("/api/settings")
async def update_settings(data: SettingsUpdate):
    global collector
    if data.idle_threshold_sec is not None:
        save_setting("idle_threshold_sec", data.idle_threshold_sec)
        if collector:
            collector.set_idle_threshold(data.idle_threshold_sec)
    if data.focus_sensitivity is not None:
        save_setting("focus_sensitivity", data.focus_sensitivity)
    if data.alert_sensitivity is not None:
        save_setting("alert_sensitivity", data.alert_sensitivity)
    if data.refresh_interval_sec is not None:
        save_setting("refresh_interval_sec", data.refresh_interval_sec)
    if data.theme is not None:
        save_setting("theme", data.theme)
    return {"ok": True}


@app.get("/api/reports/weekly")
async def get_weekly_report():
    data = get_weekly_summary()
    state = build_dashboard_state()
    data["recommendation"] = state.get("ai_suggestion", "-")
    data["switch_count"] = state.get("switch_count", 0)
    return data


@app.get("/api/reports/monthly")
async def get_monthly_report():
    return get_monthly_focus(30)


@app.get("/api/log")
async def get_log():
    return get_recent_logs(50)


@app.get("/api/reports/pdf/daily")
async def export_daily_pdf():
    state = build_dashboard_state()
    top_app = state.get("top_apps", [{}])[0].get("name", "-") if state.get("top_apps") else "-"
    data = {
        "focus_score": state.get("focus_score", 0),
        "productivity_grade": state.get("productivity_grade", "-"),
        "work_mode": state.get("work_mode", "-"),
        "productive_sec": state.get("productive_sec", 0),
        "top_app": top_app,
        "switch_count": state.get("switch_count", 0),
        "distractions_count": len([a for a in state.get("alerts", []) if a.get("type") in ("focus", "switching")]),
        "threats_count": len([a for a in state.get("alerts", []) if a.get("severity") == "critical"]),
    }
    pdf_bytes = generate_daily_pdf(data)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": "attachment; filename=daily_report.pdf"
    })


@app.get("/api/reports/pdf/weekly")
async def export_weekly_pdf():
    data = get_weekly_summary()
    state = build_dashboard_state()
    data["recommendation"] = state.get("ai_suggestion", "-")
    pdf_bytes = generate_weekly_pdf(data)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": "attachment; filename=weekly_report.pdf"
    })


@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    refresh = get_setting("refresh_interval_sec", 3)

    try:
        while True:
            state = build_dashboard_state()
            await websocket.send_json(state)
            await asyncio.sleep(refresh)
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)


static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    index = Path(__file__).parent.parent / "static" / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "FocusAI PRO MONITOR", "docs": "/docs"}
