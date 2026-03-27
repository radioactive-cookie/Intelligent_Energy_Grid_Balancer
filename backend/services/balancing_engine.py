"""Grid Balancing Decision Engine"""
from models.balancing_action import BalancingAction
from models.grid_state import GridState
from models.battery_storage import BatteryStorage
from models.demand_profile import DemandProfile
from utils.helpers import get_logger, is_frequency_critical

logger = get_logger(__name__)

class BalancingEngine:
    """Core balancing decision engine"""
    
    def __init__(self):
        self.action_history = []
        self.decision_count = 0
    
    def decide_action(
        self,
        grid_state: GridState,
        battery: BatteryStorage,
        demand: DemandProfile,
        solar_generation: float,
        wind_generation: float
    ) -> BalancingAction:
        """
        Decide the best balancing action based on grid state.
        
        Decision Logic:
        1. If frequency is critical -> Emergency response
        2. If generation > demand -> Store excess energy
        3. If demand > generation -> Release energy from battery
        4. If battery is low -> Trigger demand response
        """
        self.decision_count += 1
        total_generation = solar_generation + wind_generation
        imbalance = total_generation - demand.current_demand
        
        # Check frequency critical condition
        if is_frequency_critical(grid_state.frequency, 50.0, 1.5):
            if imbalance < 0:
                action = self._create_action("demand_response", imbalance, "Critical frequency detected")
            else:
                action = self._create_action("shed_load", imbalance, "Critical frequency detected")
            action.priority = 10
            logger.critical(f"CRITICAL: Frequency {grid_state.frequency} Hz - Action: {action.action}")
            return action
        
        # Battery level considerations
        soc_percentage = battery.state_of_charge
        
        if soc_percentage < 20:
            # Battery critically low - demand response
            reasoning = f"Battery critically low at {soc_percentage:.1f}% SOC"
            action = self._create_action("demand_response", imbalance, reasoning)
            action.priority = 9
        elif imbalance > 100:  # Generation significantly exceeds demand
            # Store excess energy
            reasoning = f"Excess generation: {imbalance:.1f} kW. Storing in battery (SOC: {soc_percentage:.1f}%)"
            action = self._create_action("store", imbalance, reasoning)
            if soc_percentage > 95:
                action.magnitude = min(imbalance, battery.charge_rate * 0.5)
                action.reasoning = f"Battery near full capacity. Limited charging: {action.magnitude:.1f} kW"
        elif imbalance < -100:  # Demand significantly exceeds generation
            # Release energy from battery
            if soc_percentage > 20:
                reasoning = f"Demand exceeds generation by {abs(imbalance):.1f} kW. Releasing battery (SOC: {soc_percentage:.1f}%)"
                action = self._create_action("release", imbalance, reasoning)
                action.magnitude = min(abs(imbalance), battery.discharge_rate)
            else:
                reasoning = f"Demand exceeds generation by {abs(imbalance):.1f} kW but battery low. Demand response required"
                action = self._create_action("demand_response", imbalance, reasoning)
                action.priority = 8
        elif 20 < imbalance < 100:  # Slight excess generation
            reasoning = f"Slight excess generation: {imbalance:.1f} kW. Gradual charging (SOC: {soc_percentage:.1f}%)"
            action = self._create_action("store", imbalance, reasoning)
            action.magnitude = min(imbalance, 50)  # Gradual charging
        elif -100 < imbalance < -20:  # Slight demand excess
            if soc_percentage > 40:
                reasoning = f"Slight demand excess: {abs(imbalance):.1f} kW. Gradual discharge (SOC: {soc_percentage:.1f}%)"
                action = self._create_action("release", imbalance, reasoning)
                action.magnitude = min(abs(imbalance), 50)  # Gradual discharge
            else:
                reasoning = "Slight demand excess and battery moderate. Standby."
                action = self._create_action("none", 0, reasoning)
        else:
            action = self._create_action("none", 0, "Grid balanced. No action needed.")
        
        # Log the decision
        logger.info(f"Decision #{self.decision_count}: {action.action} - {action.reasoning}")
        self.action_history.append(action)
        return action
    
    def _create_action(self, action_type: str, imbalance: float, reasoning: str) -> BalancingAction:
        """Helper to create a BalancingAction instance"""
        return BalancingAction(
            action_id=f"ACTION_{self.decision_count:06d}",
            action=action_type,
            reasoning=reasoning,
            magnitude=abs(imbalance),
            details={
                "imbalance": imbalance,
                "decision_number": self.decision_count
            }
        )
    
    def get_grid_stability_score(self, grid_state: GridState, battery: BatteryStorage) -> float:
        """
        Calculate overall grid stability score (0-100)
        
        Factors:
        - Frequency deviation (40%)
        - Load balance (30%)
        - Battery health (20%)
        - System reserves (10%)
        """
        freq_score = max(0, 100 - abs(grid_state.frequency - 50.0) * 50)
        balance_score = max(0, 100 - abs(grid_state.imbalance) / max(1, grid_state.total_demand) * 100)
        battery_score = battery.health
        reserve_score = battery.state_of_charge
        
        stability = (freq_score * 0.4 + balance_score * 0.3 + battery_score * 0.2 + reserve_score * 0.1)
        return min(100, max(0, stability))
    
    def get_action_history(self, limit: int = 100):
        """Get recent action history"""
        return self.action_history[-limit:]
