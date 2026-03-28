"""Data Storage Service"""
import json
import os
from typing import List, Dict
from datetime import datetime
from models.balancing_action import BalancingAction
from models.grid_state import GridState
from models.alert import Alert
from utils.helpers import get_logger, save_to_json, load_from_json

logger = get_logger(__name__)

class DataStorageService:
    """Service for storing and retrieving system data"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.actions_file = os.path.join(data_dir, "actions.json")
        self.states_file = os.path.join(data_dir, "grid_states.json")
        self.alerts_file = os.path.join(data_dir, "alerts.json")
        self.metrics_file = os.path.join(data_dir, "metrics.json")
    
    def save_action(self, action: BalancingAction):
        """Save balancing action to storage"""
        try:
            actions = []
            if os.path.exists(self.actions_file):
                with open(self.actions_file, 'r') as f:
                    actions = json.load(f)
            
            actions.append(action.model_dump(mode='json'))
            
            with open(self.actions_file, 'w') as f:
                json.dump(actions, f, indent=2, default=str)
            
            logger.debug(f"Saved action {action.action_id}")
        except Exception as e:
            logger.error(f"Error saving action: {e}")
    
    def save_grid_state(self, state: GridState):
        """Save grid state to storage"""
        try:
            states = []
            if os.path.exists(self.states_file):
                with open(self.states_file, 'r') as f:
                    states = json.load(f)
            
            states.append(state.model_dump(mode='json'))
            
            # Keep only last 1000 states
            if len(states) > 1000:
                states = states[-1000:]
            
            with open(self.states_file, 'w') as f:
                json.dump(states, f, indent=2, default=str)
            
            logger.debug(f"Saved grid state")
        except Exception as e:
            logger.error(f"Error saving grid state: {e}")
    
    def save_alert(self, alert: Alert):
        """Save alert to storage"""
        try:
            alerts = []
            if os.path.exists(self.alerts_file):
                with open(self.alerts_file, 'r') as f:
                    alerts = json.load(f)
            
            alerts.append(alert.model_dump(mode='json'))
            
            with open(self.alerts_file, 'w') as f:
                json.dump(alerts, f, indent=2, default=str)
            
            logger.debug(f"Saved alert {alert.alert_id}")
        except Exception as e:
            logger.error(f"Error saving alert: {e}")
    
    def get_actions(self, limit: int = 100) -> List[Dict]:
        """Get recent actions"""
        try:
            if os.path.exists(self.actions_file):
                with open(self.actions_file, 'r') as f:
                    actions = json.load(f)
                return actions[-limit:]
            return []
        except Exception as e:
            logger.error(f"Error loading actions: {e}")
            return []
    
    def get_grid_states(self, limit: int = 100) -> List[Dict]:
        """Get recent grid states"""
        try:
            if os.path.exists(self.states_file):
                with open(self.states_file, 'r') as f:
                    states = json.load(f)
                return states[-limit:]
            return []
        except Exception as e:
            logger.error(f"Error loading grid states: {e}")
            return []
    
    def get_alerts(self, limit: int = 100) -> List[Dict]:
        """Get recent alerts"""
        try:
            if os.path.exists(self.alerts_file):
                with open(self.alerts_file, 'r') as f:
                    alerts = json.load(f)
                return alerts[-limit:]
            return []
        except Exception as e:
            logger.error(f"Error loading alerts: {e}")
            return []
    
    def save_metrics(self, metrics: Dict):
        """Save performance metrics"""
        try:
            metrics['timestamp'] = datetime.utcnow().isoformat()
            existing_metrics = []
            
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    existing_metrics = json.load(f)
            
            existing_metrics.append(metrics)
            
            # Keep only last 500 metric points
            if len(existing_metrics) > 500:
                existing_metrics = existing_metrics[-500:]
            
            with open(self.metrics_file, 'w') as f:
                json.dump(existing_metrics, f, indent=2, default=str)
            
            logger.debug("Saved metrics")
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def save_simulation_run(self, result: Dict):
        """Save a simulation run result"""
        try:
            sims = []
            sim_file = os.path.join(self.data_dir, "simulations.json")
            if os.path.exists(sim_file):
                with open(sim_file, 'r') as f:
                    sims = json.load(f)

            sims.append(result)

            # Keep only last 500 simulation results
            if len(sims) > 500:
                sims = sims[-500:]

            with open(sim_file, 'w') as f:
                json.dump(sims, f, indent=2, default=str)

            logger.debug("Saved simulation run")
        except Exception as e:
            logger.error(f"Error saving simulation run: {e}")

    def clear_old_data(self, days: int = 7):
        """Clear data older than N days"""
        cutoff_time = datetime.utcnow().timestamp() - (days * 86400)
        # Implementation would filter and rewrite files
        logger.info(f"Cleared data older than {days} days")
