import os, time
from openai import OpenAI

c = OpenAI(api_key=os.environ["GEMINI_API_KEY"],
           base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
           timeout=20, max_retries=0)
for model in ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash",
              "gemini-3.5-flash", "gemini-flash-latest", "gemini-3.1-flash-lite"]:
    t = time.time()
    try:
        r = c.chat.completions.create(model=model, messages=[{"role": "user", "content": "Say hi"}])
        print(f"{model:24} ok    {time.time() - t:5.1f}s  {r.choices[0].message.content!r:.40}")
    except Exception as e:
        print(f"{model:24} FAIL  {time.time() - t:5.1f}s  {type(e).__name__}: {str(e)[:80]}")