"""3️⃣ AI INTELLIGENCE LAYER - Behaviour Analytics."""
import time
from collections import deque
from app.models.schemas import SessionAggregate, AIInsight, FeatureVector, WorkMode
from app.layers.event_processing import SessionAggregator


class FeatureExtractor:
    """Extract features from session data for AI scoring."""
    
    def __init__(self):
        self._focus_blocks: deque = deque(maxlen=20)
        self._switch_times: deque = deque(maxlen=100)
        self._session_start = time.time()
    
    def extract(
        self,
        aggregate: SessionAggregate,
        switch_count: int,
        idle_ratio: float = 0.0
    ) -> FeatureVector:
        """Extract feature vector from session aggregate."""
        
        total = aggregate.total_active_time or 1
        
        productive_ratio = (
            aggregate.session_productive_time / total
            if total > 0 else 0
        )
        
        distracting_ratio = (
            aggregate.session_distracting_time / total
            if total > 0 else 0
        )
        
        session_minutes = (time.time() - self._session_start) / 60
        session_minutes = session_minutes if session_minutes > 0 else 0.1
        
        switch_rate = switch_count / session_minutes
        
        # Estimate avg focus block (minutes)
        avg_focus_block = (
            aggregate.session_productive_time / (switch_count + 1) / 60
            if switch_count > 0 else 25
        )
        
        return FeatureVector(
            productive_ratio=round(productive_ratio, 3),
            switch_rate=round(switch_rate, 2),
            idle_ratio=round(idle_ratio, 3),
            avg_focus_block=round(avg_focus_block, 1),
            cpu_spike_freq=0,
            net_spike_freq=0
        )


class AIScoringEngine:
    """Deterministic + weighted intelligence for focus & behaviour."""
    
    def calculate_focus_score(self, features: FeatureVector) -> int:
        """Focus Score = (productive_ratio * 100) - penalties."""
        base = features.productive_ratio * 100
        
        # Switch rate penalty (max -20)
        switch_penalty = min(20, features.switch_rate * 3)
        base -= switch_penalty
        
        # Idle penalty (max -15)
        idle_penalty = features.idle_ratio * 100
        base -= idle_penalty
        
        return max(0, min(100, int(base)))
    
    def classify_behaviour(self, features: FeatureVector) -> str:
        """Classify work mode from features."""
        if features.productive_ratio > 0.7 and features.switch_rate < 3:
            return WorkMode.DEEP_WORK.value
        if features.productive_ratio > 0.5 and features.switch_rate < 6:
            return WorkMode.BALANCED_WORK.value
        if features.switch_rate > 8 or features.productive_ratio < 0.3:
            return WorkMode.DISTRACTED.value
        if features.idle_ratio > 0.3:
            return WorkMode.IDLE_HEAVY.value
        return WorkMode.UNSTABLE.value
    
    def get_productivity_grade(self, focus_score: int) -> str:
        """Convert focus score to letter grade."""
        if focus_score >= 85:
            return "A"
        if focus_score >= 70:
            return "B"
        if focus_score >= 50:
            return "C"
        return "D"
    
    def generate_suggestion(self, mode: str, focus_score: int) -> str:
        """Generate actionable AI suggestion."""
        if mode == WorkMode.DEEP_WORK.value:
            return "Deep Work Mode Detected — Maintain momentum!"
        if mode == WorkMode.DISTRACTED.value:
            return "Reduce app switching. Consider focus blocks."
        if mode == WorkMode.IDLE_HEAVY.value:
            return "Take a short break or resume work."
        if focus_score < 50:
            return "Focus declining. Reduce distractions."
        return "Balanced session. Keep steady pace."


class AIInsightGenerator:
    """Orchestrates AI layer and produces insights."""
    
    def __init__(self):
        self.extractor = FeatureExtractor()
        self.scorer = AIScoringEngine()
        self._focus_history: deque = deque(maxlen=20)
    
    def generate(
        self,
        aggregate: SessionAggregate,
        switch_count: int,
        security_score: int = 92,
        idle_ratio: float = 0
    ) -> AIInsight:
        """Generate complete AI insight."""
        features = self.extractor.extract(aggregate, switch_count, idle_ratio)
        focus_score = self.scorer.calculate_focus_score(features)
        mode = self.scorer.classify_behaviour(features)
        grade = self.scorer.get_productivity_grade(focus_score)
        suggestion = self.scorer.generate_suggestion(mode, focus_score)
        
        # Health index: blend focus + security
        health_index = int((focus_score * 0.6 + security_score * 0.4))
        health_index = min(100, health_index)
        
        # Trend
        self._focus_history.append(focus_score)
        if len(self._focus_history) >= 3:
            recent = list(self._focus_history)[-3:]
            if recent[-1] > recent[0] + 5:
                trend = "Improving"
            elif recent[-1] < recent[0] - 5:
                trend = "Declining"
            else:
                trend = "Stable"
        else:
            trend = "Stable"
        
        return AIInsight(
            focus_score=focus_score,
            productivity_grade=grade,
            mode=mode,
            health_index=health_index,
            trend=trend,
            suggestion=suggestion,
            risk_level="Low" if security_score > 80 else "Medium"
        )
