"""Example client for testing the Intelligent Energy Grid Balancer API"""

import requests
import json
import time
import websocket
from datetime import datetime

BASE_URL = "http://localhost:8000"

class GridBalancerClient:
    """Client for interacting with the Grid Balancer API"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self):
        """Check service health"""
        response = self.session.get(f"{self.base_url}/health")
        return response.json()
    
    def get_grid_status(self):
        """Get current grid status"""
        response = self.session.get(f"{self.base_url}/grid/status")
        return response.json()
    
    def get_solar_generation(self):
        """Get current solar generation"""
        response = self.session.get(f"{self.base_url}/energy/solar")
        return response.json()
    
    def get_wind_generation(self):
        """Get current wind generation"""
        response = self.session.get(f"{self.base_url}/energy/wind")
        return response.json()
    
    def get_battery_status(self):
        """Get battery status"""
        response = self.session.get(f"{self.base_url}/battery/status")
        return response.json()
    
    def run_balancing(self):
        """Run balancing engine"""
        response = self.session.post(f"{self.base_url}/balance/run")
        return response.json()
    
    def get_alerts(self):
        """Get all alerts"""
        response = self.session.get(f"{self.base_url}/alerts")
        return response.json()
    
    def get_metrics(self):
        """Get system metrics"""
        response = self.session.get(f"{self.base_url}/metrics")
        return response.json()
    
    def predict_solar(self, hours: int = 24):
        """Predict solar generation"""
        response = self.session.post(f"{self.base_url}/predict/generation/solar?hours={hours}")
        return response.json()
    
    def simulate_scenario(self, sunlight_level: float, wind_speed: float, demand_spike: float):
        """Simulate a scenario"""
        params = {
            "sunlight_level": sunlight_level,
            "wind_speed": wind_speed,
            "demand_spike": demand_spike
        }
        response = self.session.post(f"{self.base_url}/simulate/scenario", params=params)
        return response.json()

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_api():
    """Run test suite"""
    client = GridBalancerClient()
    
    try:
        # Test 1: Health Check
        print_section("1. HEALTH CHECK")
        health = client.health_check()
        print(json.dumps(health, indent=2))
        
        # Test 2: Get Grid Status
        print_section("2. GRID STATUS")
        grid = client.get_grid_status()
        print(f"Frequency: {grid['frequency']} Hz")
        print(f"Generation: {grid['total_generation']:.2f} kW")
        print(f"Demand: {grid['total_demand']:.2f} kW")
        print(f"Stability Score: {grid['grid_stability_score']:.1f}/100")
        print(f"Is Stable: {grid['is_stable']}")
        
        # Test 3: Get Energy Sources
        print_section("3. ENERGY SOURCES")
        solar = client.get_solar_generation()
        wind = client.get_wind_generation()
        print(f"Solar: {solar['generation_value']:.2f} kW / {solar['capacity']:.2f} kW capacity")
        print(f"Wind: {wind['generation_value']:.2f} kW / {wind['capacity']:.2f} kW capacity")
        
        # Test 4: Battery Status
        print_section("4. BATTERY STATUS")
        battery = client.get_battery_status()
        print(f"SOC: {battery['state_of_charge']:.1f}%")
        print(f"Current Level: {battery['current_level']:.2f} kWh / {battery['capacity']:.2f} kWh")
        print(f"Health: {battery['health']:.1f}%")
        print(f"Status: {battery['status']}")
        
        # Test 5: Run Balancing
        print_section("5. RUN BALANCING ENGINE")
        action = client.run_balancing()
        print(f"Action: {action['action'].upper()}")
        print(f"Reasoning: {action['reasoning']}")
        print(f"Magnitude: {action['magnitude']:.2f} kW")
        print(f"Priority: {action['priority']}/10")
        
        # Test 6: Alerts
        print_section("6. SYSTEM ALERTS")
        alerts = client.get_alerts()
        print(f"Active Alerts: {alerts['stats']['active_alerts']}")
        print(f"  Critical: {alerts['stats']['critical']}")
        print(f"  High: {alerts['stats']['high']}")
        print(f"  Medium: {alerts['stats']['medium']}")
        print(f"  Low: {alerts['stats']['low']}")
        
        if alerts['alerts']:
            print("\nRecent Alerts:")
            for alert in alerts['alerts'][:3]:
                print(f"  [{alert['severity'].upper()}] {alert['type']}: {alert['message']}")
        
        # Test 7: Metrics
        print_section("7. SYSTEM METRICS")
        metrics = client.get_metrics()
        print(f"Grid Frequency: {metrics['grid_frequency']} Hz")
        print(f"Grid Stability: {metrics['grid_stability_score']:.1f}/100")
        print(f"Renewable Energy: {metrics['renewable_percentage']:.1f}%")
        print(f"Load Percentage: {metrics['load_percentage']:.1f}%")
        print(f"Decisions Made: {metrics['decisions_made']}")
        
        # Test 8: Predictions
        print_section("8. GENERATION PREDICTIONS (Next 24 hours)")
        solar_pred = client.predict_solar(24)
        avg_solar = sum(solar_pred['predictions']) / len(solar_pred['predictions'])
        print(f"Average Solar: {avg_solar:.2f} kW")
        print(f"Peak Solar: {max(solar_pred['predictions']):.2f} kW")
        
        # Test 9: Scenario Simulation
        print_section("9. SCENARIO SIMULATION")
        print("Testing: High solar (0.9), Moderate wind (12 m/s), High demand spike (0.3)")
        scenario = client.simulate_scenario(0.9, 12, 0.3)
        print(f"Solar Generation: {scenario['inputs']['solar_generation']:.2f} kW")
        print(f"Wind Generation: {scenario['inputs']['wind_generation']:.2f} kW")
        print(f"Demand: {scenario['inputs']['demand']:.2f} kW")
        print(f"Recommended Action: {scenario['recommended_action']['action'].upper()}")
        print(f"Reasoning: {scenario['recommended_action']['reasoning']}")
        
        if scenario['alerts']:
            print(f"Alerts Triggered: {len(scenario['alerts'])}")
            for alert in scenario['alerts']:
                print(f"  [{alert['severity'].upper()}] {alert['type']}")
        
        print_section("ALL TESTS COMPLETED SUCCESSFULLY ✅")
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to server")
        print("Make sure the server is running: python main.py")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def test_websocket():
    """Test WebSocket connection"""
    print_section("WEBSOCKET TEST")
    
    try:
        ws = websocket.create_connection("ws://localhost:8000/ws")
        print("✅ Connected to WebSocket")
        
        # Receive initial connection message
        message = ws.recv()
        print(f"Received: {message}\n")
        
        # Receive a few updates
        print("Receiving updates for 10 seconds...\n")
        start_time = time.time()
        update_count = 0
        
        while time.time() - start_time < 10:
            try:
                message = ws.recv()
                update_count += 1
                data = json.loads(message)
                print(f"Update #{update_count}: {data['type']}")
                print(f"  Grid Frequency: {data.get('frequency', 'N/A')} Hz")
                print(f"  Stability Score: {data.get('stability_score', 'N/A')}/100\n")
            except websocket.WebSocketTimeoutException:
                break
        
        ws.close()
        print(f"✅ WebSocket test completed ({update_count} updates received)")
        
    except Exception as e:
        print(f"❌ WebSocket error: {str(e)}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  INTELLIGENT ENERGY GRID BALANCER - TEST CLIENT")
    print("="*60)
    
    # Run REST API tests
    test_api()
    
    # Run WebSocket test (optional)
    try:
        input("\nPress Enter to test WebSocket (Ctrl+C to skip)...")
        test_websocket()
    except KeyboardInterrupt:
        print("\nWebSocket test skipped")
