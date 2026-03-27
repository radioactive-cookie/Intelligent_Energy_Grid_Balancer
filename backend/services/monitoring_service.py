"""Grid Monitoring Service"""
from typing import List, Optional
from datetime import datetime
from models.alert import Alert
from models.grid_state import GridState
from models.battery_storage import BatteryStorage
from utils.helpers import get_logger, is_frequency_stable, is_frequency_critical

logger = get_logger(__name__)

class GridMonitoringService:
    """Service for monitoring grid health and generating alerts"""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_counter = 0
    
    def check_grid_health(
        self,
        grid_state: GridState,
        battery: BatteryStorage,
        generation: float,
        demand: float
    ) -> List[Alert]:
        """Check multiple grid health conditions and generate alerts"""
        new_alerts = []
        
        # Check frequency stability
        if is_frequency_critical(grid_state.frequency, 50.0, 1.5):
            new_alerts.append(self._create_alert(
                "frequency_critical",
                f"Grid frequency critically low: {grid_state.frequency} Hz (±1.5 Hz threshold exceeded)",
                "critical",
                "GridFrequencyMonitor"
            ))
        elif not is_frequency_stable(grid_state.frequency, 50.0, 0.5):
            new_alerts.append(self._create_alert(
                "frequency_deviation",
                f"Grid frequency deviation: {grid_state.frequency} Hz (±0.5 Hz tolerance exceeded)",
                "high",
                "GridFrequencyMonitor"
            ))
        
        # Check battery status
        if battery.state_of_charge < 10:
            new_alerts.append(self._create_alert(
                "battery_low",
                f"CRITICAL: Battery critically low at {battery.state_of_charge:.1f}% SOC",
                "critical",
                "BatteryMonitor"
            ))
        elif battery.state_of_charge < 20:
            new_alerts.append(self._create_alert(
                "battery_low",
                f"WARNING: Battery low at {battery.state_of_charge:.1f}% SOC",
                "high",
                "BatteryMonitor"
            ))
        
        # Check demand spike
        if demand > 2000:
            severity = "high" if 2000 < demand < 2500 else "critical"
            new_alerts.append(self._create_alert(
                "demand_spike",
                f"Demand spike detected: {demand:.1f} kW",
                severity,
                "DemandAnalyzer"
            ))
        
        # Check generation drop
        if generation < 200 and datetime.now().hour > 6 and datetime.now().hour < 18:
            new_alerts.append(self._create_alert(
                "generation_drop",
                f"Generation drop during day hours: {generation:.1f} kW",
                "medium",
                "GenerationMonitor"
            ))
        
        # Check imbalance
        imbalance_percentage = abs(grid_state.imbalance) / max(1, grid_state.total_demand) * 100
        if imbalance_percentage > 15:
            severity = "high" if imbalance_percentage < 25 else "critical"
            new_alerts.append(self._create_alert(
                "imbalance",
                f"Supply-demand imbalance: {grid_state.imbalance:.1f} kW ({imbalance_percentage:.1f}%)",
                severity,
                "BalancingEngine"
            ))
        
        # Add to alert list and log
        for alert in new_alerts:
            self.alerts.append(alert)
            logger.warning(f"ALERT: {alert.type} - {alert.message} (Severity: {alert.severity})")
        
        return new_alerts
    
    def resolve_alert(self, alert_id: str):
        """Mark an alert as resolved"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolution_time = datetime.utcnow()
                logger.info(f"Alert {alert_id} resolved")
                break
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all unresolved alerts"""
        return [a for a in self.alerts if not a.resolved]
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return self.alerts[-limit:]
    
    def get_alert_stats(self) -> dict:
        """Get alert statistics"""
        active = self.get_active_alerts()
        
        return {
            "total_alerts": len(self.alerts),
            "active_alerts": len(active),
            "critical": len([a for a in active if a.severity == "critical"]),
            "high": len([a for a in active if a.severity == "high"]),
            "medium": len([a for a in active if a.severity == "medium"]),
            "low": len([a for a in active if a.severity == "low"]),
        }
    
    def _create_alert(self, alert_type: str, message: str, severity: str, component: str) -> Alert:
        """Helper to create alert"""
        self.alert_counter += 1
        return Alert(
            alert_id=f"ALERT_{self.alert_counter:06d}",
            type=alert_type,
            message=message,
            severity=severity,
            component=component,
            timestamp=datetime.utcnow()
        )
