import os
from typing import Literal, TypedDict

import instructor
from openai import OpenAI
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt

from app.main import call_opa

MODEL = "gemini-3.1-flash-lite"
llm = instructor.from_openai(
    OpenAI(api_key=os.environ["GEMINI_API_KEY"],
           base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
           timeout=180, max_retries=3),
    mode=instructor.Mode.JSON,
)

class ClaimFacts(BaseModel):
    """Only what the traveller said. Anything they didn't say stays null."""
    disruption: Literal["cancellation", "delay"] | None = None
    distance_km: float | None = Field(None, description="flight distance in km, only if stated")
    departs_eu: bool | None = Field(None, description="the flight left from an EU airport")
    arrives_eu: bool | None = Field(None, description="the flight landed at an EU airport")
    carrier_is_eu: bool | None = Field(None, description="the airline is an EU airline")
    intra_eu: bool | None = Field(None, description="both airports are in the EU")
    notice_days: float | None = Field(None, description="days of notice before a cancellation")
    arrival_delay_h: float | None = Field(None, description="hours late at the final destination")
    extraordinary_claimed: bool | None = Field(
        None, description="the airline blamed extraordinary circumstances, such as weather or a strike")

QUESTIONS = {
    "disruption": "was the flight cancelled or delayed?",
    "distance_km": "roughly how long was the flight, in km?",
    "departs_eu": "did it leave from an airport in the EU?",
    "notice_days": "how many days' notice of the cancellation did you get?",
    "arrival_delay_h": "how many hours late did you arrive?",
}

class State(TypedDict, total=False):
    message: str
    claim: dict
    missing: list[str]
    decision: dict
    reviewer_verdict: str
    reply: str

def missing_facts(claim: dict) -> list[str]:
    need = ["disruption", "distance_km", "departs_eu"]
    if claim.get("disruption") == "cancellation":
        need.append("notice_days")
    if claim.get("disruption") == "delay":
        need.append("arrival_delay_h")
    return [f for f in need if f not in claim]

def gather(state: State) -> State:
    if "message" not in state:  # facts passed in directly, as in the first test
        return {"claim": state["claim"], "missing": []}
    facts = llm.chat.completions.create(
        model=MODEL,
        response_model=ClaimFacts,
        max_retries=2,
        messages=[{"role": "system", "content": "Extract the facts of an EU261 flight-compensation "
                   "claim from the traveller's words. Use only what they say; leave the rest null."},
                  {"role": "user", "content": state["message"]}],
    )
    claim = facts.model_dump(exclude_none=True)
    return {"claim": claim, "missing": missing_facts(claim)}

def ask(state: State) -> State:
    answer = interrupt({"question": " ".join(QUESTIONS[f] for f in state["missing"])})
    return {"message": state["message"] + "\n" + answer}

def after_gather(state: State) -> str:
    return "ask" if state["missing"] else "decide"

def decide(state: State) -> State:
    return {"decision": call_opa(state["claim"])}

def human_review(state: State) -> State:
    verdict = interrupt({"claim": state["claim"], "decision": state["decision"]})
    return {"reviewer_verdict": verdict}

def respond(state: State) -> State:
    if state.get("reviewer_verdict"):
        return {"reply": f"Reviewed by a person: {state['reviewer_verdict']}"}
    d = state["decision"]
    reply = f"Eligible: {d['eligible']}, EUR {d['amount_eur']} ({', '.join(d['citations'])})"
    if d["eligible"] and "extraordinary_claimed" not in state["claim"]:
        reply += ", unless the airline proves extraordinary circumstances (Art. 5(3))"
    return {"reply": reply}

def route(state: State) -> str:
    return "human_review" if state["decision"].get("needs_human_review") else "respond"

builder = StateGraph(State)
builder.add_node("gather", gather)
builder.add_node("ask", ask)
builder.add_node("decide", decide)
builder.add_node("human_review", human_review)
builder.add_node("respond", respond)
builder.add_edge(START, "gather")
builder.add_conditional_edges("gather", after_gather, ["ask", "decide"])
builder.add_edge("ask", "gather")
builder.add_conditional_edges("decide", route, ["human_review", "respond"])
builder.add_edge("human_review", "respond")
builder.add_edge("respond", END)
graph = builder.compile(checkpointer=InMemorySaver())