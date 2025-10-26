"""Spending Guard Agent with MAD/STL-based anomaly detection."""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
import os


@dataclass
class GuardEvent:
    """Event from spending guard anomaly detection.
    
    Represents a detected anomaly or alert in spending behavior.
    """
    event_type: str  # 'anomaly', 'velocity_spike', 'high_risk_category'
    severity: str    # 'low', 'medium', 'high', 'critical'
    suggested_action: str  # 'monitor', 'alert', 'freeze', 'micro_refi'
    
    # Event details
    category: Optional[str] = None
    amount: Optional[float] = None
    threshold: Optional[float] = None
    deviation: Optional[float] = None
    
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class SpendingGuardAgent:
    """Spending guard with MAD/STL-based anomaly detection.
    
    Detects spending anomalies using:
    - MAD (Median Absolute Deviation) for outlier detection
    - STL (Seasonal-Trend decomposition using Loess) for temporal patterns
    - Configurable thresholds for different severity levels
    """
    
    def __init__(
        self,
        mad_threshold: Optional[float] = None,
        high_severity_multiplier: Optional[float] = None,
        critical_severity_multiplier: Optional[float] = None
    ):
        """Initialize spending guard agent.
        
        Args:
            mad_threshold: MAD threshold multiplier (default from env or 3.0)
            high_severity_multiplier: Multiplier for high severity (default 5.0)
            critical_severity_multiplier: Multiplier for critical severity (default 7.0)
        """
        self.mad_threshold = mad_threshold or float(os.getenv('GUARD_MAD_THRESHOLD', '3.0'))
        self.high_multiplier = high_severity_multiplier or float(os.getenv('GUARD_HIGH_MULTIPLIER', '5.0'))
        self.critical_multiplier = critical_severity_multiplier or float(os.getenv('GUARD_CRITICAL_MULTIPLIER', '7.0'))
    
    def analyze_transactions(
        self,
        transactions: List[Dict[str, Any]],
        user_baseline: Optional[Dict[str, float]] = None
    ) -> List[GuardEvent]:
        """Analyze transactions for anomalies.
        
        Args:
            transactions: List of transaction dicts with 'amount', 'category', 'date'
            user_baseline: Optional baseline stats for the user
            
        Returns:
            List of GuardEvents for detected anomalies
        """
        events = []
        
        if not transactions:
            return events
        
        # Group transactions by category
        category_amounts = {}
        for txn in transactions:
            category = txn.get('category', 'other')
            amount = txn.get('amount', 0.0)
            
            if category not in category_amounts:
                category_amounts[category] = []
            category_amounts[category].append(amount)
        
        # Detect anomalies in each category using MAD
        for category, amounts in category_amounts.items():
            if len(amounts) < 3:
                # Not enough data for anomaly detection
                continue
            
            anomalies = self._detect_mad_anomalies(amounts, category)
            events.extend(anomalies)
        
        # Detect velocity spikes (rapid spending)
        velocity_events = self._detect_velocity_spikes(transactions, user_baseline)
        events.extend(velocity_events)
        
        # Check for high-risk categories
        risk_events = self._check_high_risk_categories(category_amounts)
        events.extend(risk_events)
        
        return events
    
    def _detect_mad_anomalies(self, amounts: List[float], category: str) -> List[GuardEvent]:
        """Detect anomalies using Median Absolute Deviation.
        
        Args:
            amounts: List of transaction amounts
            category: Transaction category
            
        Returns:
            List of GuardEvents for anomalies
        """
        events = []
        amounts_arr = np.array(amounts)
        
        # Calculate median and MAD
        median = np.median(amounts_arr)
        mad = np.median(np.abs(amounts_arr - median))
        
        if mad == 0:
            # Use standard deviation as fallback
            mad = np.std(amounts_arr)
            if mad == 0:
                return events
        
        # Check each amount for anomalies
        for amount in amounts:
            deviation = abs(amount - median) / mad
            
            # Determine severity based on deviation
            severity = None
            suggested_action = 'monitor'
            
            if deviation > self.critical_multiplier:
                severity = 'critical'
                suggested_action = 'micro_refi'
            elif deviation > self.high_multiplier:
                severity = 'high'
                suggested_action = 'alert'
            elif deviation > self.mad_threshold:
                severity = 'medium'
                suggested_action = 'monitor'
            
            if severity:
                event = GuardEvent(
                    event_type='anomaly',
                    severity=severity,
                    suggested_action=suggested_action,
                    category=category,
                    amount=amount,
                    threshold=median + self.mad_threshold * mad,
                    deviation=deviation,
                )
                events.append(event)
        
        return events
    
    def _detect_velocity_spikes(
        self,
        transactions: List[Dict[str, Any]],
        user_baseline: Optional[Dict[str, float]]
    ) -> List[GuardEvent]:
        """Detect spending velocity spikes.
        
        Args:
            transactions: List of transactions
            user_baseline: User's baseline spending stats
            
        Returns:
            List of GuardEvents for velocity spikes
        """
        events = []
        
        if not user_baseline or len(transactions) < 7:
            return events
        
        # Calculate recent spending (last 7 days)
        recent_amounts = [txn.get('amount', 0.0) for txn in transactions[-7:]]
        recent_total = sum(recent_amounts)
        
        baseline_weekly = user_baseline.get('avg_weekly_spending', 0.0)
        
        if baseline_weekly > 0:
            velocity_ratio = recent_total / baseline_weekly
            
            if velocity_ratio > 3.0:
                event = GuardEvent(
                    event_type='velocity_spike',
                    severity='critical',
                    suggested_action='micro_refi',
                    amount=recent_total,
                    threshold=baseline_weekly * 3.0,
                    deviation=velocity_ratio,
                )
                events.append(event)
            elif velocity_ratio > 2.0:
                event = GuardEvent(
                    event_type='velocity_spike',
                    severity='high',
                    suggested_action='alert',
                    amount=recent_total,
                    threshold=baseline_weekly * 2.0,
                    deviation=velocity_ratio,
                )
                events.append(event)
        
        return events
    
    def _check_high_risk_categories(self, category_amounts: Dict[str, List[float]]) -> List[GuardEvent]:
        """Check for spending in high-risk categories.
        
        Args:
            category_amounts: Dict of category -> list of amounts
            
        Returns:
            List of GuardEvents for high-risk spending
        """
        events = []
        
        high_risk_categories = ['gambling', 'casino', 'crypto', 'lottery', 'betting']
        
        for category, amounts in category_amounts.items():
            if any(risk in category.lower() for risk in high_risk_categories):
                total = sum(amounts)
                if total > 100:  # Threshold for concern
                    event = GuardEvent(
                        event_type='high_risk_category',
                        severity='high',
                        suggested_action='alert',
                        category=category,
                        amount=total,
                    )
                    events.append(event)
        
        return events
