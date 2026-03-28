"""
AI Grid Balancer Service
Uses GitHub Models API (free, OpenAI-compatible) to make intelligent
grid balancing decisions based on live grid state.
"""

import json
import os

from openai import OpenAI

# GitHub Models API — free inference using a GitHub PAT with models:read scope
GITHUB_MODELS_ENDPOINT = "https://models.github.ai/inference"
_client = None


def _strip_markdown_fence(content: str) -> str:
    text = (content or "").strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if len(lines) < 3:
        return text
    if not lines[-1].strip().startswith("```"):
        return text
    return "\n".join(lines[1:-1]).strip()


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError(
                "GITHUB_TOKEN environment variable is not set. "
                "Create a GitHub PAT with models:read scope and add it to your .env file."
            )
        _client = OpenAI(
            base_url=GITHUB_MODELS_ENDPOINT,
            api_key=github_token,
        )
    return _client


def run_ai_balancer(grid_state: dict) -> dict:
    """
    Takes current grid state and returns AI-generated balancing decision.

    grid_state keys:
      - solar_kw: float
      - wind_kw: float
      - total_supply_kw: float
      - demand_kw: float
      - battery_percentage: float
      - battery_level_kwh: float
      - battery_capacity_kwh: float
      - hour: int (0-23)
      - grid_status: str (SURPLUS / DEFICIT / BALANCED)
      - imbalance_threshold: float (%)
    """
    client = _get_client()

    system_prompt = """You are an intelligent energy grid management AI.
Your job is to analyze real-time grid data and return a precise balancing decision as JSON.

You must respond ONLY with valid JSON — no markdown, no explanation outside the JSON.

The JSON must have this exact structure:
{
  "action": "one of: STORE_EXCESS | DISCHARGE_BATTERY | SHED_LOAD | REDUCE_LOAD | BALANCED | EMERGENCY",
  "confidence": <float 0.0-1.0>,
  "battery_instruction": {
    "operation": "one of: charge | discharge | hold",
    "target_percentage": <float 0-100>,
    "rate_kw": <float, suggested charge/discharge rate>
  },
  "demand_response": {
    "active": <boolean>,
    "zones_affected": <list of strings, e.g. ["Zone A", "Zone B"]>,
    "reduction_percentage": <float 0-100>,
    "message_to_households": <string, a plain-language message to send to households>
  },
  "grid_stability_score": <float 0.0-1.0>,
  "reasoning": <string, 2-3 sentences explaining the decision>,
  "forecast_30min": <string, brief prediction of grid state in 30 minutes>
}"""

    user_message = f"""Current grid state at hour {grid_state.get('hour', 'unknown')}:

- Solar generation: {grid_state.get('solar_kw', 0):.1f} kW
- Wind generation: {grid_state.get('wind_kw', 0):.1f} kW
- Total supply: {grid_state.get('total_supply_kw', 0):.1f} kW
- Current demand: {grid_state.get('demand_kw', 0):.1f} kW
- Net delta: {grid_state.get('total_supply_kw', 0) - grid_state.get('demand_kw', 0):.1f} kW
- Battery level: {grid_state.get('battery_percentage', 0):.1f}% ({grid_state.get('battery_level_kwh', 0):.0f} / {grid_state.get('battery_capacity_kwh', 1000):.0f} kWh)
- Grid status: {grid_state.get('grid_status', 'UNKNOWN')}
- Imbalance threshold: {grid_state.get('imbalance_threshold', 20)}%

Analyze this situation and provide your balancing decision as JSON."""

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",  # free tier, fast, good enough for this task
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,  # low temperature for consistent, deterministic decisions
        max_tokens=600,
    )

    raw = _strip_markdown_fence(response.choices[0].message.content or "")

    decision = json.loads(raw)

    # Attach the original grid state snapshot for the frontend to display
    decision["grid_snapshot"] = {
        "solar_kw": grid_state.get("solar_kw", 0),
        "wind_kw": grid_state.get("wind_kw", 0),
        "total_supply_kw": grid_state.get("total_supply_kw", 0),
        "demand_kw": grid_state.get("demand_kw", 0),
        "battery_percentage": grid_state.get("battery_percentage", 0),
        "hour": grid_state.get("hour", 0),
    }

    return decision
