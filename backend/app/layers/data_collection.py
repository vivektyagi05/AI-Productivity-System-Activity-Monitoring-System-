"""1️⃣ DATA COLLECTION LAYER - Low-Level System Monitoring."""
import psutil
import time
from datetime import datetime
from typing import Optional
from app.models.schemas import RawEvent

try:
    import win32gui
    import win32process
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False


class WindowTracker:
    """Active window detection and app switch events."""
    
    def get_active_window(self) -> tuple[str, str, Optional[int]]:
        """Get current active window title, app name, and PID."""
        if not WINDOWS_AVAILABLE:
            return "Unknown", "unknown", None
        try:
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            app_name = "unknown"
            if pid:
                try:
                    proc = psutil.Process(pid)
                    app_name = proc.name().lower().replace(".exe", "")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return title or "Unknown", app_name, pid
        except Exception:
            return "Unknown", "unknown", None


class IdleDetector:
    """User inactivity time detection."""
    
    def __init__(self, threshold_sec: int = 30):
        self.threshold = threshold_sec
        self._last_activity = time.time()
    
    def update_activity(self):
        self._last_activity = time.time()
    
    def get_idle_seconds(self) -> float:
        return time.time() - self._last_activity
    
    def is_idle(self) -> bool:
        return self.get_idle_seconds() >= self.threshold


class SystemMonitor:
    """CPU, RAM, Process list, Network IO."""
    
    def __init__(self):
        self._last_net = psutil.net_io_counters()
        self._last_check = time.time()
    
    def get_cpu_usage(self) -> float:
        return psutil.cpu_percent(interval=0.1)
    
    def get_ram_usage(self) -> float:
        mem = psutil.virtual_memory()
        return mem.percent
    
    def get_network_io(self) -> tuple[int, int]:
        net = psutil.net_io_counters()
        sent = net.bytes_sent - self._last_net.bytes_sent
        recv = net.bytes_recv - self._last_net.bytes_recv
        self._last_net = net
        return sent, recv
    
    def get_process_count(self) -> int:
        return len(psutil.pids())
    
    def get_top_processes_by_cpu(self, limit: int = 5) -> list[dict]:
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                p.info['cpu_percent'] = p.cpu_percent()
                if p.info['cpu_percent'] and p.info['cpu_percent'] > 0:
                    procs.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        procs.sort(key=lambda x: x.get('cpu_percent', 0) or 0, reverse=True)
        return procs[:limit]


class DataCollector:
    """Orchestrates all data collection."""
    
    def __init__(self, idle_threshold: int = 30):
        self.window_tracker = WindowTracker()
        self.idle_detector = IdleDetector(idle_threshold)
        self.system_monitor = SystemMonitor()
        self._last_window = ("", "", None)
        self._window_start = time.time()
    
    def set_idle_threshold(self, sec: int):
        self.idle_detector.threshold = sec
    
    def collect_raw_event(self) -> RawEvent:
        """Collect single raw event observation."""
        title, app_name, pid = self.window_tracker.get_active_window()
        
        # Update idle - consider activity if window changed
        if (title, app_name, pid) != self._last_window:
            self.idle_detector.update_activity()
            self._last_window = (title, app_name, pid)
            self._window_start = time.time()
        
        duration = int(time.time() - self._window_start)
        cpu = self.system_monitor.get_cpu_usage()
        ram = self.system_monitor.get_ram_usage()
        net_sent, net_recv = self.system_monitor.get_network_io()
        
        return RawEvent(
            timestamp=datetime.now().isoformat(),
            window=title,
            app_name=app_name,
            duration=duration,
            cpu_usage=cpu,
            ram_usage=ram,
            network_bytes_sent=net_sent,
            network_bytes_recv=net_recv,
            pid=pid
        )

