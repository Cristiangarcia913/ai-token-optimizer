---
source_file: service_auth.py
converter: CodeConverter
raw_tokens: 402
optimized_tokens: 241
reduction: 40.05%
---

```python
import hmac
import hashlib
import time
from typing import Optional, Dict, Any

def verify_jwt_token(token: str, secret_key: str) -> bool:
    if not token or not secret_key:
        return False

    parts = token.split(".")
    if len(parts) != 3:
        return False

    header, payload, signature = parts
    expected = hmac.new(
        secret_key.encode("utf-8"),
        f"{header}.{payload}".encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)

class SecuritySessionManager:
    def __init__(self, ttl_seconds: int = 3600):
        self.ttl = ttl_seconds
        self.sessions: Dict[str, float] = {}

    def register_session(self, user_id: str) -> None:
        self.sessions[user_id] = time.time()

    def is_valid(self, user_id: str) -> bool:
        created = self.sessions.get(user_id)
        if not created:
            return False
        return (time.time() - created) < self.ttl
```