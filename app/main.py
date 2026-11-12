from typing import Literal

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

OPA_URL = "http://localhost:8181/v1/data/eu261/decision"
app = FastAPI()

class Claim(BaseModel):
    disruption: Literal["cancellation", "delay"]  # anything else is a 422, not a silent "no"
    distance_km: float
    departs_eu: bool
    arrives_eu: bool = False
    carrier_is_eu: bool = False
    intra_eu: bool = False
    notice_days: float | None = None
    rerouted: bool = False
    reroute_depart_early_h: float | None = None
    reroute_arrive_late_h: float | None = None
    arrival_delay_h: float | None = None
    extraordinary_claimed: bool = False

def call_opa(claim: dict) -> dict:
    try:
        r = httpx.post(OPA_URL, json={"input": claim}, timeout=2.0)
        r.raise_for_status()
        return r.json()["result"]
    except (httpx.HTTPError, KeyError):
        # Fail closed: no decision means no payout, and a person looks at it
        return {"eligible": False, "amount_eur": 0, "carrier_may_halve": False,
                "needs_human_review": True, "citations": [],
                "error": "policy engine unavailable"}

@app.post("/decide")
def decide(claim: Claim) -> dict:
    return call_opa(claim.model_dump(exclude_none=True))