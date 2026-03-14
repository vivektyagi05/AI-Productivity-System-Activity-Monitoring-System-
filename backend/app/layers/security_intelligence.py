"""4️⃣ SECURITY INTELLIGENCE LAYER - Behavioural Threat Monitoring."""
from collections import deque
from app.models.schemas import SecurityAlert, RawEvent


class CPUSpikeAnalyzer:
    """Detect abnormal CPU usage patterns."""
    
    def __init__(self, threshold: float = 70.0):
        self.threshold = threshold
        self._history: deque = deque(maxlen=10)
    
    def check(self, cpu_usage: float, process_name: str = "") -> SecurityAlert | None:
        self._history.append(cpu_usage)
        if cpu_usage > self.threshold:
            return SecurityAlert(
                type="cpu_spike",
                message=f"High CPU usage: {process_name or 'system'} ({cpu_usage:.0f}%)",
                severity="warning" if cpu_usage < 90 else "critical",
                process_name=process_name or None
            )
        return None


class NetworkSpikeAnalyzer:
    """Detect abnormal network bursts."""
    
    def __init__(self, threshold_bytes: int = 5_000_000):
        self.threshold = threshold_bytes
        self._last_bytes = 0
    
    def check(self, bytes_sent: int, bytes_recv: int) -> SecurityAlert | None:
        total = bytes_sent + bytes_recv
        if total > self.threshold and self._last_bytes > 0:
            spike = SecurityAlert(
                type="network_spike",
                message=f"Suspicious network spike: {total // 1024} KB",
                severity="warning"
            )
            self._last_bytes = total
            return spike
        self._last_bytes = total
        return None


class SecurityIntelligence:
    """Orchestrates security monitoring."""
    
    def __init__(self):
        self.cpu_analyzer = CPUSpikeAnalyzer()
        self.net_analyzer = NetworkSpikeAnalyzer()
        self._alerts: list[SecurityAlert] = []
        self._known_processes = {"explorer", "code", "cursor", "chrome", "msedge", "firefox"}
    
    def analyze(self, event: RawEvent, top_processes: list[dict]) -> tuple[int, list[SecurityAlert]]:
        """Analyze and return security score + alerts."""
        self._alerts = []
        
        # CPU spike check
        if event.cpu_usage > 70:
            top_proc = top_processes[0]["name"] if top_processes else "system"
            alert = self.cpu_analyzer.check(event.cpu_usage, top_proc)
            if alert:
                self._alerts.append(alert)
        
        # Network spike
        net_alert = self.net_analyzer.check(
            event.network_bytes_sent,
            event.network_bytes_recv
        )
        if net_alert:
            self._alerts.append(net_alert)
        
        # Calculate risk score (100 = safe)
        score = 100
        for a in self._alerts:
            if a.severity == "critical":
                score -= 25
            elif a.severity == "warning":
                score -= 10
        score = max(0, min(100, score))
        
        return score, self._alerts
