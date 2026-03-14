"""Pydantic schemas for API."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class SystemState(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"


class ThreatLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class WorkMode(str, Enum):
    DEEP_WORK = "Deep Work"
    BALANCED_WORK = "Balanced Work"
    DISTRACTED = "Distracted"
    UNSTABLE = "Unstable Session"
    IDLE_HEAVY = "Idle Heavy"


class RawEvent(BaseModel):
    """Raw data from Data Collection Layer."""
    timestamp: str
    window: str
    app_name: str
    duration: int
    cpu_usage: float
    ram_usage: float
    network_bytes_sent: int
    network_bytes_recv: int
    pid: Optional[int] = None


class SessionAggregate(BaseModel):
    """Processed session data."""
    session_productive_time: int
    session_distracting_time: int
    session_neutral_time: int
    top_apps: list[dict]
    total_active_time: int


class FeatureVector(BaseModel):
    """AI feature extraction output."""
    productive_ratio: float
    switch_rate: float
    idle_ratio: float
    avg_focus_block: float
    cpu_spike_freq: int
    net_spike_freq: int


class AIInsight(BaseModel):
    """AI Intelligence output."""
    focus_score: int
    productivity_grade: str  # A, B, C
    mode: str
    health_index: int
    trend: str  # Improving, Stable, Declining
    suggestion: str
    risk_level: str


class SecurityAlert(BaseModel):
    """Security intelligence alert."""
    type: str
    message: str
    severity: str  # warning, critical, stable
    process_name: Optional[str] = None


class DashboardState(BaseModel):
    """Complete dashboard state for real-time sync."""
    system_state: str
    ai_engine_status: str
    threat_level: str
    session_time_sec: int
    sync_status: str
    focus_score: int
    productivity_grade: str
    ai_suggestion: str
    work_mode: str
    health_index: int
    trend: str
    top_apps: list[dict]
    productivity_split: dict
    focus_trend: list[dict]
    alerts: list[dict]
    cpu_usage: float
    ram_usage: float
    network_upload: int
    network_download: int
    active_processes: int
    timestamp: str
