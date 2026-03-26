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

import logging

class InterceptHandler(logging.Handler):
    """
    SECURITY & OPS: Intercept standard logging to unify under loguru.
    """
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_standard_logging(level="INFO", log_file="system_observability.log"):
    # Clear any existing handlers
    logger.remove()
    
    # 🖥️ CONSOLE: Human-Readable & Colored
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{extra[request_id]}</cyan> - "
        "<b>{message}</b>"
    )
    
    def filter_requests(record):
        if "request_id" not in record["extra"]:
            record["extra"]["request_id"] = get_request_id()
        return True

    logger.add(
        sys.stdout,
        format=console_format,
        level=level,
        colorize=True,
        enqueue=True,
        filter=filter_requests
    )
    
    # 💾 FILE: Structured JSON
    logger.add(
        log_file,
        format="{message}",
        level=level,
        serialize=True,
        rotation="100 MB",
        enqueue=True
    )
    
    # 🔗 INTERCEPT: Route all Uvicorn/App logs into Loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for _name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        _logger = logging.getLogger(_name)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False

    logger.info("\n" + "="*50 + "\n🚀 AI ASSISTANT BACKEND: STANDBY\n" + "="*50)
    logger.info("Logging: Unified & Hardened (Uvicorn Intercept Active).")

class StructuredLogger:
    @staticmethod
    def log_event(event_type: str, data: Dict[str, Any]):
        """
        Record a structured event for audit trail.
        """
        payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "request_id": get_request_id(),
            "event_type": event_type,
            **redact_sensitive(data)
        }
        
        # We bind the structured data to the record
        logger.bind(**payload).info(f"📊 EVENT_{event_type}: {json.dumps(redact_sensitive(data))}")

# Initialize logging on import
setup_standard_logging()
