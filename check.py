import os, time
from openai import OpenAI
t=time.time()
c = OpenAI(api_key=os.environ["GEMINI_API_KEY"],
           base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
           timeout=30)
print([m.id for m in c.models.list() if "flash" in m.id])
r = c.chat.completions.create(model="gemini-3.8-flash", reasoning_effort="low",
                              messages=[{"role": "user", "content": "Say hi"}])
print(r.choices[0].message.content, f"{time.time() - t:.1f}s")