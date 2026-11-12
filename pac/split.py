import re

def split_articles(text: str) -> dict[str, str]:
    parts = re.split(r"(?m)^Article (\d+)\s*$", text)
    return {f"Art. {n}": body.strip() for n, body in zip(parts[1::2], parts[2::2])}