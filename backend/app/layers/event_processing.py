"""2️⃣ EVENT PROCESSING LAYER - Data Structuring & Aggregation."""
from collections import defaultdict
from app.models.schemas import RawEvent, SessionAggregate
from app.config import get_settings


class SessionAggregator:
    """Aggregates raw events into session metrics."""
    
    def __init__(self):
        self.settings = get_settings()
        self.app_durations: dict[str, int] = defaultdict(int)
        self.productive_time = 0
        self.distracting_time = 0
        self.neutral_time = 0
        self.session_start = None
        self._last_event: RawEvent | None = None
        self._switch_count = 0
    
    def _classify_app(self, app_name: str) -> str:
        """Classify app as productive, distracting, or neutral."""
        app_lower = app_name.lower()
        for p in self.settings.productive_apps:
            if p in app_lower:
                return "productive"
        for d in self.settings.distracting_apps:
            if d in app_lower:
                return "distracting"
        return "neutral"
    
    def process_event(self, event: RawEvent, poll_interval_sec: int = 3) -> SessionAggregate:
        """Process raw event and update aggregates. Adds delta since last poll."""
        import time
        if self.session_start is None:
            self.session_start = time.time()
        
        last_duration = getattr(self, '_last_duration', 0)
        
        if self._last_event and self._last_event.app_name != event.app_name:
            self._switch_count += 1
            delta_old = min(poll_interval_sec, last_duration)
            old_class = self._classify_app(self._last_event.app_name)
            old_key = self._last_event.app_name or "unknown"
            self.app_durations[old_key] = self.app_durations.get(old_key, 0) + delta_old
            if old_class == "productive":
                self.productive_time += delta_old
            elif old_class == "distracting":
                self.distracting_time += delta_old
            else:
                self.neutral_time += delta_old
            delta = min(event.duration, poll_interval_sec)
        else:
            delta = min(max(0, event.duration - last_duration), poll_interval_sec)
        
        self._last_duration = event.duration
        classification = self._classify_app(event.app_name)
        app_key = event.app_name or "unknown"
        self.app_durations[app_key] = self.app_durations.get(app_key, 0) + delta
        
        if classification == "productive":
            self.productive_time += delta
        elif classification == "distracting":
            self.distracting_time += delta
        else:
            self.neutral_time += delta
        
        self._last_event = event
        return self.get_aggregate()
    
    def get_aggregate(self) -> SessionAggregate:
        """Get current session aggregate."""
        total = self.productive_time + self.distracting_time + self.neutral_time
        top_apps = sorted(
            [{"name": k, "duration": v} for k, v in self.app_durations.items()],
            key=lambda x: x["duration"],
            reverse=True
        )[:10]
        
        return SessionAggregate(
            session_productive_time=self.productive_time,
            session_distracting_time=self.distracting_time,
            session_neutral_time=self.neutral_time,
            top_apps=top_apps,
            total_active_time=int(total)
        )
    
    def get_switch_count(self) -> int:
        return self._switch_count
    
    def reset_session(self):
        """Reset for new session."""
        self.app_durations.clear()
        self.productive_time = 0
        self.distracting_time = 0
        self.neutral_time = 0
        self.session_start = None
        self._last_event = None
        self._switch_count = 0


class ContextCleaner:
    """Window name normalization and duplicate merging."""
    
    @staticmethod
    def normalize_window_name(name: str) -> str:
        """Normalize window title for consistency."""
        if not name or name == "Unknown":
            return "Unknown"
        # Take first part before common separators
        for sep in [" - ", " | ", " — "]:
            if sep in name:
                return name.split(sep)[-1].strip()
        return name[:50]
