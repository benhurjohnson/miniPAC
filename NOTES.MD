# Build notes: mini policy as code on EU261

Prototype built this week with Claude Code. Extraction model: gemini-3.1-flash-lite
through Google's OpenAI-compatible endpoint, with Instructor for structured output.
Policy written in Rego with AI assistance and checked against the regulation.

## Results
- Extraction: 68 rules from 19 articles. 54 passed the quote check, 14 were rejected,
  0 failed.
- Policy: fill in (expect: all 7 opa tests pass). Where the text runs out: delay
  compensation comes from case law (Sturgeon); extraordinary circumstances go to a
  person; the carrier's option to halve is flagged, not applied. A flight of exactly
  3,500 km counts as medium.
- API: fill in (expect: /decide returns EUR 250 for the short-flight example).
- Agent: fill in (expect: an extraordinary-circumstances claim pauses for a person,
  then resumes).
- Eval: skipped for time. The findings below come from reviewing the output by hand.

## What the extraction got wrong
1. The quote check rejected faithful quotes. 13 of the 14 rejections quoted the text
   accurately but not word for word: the model joined a list's lead-in to item (b) or
   (c), stitched fragments with "...", or changed spacing and quote marks. Only item (a)
   directly follows its lead-in, so EUR 250 passed while EUR 400 and EUR 600 (Art. 7(1)(b),
   (c)) and arrivals on EU carriers (Art. 3(1)(b)) were rejected. A policy built only from
   the passing rules would have dropped two of the three compensation amounts.
2. A whole exception disappeared. The "unless" clause of Art. 5(1)(c), the notice and
   re-routing exemptions, was not extracted, so the rule as extracted says every
   cancellation pays. Art. 3(2) (confirmed reservation, on-time check-in) is also missing.
3. A logic error the quote check can't see. Art. 5(3), "shall not be obliged to pay",
   was labelled a prohibition on paying. Not obliged to pay means permitted not to pay;
   it does not mean must not pay. The quote was perfect, so only review catches this.
4. Legal language and schema gaps. Art. 16(2) was marked an exception to Art. 12, but
   "without prejudice to Article 12" means it doesn't limit Art. 12 at all. Scope
   provisions were forced into obligations because the schema has no type for scope or
   definitions. needs_interpretation was set on 30 of 68 rules, too many to send to people.

## How I handled it
- Left rules.json unedited, as the record of what the model produced.
- Wrote the policy from the regulation text, using rules.json as a checklist, so the
  policy covers what the extraction missed. Known gap: Art. 3(2).

## What broke during the build, and what I changed

### 1. The pasted text lost its structure
- What happened: pasting the Regulation from legislation.gov.uk merged each article
  number into its title ("Article 1Subject"), so the split found no articles.
- What I changed: a regex that puts the line break back where "Article N" runs into
  a capital letter, and a grep check that all 19 headings sit on their own lines.
- Lesson: ingestion is where structure breaks first. Check the structure before
  extracting; in production, use the source's structured format (XML), not copy-paste.

### 2. Swapping providers was a config change
- What happened: OpenAI has no free tier, so I moved to Gemini.
- What I changed: only the base URL, key and model name. Instructor and the schema
  stayed the same.
- Lesson: an OpenAI-compatible interface, or an LLM gateway, keeps the provider swappable.

### 3. Model availability is an operational risk
- What happened: gemini-2.5-flash was retired for new users (404), gemini-3.8-flash
  was overloaded (503), and 3.5–3.7 Flash timed out after 20 s. Only
  gemini-3.1-flash-lite answered, in about 10 s.
- What I changed: probed the models with a short script and used the one that answered.
- Lesson: measure availability and latency rather than assume them; keep a fallback model.

### 4. One timeout crashed the whole run
- What happened: a single timeout crashed the run before anything was saved.
- What I changed: a 180 s timeout, SDK retries (timeouts, 429s, 5xx), a try/except
  around each article, and a cache of each article's result, so a rerun only redoes
  failures.
- Lesson: pipeline steps should be idempotent and retryable. In production, key the
  cache on a hash of the text, prompt and model.

## What I'd do next
- Split list items (a), (b), (c) in code before extraction, which fixes the stitched quotes.
- Accept quotes made of verbatim fragments in order, rather than one exact string.
- Add scope and definition types to the schema, and define needs_interpretation tightly.
- Build a gold set for Articles 3 and 5–8 before changing the prompt, then measure
  precision and recall on every prompt change in CI, and use it to compare models.
- Fetch the official XML instead of copy-pasting the text.