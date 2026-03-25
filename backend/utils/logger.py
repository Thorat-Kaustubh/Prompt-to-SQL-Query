import sys
import json
import uuid
import time
from typing import Any, Dict, Optional
from loguru import logger
from contextvars import ContextVar

# Context for Request-based logging
_request_id_ctx = ContextVar("request_id", default="INTERNAL")

def set_request_id(request_id: str):
    return _request_id_ctx.set(request_id)

def get_request_id() -> str:
    return _request_id_ctx.get()

# Sensitive Keys to redact
SENSITIVE_KEYS = {"jwt_token", "password", "secret", "apikey", "token"}

def redact_sensitive(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: ("***REDACTED***" if k.lower() in SENSITIVE_KEYS else redact_sensitive(v)) for k, v in data.items()}
    elif isinstance(data, list):
        return [redact_sensitive(i) for i in data]
    return data

def json_serializer(record):
    """
    Standardized System Log Format
    """
    subset = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "request_id": get_request_id(),
        "module": record["name"],
        "message": record["message"],
        "context": redact_sensitive(record["extra"]),
    }
    # Add exception info if present
    if record["exception"]:
        subset["exception"] = record["exception"].format()
        
    return json.dumps(subset)

def setup_standard_logging(level="INFO", log_file="system_observability.log"):
    # Remove default handler
    logger.remove()
    
    # Console JSON Output
    logger.add(
        sys.stdout, 
        format=lambda r: "{message}", 
        level=level, 
        serialize=True, 
        enqueue=True
    )
    
    # File JSON Output
    logger.add(
        log_file, 
        format=lambda r: "{message}", 
        level=level, 
        serialize=True, 
        rotation="100 MB",
        enqueue=True
    )
    
    # Intercept loguru's native serialization with our custom subset if needed
    # But loguru's `serialize=True` is already quite good. 
    # For THE exact format requested by the user, we will create a dedicated "StructuredLogger" helper.

class StructuredLogger:
    @staticmethod
    def log_event(event_type: str, data: Dict[str, Any]):
        """
        Final Standardized Format as per PRD:
        {
          "timestamp": "...",
          "user_id": "...",
          "query": "...",
          "sql": "...",
          "execution_time_ms": "...",
          "cache_hit": true/false,
          "status": "SUCCESS | FAILED",
          "error": null | "error message",
          "event_type": "..."
        }
        """
        payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "request_id": get_request_id(),
            "event_type": event_type,
            **redact_sensitive(data)
        }
        
        # Use loguru to record it
        logger.bind(type="structured", **payload).info(f"EVENT_{event_type}")

# Initialize logging on import
setup_standard_logging()
