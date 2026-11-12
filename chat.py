import uuid

from langgraph.types import Command

from app.agent import graph

cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}  # a fresh claim each run
out = graph.invoke({"message": input("Traveller: ")}, cfg)

while "__interrupt__" in out:
    pending = out["__interrupt__"][0].value
    if "question" in pending:  # the agent needs a missing fact
        answer = input(f"Agent: {pending['question']}\nTraveller: ")
    else:  # OPA wants a person to decide
        print(f"Reviewer needed. Claim: {pending['claim']}")
        print(f"OPA said: {pending['decision']}")
        answer = input("Reviewer verdict: ")
    out = graph.invoke(Command(resume=answer), cfg)

print("Agent:", out["reply"])