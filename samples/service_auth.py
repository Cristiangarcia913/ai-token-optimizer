# Copyright (c) 2024-2025 Acme Software Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# System Identification: AUTH-SERVICE-SEC-092
# Module: auth_token_provider.py
# Author: Architecture Security Guild

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
