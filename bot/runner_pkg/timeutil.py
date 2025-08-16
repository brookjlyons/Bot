# bot/runner_pkg/timeutil.py
"""
Time utilities for runner_pkg.

Purpose
- Provide a single, consistent source of truth for how we write and read
  timestamps in the pending state (postedAt / expires math).

Design
- Write: ISO-8601 strings in UTC (e.g., "2025-08-16T05:00:00+00:00").
- Read: tolerate legacy epoch floats/ints and various ISO forms (with/without 'Z').
- Never raise: invalid inputs return 0.0 to ensure fail-safe expiry math.

This file contains no side effects and no external I/O.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

__all__ = ["now_iso", "iso_to_epoch"]


def now_iso() -> str:
    """
    Return the current UTC time as an ISO-8601 string.

    Example:
        "2025-08-16T05:00:00.123456+00:00"
    """
    # Use timezone-aware UTC; Discord/Gist/state all operate fine with "+00:00"
    return datetime.now(timezone.utc).isoformat()


def iso_to_epoch(value: Any) -> float:
    """
    Convert an ISO-8601 timestamp (or legacy epoch) to epoch seconds (float).

    Accepts:
      - float/int epoch seconds (legacy persisted values) → returned as float
      - ISO strings with or without trailing 'Z' (treated as UTC)
      - ISO strings with timezone offsets (e.g., "+00:00", "+12:00")
      - Naive datetimes (no offset) → treated as UTC

    Fail-safe:
      - On invalid/empty values, returns 0.0 (caller should handle as "very old").

    Args:
        value: ISO string | float | int | any

    Returns:
        float: epoch seconds
    """
    # Legacy path: numeric epoch already
    if isinstance(value, (int, float)):
        try:
            return float(value)
        except Exception:
            return 0.0

    if value is None:
        return 0.0

    s = str(value).strip()
    if not s:
        return 0.0

    try:
        # Tolerate trailing 'Z' by normalizing to explicit UTC offset
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"

        dt = datetime.fromisoformat(s)

        # If the parsed datetime is naive (no tzinfo), assume UTC per our state contract
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.timestamp()
    except Exception:
        # Final guard: never raise to caller code
        return 0.0
