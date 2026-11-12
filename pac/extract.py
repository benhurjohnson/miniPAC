import json, os, time
from pathlib import Path

import instructor
from openai import OpenAI

from pac.schema import Extraction, grounded
from pac.split import split_articles

MODEL = "gemini-3.1-flash-lite"  # an id from your models list
CACHE = Path("data/extracted") / MODEL
CACHE.mkdir(parents=True, exist_ok=True)

client = instructor.from_openai(
    OpenAI(
        api_key=os.environ["GEMINI_API_KEY"],
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        timeout=180,    # seconds per request, instead of the SDK's long default
        max_retries=3,  # the SDK retries timeouts, 429s and 5xx, with backoff
    ),
    mode=instructor.Mode.JSON,
)
SYSTEM = (
    "You extract normative rules from EU legislation: one rule per obligation, "
    "permission or prohibition. Copy the exact source sentence into quote. When a rule "
    "makes an exception to another provision, set exception_to to that provision. "
    "Use only what the text states. Set needs_interpretation for open terms."
)

def extract(article_id: str, text: str) -> Extraction:
    return client.chat.completions.create(
        model=MODEL,
        response_model=Extraction,
        max_retries=2,  # Instructor re-asks on validation errors
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": f"{article_id}\n\n{text}"}],
    )

articles = split_articles(open("data/eu261.txt").read())
rules, ungrounded, failed = [], [], []
for art_id, text in articles.items():
    cached = CACHE / f"{art_id.replace('. ', '_')}.json"  # e.g. Art_5.json
    if cached.exists():
        extraction = Extraction.model_validate_json(cached.read_text())
    else:
        try:
            extraction = extract(art_id, text)
        except Exception as e:  # one bad article shouldn't kill the run
            print(f"{art_id}: failed ({type(e).__name__}); rerun to retry")
            failed.append(art_id)
            continue
        cached.write_text(extraction.model_dump_json(indent=2))
        time.sleep(5)  # stay under the free tier's requests-per-minute limit
    for n, rule in enumerate(extraction.rules, start=1):
        print(f"{art_id}: {len(extraction.rules)} rules")
        record = {**rule.model_dump(mode="json"), "rule_id": f"{art_id}#{n}"}  # IDs from code
        (rules if grounded(rule, text) else ungrounded).append(record)

json.dump({"rules": rules, "ungrounded": ungrounded, "failed": failed},
          open("rules.json", "w"), indent=2)
print(f"{len(rules)} grounded, {len(ungrounded)} ungrounded, {len(failed)} failed")