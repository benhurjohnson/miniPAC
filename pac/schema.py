from enum import Enum
from pydantic import BaseModel, Field

class Modality(str, Enum):
    obligation = "obligation"
    permission = "permission"
    prohibition = "prohibition"

class Condition(BaseModel):
    variable: str = Field(description="snake_case fact, e.g. distance_km")
    operator: str = Field(description="one of ==, !=, <, <=, >, >=")
    value: float | bool | str

class Rule(BaseModel):  # rule IDs are assigned in code, not by the model
    source: str = Field(description="article and paragraph, e.g. 'Art. 5(1)(c)(ii)'")
    quote: str = Field(description="the exact sentence the rule comes from")
    modality: Modality
    bearer: str = Field(description="who it binds, e.g. operating air carrier")
    action: str
    conditions: list[Condition]
    exception_to: str | None = Field(
        default=None, description="source of the provision this rule defeats, e.g. 'Art. 5(1)(c)'")
    needs_interpretation: bool = Field(description="true for open terms such as 'extraordinary'")

class Extraction(BaseModel):
    rules: list[Rule]

def grounded(rule: Rule, source_text: str) -> bool:
    """Deterministic provenance check: the quote must appear in the source."""
    norm = lambda s: " ".join(s.split())
    return norm(rule.quote) in norm(source_text)