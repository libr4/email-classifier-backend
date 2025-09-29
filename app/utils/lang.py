import re

def detect_language(_text: str) -> str:
    return "pt" if re.search(r"[áéíóúãõç]", _text, re.I) else "en" if re.search(r"[a-z]", _text, re.I) else "unknown"
