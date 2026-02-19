#!/usr/bin/env python3
"""Check Gemini daily usage symptoms and current quota state.

What this script can do:
1) Parse local app logs (logs/api_requests.log) and summarize GEMINI usage
   for the last 24h and for "today" (local time).
2) Optionally probe the Gemini API with a tiny request to see if the key/model
   is currently blocked by quota/daily limits.

Usage:
  python scripts/check_gemini_daily_limits.py
  python scripts/check_gemini_daily_limits.py --log-file logs/api_requests.log
  python scripts/check_gemini_daily_limits.py --probe
  python scripts/check_gemini_daily_limits.py --probe --model gemini-2.5-pro

Env:
  GOOGLE_API_KEY or GEMINI_API_KEY
  GEMINI_MODEL (optional)
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from collections import Counter, defaultdict


_QUOTA_TERMS = [
    "resource_exhausted",
    "quota",
    "daily",
    "limit",
    "rate limit",
    "too many requests",
    "429",
]


def _is_quota_error_message(message: str) -> bool:
    msg = (message or "").lower()
    return any(t in msg for t in _QUOTA_TERMS)


def _parse_log_line(line: str):
    """Parse a line from logs/api_requests.log written by pyFunctions/api_logging.py.

    Example:
      [2026-02-19 12:34:56] [GEMINI] gemini_generate_content - FAILED - Prompt: 123 chars
        ERROR: ...
        FALLBACK_REASON: quota_exhausted

    Returns dict or None.
    """
    m = re.match(r"^\[(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+(?P<rest>.*)$", line.strip())
    if not m:
        return None

    try:
        ts = dt.datetime.strptime(m.group("ts"), "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

    rest = m.group("rest")

    # Optional [SOURCE] prefix
    source = None
    if rest.startswith("["):
        m2 = re.match(r"^\[(?P<src>[^\]]+)\]\s+(?P<tail>.*)$", rest)
        if m2:
            source = m2.group("src")
            rest = m2.group("tail")

    # Function name then status
    m3 = re.match(r"^(?P<fn>[^-]+?)\s+-\s+(?P<status>SUCCESS|FAILED)\s+-\s+Prompt:\s+(?P<prompt_len>\d+)\s+chars(?:,\s+Response:\s+(?P<resp_len>\d+)\s+chars)?(?:,\s+Model:\s+(?P<model>.+))?$", rest)
    if not m3:
        return {
            "timestamp": ts,
            "source": source,
            "raw": line.strip(),
        }

    return {
        "timestamp": ts,
        "source": source,
        "function": m3.group("fn").strip(),
        "status": m3.group("status"),
        "prompt_len": int(m3.group("prompt_len")),
        "resp_len": int(m3.group("resp_len")) if m3.group("resp_len") else 0,
        "model": (m3.group("model") or "").strip() or None,
    }


def summarize_log(log_file: str) -> int:
    if not os.path.exists(log_file):
        print(f"Log file not found: {log_file}")
        return 2

    now = dt.datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_24h = now - dt.timedelta(hours=24)

    entries_today = []
    entries_24h = []

    quota_lines_today = 0
    quota_lines_24h = 0

    source_counts_today = Counter()
    source_counts_24h = Counter()

    fn_counts_today = Counter()
    fn_counts_24h = Counter()

    model_counts_today = Counter()
    model_counts_24h = Counter()

    # We also scan raw lines for quota terms, because multi-line error messages
    # include the important signal on separate lines.
    current_ts = None

    with open(log_file, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            parsed = _parse_log_line(raw)
            if parsed and "timestamp" in parsed:
                current_ts = parsed["timestamp"]
                if current_ts >= today_start:
                    entries_today.append(parsed)
                    source_counts_today.update([parsed.get("source") or "UNKNOWN"])
                    fn_counts_today.update([parsed.get("function") or "UNKNOWN"])
                    if parsed.get("model"):
                        model_counts_today.update([parsed["model"]])
                if current_ts >= last_24h:
                    entries_24h.append(parsed)
                    source_counts_24h.update([parsed.get("source") or "UNKNOWN"])
                    fn_counts_24h.update([parsed.get("function") or "UNKNOWN"])
                    if parsed.get("model"):
                        model_counts_24h.update([parsed["model"]])
            else:
                # continuation/error line
                if current_ts is None:
                    continue
                if _is_quota_error_message(raw):
                    if current_ts >= today_start:
                        quota_lines_today += 1
                    if current_ts >= last_24h:
                        quota_lines_24h += 1

    def _print_top(counter: Counter, title: str, limit: int = 6):
        print(title)
        for k, v in counter.most_common(limit):
            print(f"  - {k}: {v}")
        if not counter:
            print("  (none)")

    print(f"Log summary: {log_file}")
    print(f"Now: {now:%Y-%m-%d %H:%M:%S}")
    print()

    print(f"TODAY entries: {len(entries_today)}")
    print(f"TODAY quota-related error lines: {quota_lines_today}")
    _print_top(source_counts_today, "TODAY by source:")
    _print_top(fn_counts_today, "TODAY by function:")
    _print_top(model_counts_today, "TODAY by model:")

    print()

    print(f"LAST 24H entries: {len(entries_24h)}")
    print(f"LAST 24H quota-related error lines: {quota_lines_24h}")
    _print_top(source_counts_24h, "LAST 24H by source:")
    _print_top(fn_counts_24h, "LAST 24H by function:")
    _print_top(model_counts_24h, "LAST 24H by model:")

    return 0


def probe_gemini(model: str | None) -> int:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Missing GOOGLE_API_KEY (or GEMINI_API_KEY) in environment.")
        return 2

    model_name = (model or os.getenv("GEMINI_MODEL") or "gemini-2.5-pro").strip()
    if model_name.startswith("models/"):
        model_name = model_name[len("models/"):]

    try:
        import google.generativeai as genai  # type: ignore
    except Exception:
        print("google-generativeai is not installed. Install with: pip install google-generativeai")
        return 2

    genai.configure(api_key=api_key)  # type: ignore[attr-defined]

    try:
        m = genai.GenerativeModel(model_name)  # type: ignore[attr-defined]
        # Tiny prompt to keep cost low
        resp = m.generate_content("Reply with the single word: OK")
        text = getattr(resp, "text", "") or ""
        print(f"Probe OK with model={model_name}. Response: {text.strip()[:80]}")
        return 0
    except Exception as e:
        msg = str(e)
        if _is_quota_error_message(msg):
            print(f"Probe hit quota/daily limit for model={model_name}: {msg}")
            return 3
        print(f"Probe failed for model={model_name}: {msg}")
        return 4


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Check Gemini daily limits via local logs and optional API probe")
    p.add_argument("--log-file", default=os.path.join("logs", "api_requests.log"), help="Path to api_requests.log")
    p.add_argument("--probe", action="store_true", help="Make a tiny Gemini request to detect quota blocks")
    p.add_argument("--model", help="Model name for --probe (default: GEMINI_MODEL or gemini-2.5-pro)")
    args = p.parse_args(argv)

    rc = summarize_log(args.log_file)
    if args.probe:
        print()
        probe_rc = probe_gemini(args.model)
        # Preserve nonzero exit codes, but still let logs summarize first.
        return probe_rc if probe_rc != 0 else rc

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
