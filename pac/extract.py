import json
import instructor
from openai import OpenAI
from pac.schema import Extraction, grounded
from pac.split import split_articles

client = instructor.from_openai(OpenAI())
SYSTEM = (
    "You extract normative rules from EU legislation: one rule per obligation, "
    "permission or prohibition. Copy the exact source sentence into quote. When a rule "
    "makes an exception to another provision, set exception_to to that provision. "
    "Use only what the text states. Set needs_interpretation for open terms."
)

def extract(article_id: str, text: str) -> Extraction:
    return client.chat.completions.create(
        model="gpt-4.1-mini",  # any model with structured output
        response_model=Extraction,
        max_retries=2,  # re-asks with the validation error
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": f"{article_id}\n\n{text}"}],
    )

articles = split_articles(open("data/eu261.txt").read())
rules, ungrounded = [], []
for art_id, text in articles.items():
    for n, rule in enumerate(extract(art_id, text).rules, start=1):
        record = {"rule_id": f"{art_id}#{n}", **rule.model_dump(mode="json")}  # IDs from code
        (rules if grounded(rule, text) else ungrounded).append(record)
json.dump({"rules": rules, "ungrounded": ungrounded}, open("rules.json", "w"), indent=2)