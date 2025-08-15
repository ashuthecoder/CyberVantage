#!/usr/bin/env python3
"""
Gemini AI Diagnostic Script (Refactored + Fatal Summary Fix)

(Shortened header for brevity. See previous version for full description.)
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import platform
import sys
import time
import traceback
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

# ---------------------------
# Dotenv auto-load
# ---------------------------
def _load_dotenv_if_available() -> Optional[str]:
    try:
        from dotenv import load_dotenv, find_dotenv  # type: ignore
    except Exception:
        return None
    found = find_dotenv()
    if found:
        load_dotenv(found)
        return found
    if Path(".env").exists():
        load_dotenv(".env")
        return str(Path(".env").resolve())
    return None

DOTENV_PATH = _load_dotenv_if_available()

# ---------------------------
# Library import
# ---------------------------
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    LIB_IMPORTED = True
    GENAI_VERSION = getattr(genai, "__version__", "UNKNOWN")
except Exception as e:
    LIB_IMPORTED = False
    GENAI_VERSION = "UNAVAILABLE"
    IMPORT_ERROR = str(e)

# Exit codes
EXIT_SUCCESS = 0
EXIT_PARTIAL = 2
EXIT_FATAL = 3

COLOR_ENABLED = sys.stdout.isatty()
try:
    if platform.system().lower().startswith("win"):
        pass
except Exception:
    COLOR_ENABLED = False

def _c(code: str) -> str:
    if not COLOR_ENABLED:
        return ""
    return code

COLOR = {
    "reset": _c("\033[0m"),
    "green": _c("\033[32m"),
    "yellow": _c("\033[33m"),
    "red": _c("\033[31m"),
    "blue": _c("\033[34m"),
    "cyan": _c("\033[36m"),
    "bold": _c("\033[1m"),
}

DEFAULT_PROMPTS: List[str] = [
    "Return ONLY this exact JSON: {\"diagnostic\": true, \"message\": \"hello\"}",
    ("You are generating an EMAIL SIMULATION for security awareness training. "
     "Produce EITHER a legitimate business email OR a suspicious email. "
     "Educational only. Output JSON with keys: sender, subject, body, is_spam."),
    ("Generate a SIMULATED phishing-style training email (educational) OR a legitimate email; "
     "DO NOT facilitate crime. Output plain JSON: {\"sender\":\"...\",\"subject\":\"...\","
     "\"body\":\"...\",\"is_spam\":true/false}.")
]

MODEL_PRIORITY = [
    "models/gemini-2.5-pro",
    "models/gemini-2.5-pro-latest",
    "models/gemini-2.5-pro-exp",
    "gemini-2.5-pro",
    "models/gemini-1.5-pro",
    "gemini-1.5-pro",
    "models/gemini-1.5-flash",
    "gemini-1.5-flash",
]

@dataclass
class PromptResult:
    prompt_index: int
    prompt_snippet: str
    model_name: str
    success: bool
    blocked: bool
    error: Optional[str]
    finish_reasons: List[str]
    candidate_count: int
    text_parts_total: int
    extracted_text_preview: Optional[str]
    safety_summary: List[Dict[str, Any]]
    latency_seconds: float

@dataclass
class DiagnosticReport:
    environment: Dict[str, Any]
    available_models: List[str]
    selected_model: Optional[str]
    loop_count: int
    results: List[PromptResult]
    summary: Dict[str, Any]

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Gemini Model Diagnostic (Refactored)")
    p.add_argument("--model", help="Explicit model name to test")
    p.add_argument("--list-models", action="store_true", help="List available models and exit")
    p.add_argument("--loops", type=int, default=1, help="Repeat each prompt N times")
    p.add_argument("--prompts-file", help="File with additional prompts (one per line)")
    p.add_argument("--json-out", help="Write full JSON report to this file")
    p.add_argument("--verbose", action="store_true", help="Verbose logging to stderr")
    p.add_argument("--safe-only", action="store_true", help="Only run the first default prompt")
    p.add_argument("--max-chars-preview", type=int, default=300, help="Max chars preview stored")
    p.add_argument("--show-prompts", action="store_true", help="Print prompts before running")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI color output")
    return p.parse_args(argv)

def vlog(verbose: bool, msg: str) -> None:
    if verbose:
        sys.stderr.write(msg + "\n")

def environment_info() -> Dict[str, Any]:
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "google_api_key_present": bool(os.getenv("GOOGLE_API_KEY")),
        "package_version": GENAI_VERSION,
        "library_imported": LIB_IMPORTED,
        "import_error": IMPORT_ERROR if not LIB_IMPORTED else None,
        "dotenv_loaded": DOTENV_PATH,
        "cwd": str(Path.cwd()),
    }

def configure_api_key() -> None:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)

def list_generation_models(verbose: bool) -> List[str]:
    names: List[str] = []
    for m in genai.list_models():
        if "generateContent" in getattr(m, "supported_generation_methods", []):
            names.append(m.name)
    vlog(verbose, f"[MODELS] Found {len(names)} generation-capable models.")
    for n in names:
        vlog(verbose, f"[MODEL] {n}")
    return names

def select_model(explicit: Optional[str], available: List[str], verbose: bool) -> str:
    if explicit:
        if explicit in available:
            vlog(verbose, f"[MODEL_PICK] Using explicit: {explicit}")
            return explicit
        if not explicit.startswith("models/"):
            prefixed = "models/" + explicit
            if prefixed in available:
                vlog(verbose, f"[MODEL_PICK] Resolved alias to: {prefixed}")
                return prefixed
        raise RuntimeError(f"Requested model '{explicit}' not available.")
    for m in MODEL_PRIORITY:
        if m in available:
            vlog(verbose, f"[MODEL_PICK] Auto-selected: {m}")
            return m
    if not available:
        raise RuntimeError("No generation-capable models returned.")
    fallback = available[0]
    vlog(verbose, f"[MODEL_PICK] Fallback: {fallback}")
    return fallback

def _resolve_threshold(preferred: str = "medium") -> Any:
    """
    Find the best available HarmBlockThreshold constant for a semantic preference.
    preferred options we consider: 'medium', 'low', 'high', 'none'
    We examine attributes of HarmBlockThreshold dynamically to support multiple SDK versions.
    """
    try:
        available = {name: getattr(HarmBlockThreshold, name) for name in dir(HarmBlockThreshold) if name.isupper()}
    except Exception:
        return None  # Safety system not available

    # Normalize keys for fuzzy search
    norm = {k.lower(): v for k, v in available.items()}

    # Priority lists per semantic target
    if preferred == "medium":
        for candidate in [
            "block_medium_and_above",
            "medium_and_above",              # older naming (if it ever existed)
            "block_only_high",               # stricter fallback
            "block_low_and_above",           # looser fallback
            "block_none",
            "none"
        ]:
            if candidate in norm:
                return norm[candidate]
    elif preferred == "low":
        for candidate in [
            "block_low_and_above",
            "block_medium_and_above",
            "block_only_high",
            "block_none"
        ]:
            if candidate in norm:
                return norm[candidate]
    elif preferred == "high":
        for candidate in [
            "block_only_high",
            "block_medium_and_above",
            "block_low_and_above",
            "block_none"
        ]:
            if candidate in norm:
                return norm[candidate]
    elif preferred == "none":
        for candidate in ["block_none", "none"]:
            if candidate in norm:
                return norm[candidate]

    # Absolute fallback: pick any one (stable ordering by name)
    if norm:
        return norm[sorted(norm.keys())[0]]
    return None


def build_safety_settings() -> List[Dict[str, Any]]:
    """
    Build safety settings compatible with multiple SDK versions.
    If thresholds are unavailable, returns an empty list (which usually means default policy).
    """
    try:
        # Choose a medium-ish policy for harassment/hate/sexual content, and medium for dangerous.
        threshold = _resolve_threshold("medium")
        if threshold is None:
            print("[SAFETY] Could not resolve any HarmBlockThreshold constants; using empty settings.")
            return []

        categories = [
            getattr(HarmCategory, "HARM_CATEGORY_HARASSMENT", None),
            getattr(HarmCategory, "HARM_CATEGORY_HATE_SPEECH", None),
            getattr(HarmCategory, "HARM_CATEGORY_SEXUALLY_EXPLICIT", None),
            getattr(HarmCategory, "HARM_CATEGORY_DANGEROUS_CONTENT", None)
        ]
        settings = []
        for cat in categories:
            if cat is not None:
                settings.append({"category": cat, "threshold": threshold})
        if not settings:
            print("[SAFETY] No HarmCategory attributes found; returning empty safety list.")
        return settings
    except Exception as e:
        # In case enums are radically different or removed
        print(f"[SAFETY] Error building safety settings: {e}. Proceeding without explicit safety settings.")
        return []
    
def init_model(model_name: str):
    return genai.GenerativeModel(
        model_name=model_name,
        safety_settings=build_safety_settings(),
        generation_config={
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 512,
        },
    )

def load_prompts(base: List[str], safe_only: bool, prompts_file: Optional[str]) -> List[str]:
    prompts = base[:1] if safe_only else list(base)
    if prompts_file:
        path = Path(prompts_file)
        if path.is_file():
            extra = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
            prompts.extend(extra)
        else:
            sys.stderr.write(f"WARNING: prompts file '{prompts_file}' not found.\n")
    return prompts

def run_prompt(model, model_name: str, prompt: str, idx: int, max_preview: int) -> PromptResult:
    start = time.time()
    error: Optional[str] = None
    blocked = False
    success = False
    finish_reasons: List[str] = []
    candidate_count = 0
    text_parts_total = 0
    preview: Optional[str] = None
    safety_summary: List[Dict[str, Any]] = []

    try:
        resp = model.generate_content(prompt)
    except Exception as e:
        error = f"generation_exception: {e}"
        return PromptResult(
            prompt_index=idx,
            prompt_snippet=prompt[:80],
            model_name=model_name,
            success=False,
            blocked=False,
            error=error,
            finish_reasons=[],
            candidate_count=0,
            text_parts_total=0,
            extracted_text_preview=None,
            safety_summary=[],
            latency_seconds=time.time() - start,
        )

    candidates = getattr(resp, "candidates", []) or []
    candidate_count = len(candidates)
    collected: List[str] = []

    for c in candidates:
        fr = str(getattr(c, "finish_reason", None))
        finish_reasons.append(fr)
        if getattr(c, "safety_ratings", None):
            for sr in c.safety_ratings:
                safety_summary.append({
                    "category": getattr(sr, "category", None),
                    "probability": getattr(sr, "probability", None),
                    "blocked": getattr(sr, "blocked", None),
                })
        parts = getattr(getattr(c, "content", None), "parts", []) or []
        for p in parts:
            text = getattr(p, "text", None)
            if text:
                text_parts_total += 1
                collected.append(text)

    if not collected:
        if any(fr.lower() == "safety" for fr in finish_reasons):
            blocked = True
        try:
            _ = resp.text  # attempt quick accessor
        except Exception as e:
            if not error:
                error = f"quick_accessor_error: {e}"
    else:
        success = True
        combined = "\n".join(collected)
        preview = combined[:max_preview]

    return PromptResult(
        prompt_index=idx,
        prompt_snippet=prompt[:80],
        model_name=model_name,
        success=success,
        blocked=blocked,
        error=error,
        finish_reasons=finish_reasons,
        candidate_count=candidate_count,
        text_parts_total=text_parts_total,
        extracted_text_preview=preview,
        safety_summary=safety_summary,
        latency_seconds=time.time() - start,
    )

def summarize(results: List[PromptResult], key_present: bool) -> Dict[str, Any]:
    total = len(results)
    successes = sum(r.success for r in results)
    blocked = sum(r.blocked for r in results)
    empties = sum((not r.success and not r.blocked) for r in results)
    any_generation_exception = any(r.error and "generation_exception" in r.error for r in results)
    return {
        "total_tests": total,
        "successes": successes,
        "blocked": blocked,
        "empties_nonblocked": empties,
        "any_generation_exception": any_generation_exception,
        "all_success": successes == total and total > 0,
        "api_key_present": key_present,
        "fatal": False,
    }

def decide_exit_code(summary: Dict[str, Any]) -> int:
    if summary.get("fatal"):
        return EXIT_FATAL
    if summary["all_success"]:
        return EXIT_SUCCESS
    if summary["api_key_present"] and summary["successes"] > 0:
        return EXIT_PARTIAL
    return EXIT_FATAL

def colorize(val: Any, good=False, warn=False, bad=False) -> str:
    if not COLOR_ENABLED:
        return str(val)
    if good:
        return f"{COLOR['green']}{val}{COLOR['reset']}"
    if warn:
        return f"{COLOR['yellow']}{val}{COLOR['reset']}"
    if bad:
        return f"{COLOR['red']}{val}{COLOR['reset']}"
    return str(val)

def print_summary(summary: Dict[str, Any]) -> None:
    # Handles both normal and fatal (normalized) summaries.
    print("---- Gemini Diagnostic Summary ----")
    if summary.get("fatal"):
        print_fatal_summary(summary)
        return
    total = summary.get("total_tests", 0)
    successes = summary.get("successes", 0)
    blocked = summary.get("blocked", 0)
    empties = summary.get("empties_nonblocked", 0)
    any_gen_err = summary.get("any_generation_exception", False)
    all_success = summary.get("all_success", False)

    print(f"Total tests: {total}")
    print(f"Successes: {colorize(successes, good=all_success and total > 0)}")
    print(f"Blocked (safety): {colorize(blocked, warn=blocked > 0)}")
    print(f"Empty (non-blocked): {colorize(empties, warn=empties > 0)}")
    print(f"Any generation exception: {colorize(any_gen_err, bad=any_gen_err)}")
    print(f"All success: {colorize(all_success, good=all_success, bad=not all_success)}")

def print_fatal_summary(summary: Dict[str, Any]) -> None:
    # Called for fatal states (already normalized)
    reason = summary.get("reason")
    print(colorize(f"FATAL: {reason}", bad=True))
    if summary.get("error"):
        print(f"Error: {summary['error']}")
    if summary.get("import_error"):
        print(f"Import Error: {summary['import_error']}")
    # Show API key presence for clarity
    print(f"API Key Present: {summary.get('api_key_present')}")

def normalize_fatal_summary(base_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure fatal summary still carries the numeric keys to avoid KeyError.
    """
    defaults = {
        "total_tests": 0,
        "successes": 0,
        "blocked": 0,
        "empties_nonblocked": 0,
        "any_generation_exception": False,
        "all_success": False,
    }
    merged = {**defaults, **base_summary}
    merged["fatal"] = True
    return merged

def load_all_prompts(args) -> List[str]:
    return load_prompts(DEFAULT_PROMPTS, args.safe_only, args.prompts_file)

def run_diagnostic(args: argparse.Namespace) -> DiagnosticReport:
    global COLOR_ENABLED
    if args.no_color:
        COLOR_ENABLED = False

    env = environment_info()

    # Fatal: library import failure
    if not LIB_IMPORTED:
        return DiagnosticReport(
            environment=env,
            available_models=[],
            selected_model=None,
            loop_count=args.loops,
            results=[],
            summary=normalize_fatal_summary({
                "reason": "import_failure",
                "import_error": env.get("import_error"),
                "api_key_present": env["google_api_key_present"],
            }),
        )

    # Configure API
    try:
        configure_api_key()
    except Exception as e:
        return DiagnosticReport(
            environment=env,
            available_models=[],
            selected_model=None,
            loop_count=args.loops,
            results=[],
            summary=normalize_fatal_summary({
                "reason": "api_config_failure",
                "error": str(e),
                "api_key_present": env["google_api_key_present"],
            }),
        )

    # List models
    try:
        available = list_generation_models(args.verbose)
    except Exception as e:
        return DiagnosticReport(
            environment=env,
            available_models=[],
            selected_model=None,
            loop_count=args.loops,
            results=[],
            summary=normalize_fatal_summary({
                "reason": "model_list_failure",
                "error": str(e),
                "api_key_present": env["google_api_key_present"],
            }),
        )

    if args.list_models:
        # Non-fatal list-only; no numeric keys needed but keep API shape uniform
        return DiagnosticReport(
            environment=env,
            available_models=available,
            selected_model=None,
            loop_count=args.loops,
            results=[],
            summary=normalize_fatal_summary({
                "fatal": False,
                "reason": "list_only",
                "mode": "list_only",
                "api_key_present": env["google_api_key_present"],
            }),
        )

    # Model selection
    try:
        model_name = select_model(args.model, available, args.verbose)
    except Exception as e:
        return DiagnosticReport(
            environment=env,
            available_models=available,
            selected_model=None,
            loop_count=args.loops,
            results=[],
            summary=normalize_fatal_summary({
                "reason": "model_selection_failure",
                "error": str(e),
                "api_key_present": env["google_api_key_present"],
            }),
        )

    # Init model
    try:
        model = init_model(model_name)
    except Exception as e:
        return DiagnosticReport(
            environment=env,
            available_models=available,
            selected_model=model_name,
            loop_count=args.loops,
            results=[],
            summary=normalize_fatal_summary({
                "reason": "model_init_failure",
                "error": str(e),
                "api_key_present": env["google_api_key_present"],
            }),
        )

    prompts = load_all_prompts(args)
    if args.show_prompts:
        print("---- Prompts to Run ----")
        for i, pr in enumerate(prompts):
            print(f"[{i}] {pr}")
        print("------------------------")

    results: List[PromptResult] = []
    for loop_idx in range(args.loops):
        for p_idx, prompt in enumerate(prompts):
            vlog(args.verbose, f"[RUN] loop {loop_idx+1}/{args.loops} prompt {p_idx+1}/{len(prompts)}")
            pr = run_prompt(model, model_name, prompt, idx=p_idx, max_preview=args.max_chars_preview)
            results.append(pr)
            time.sleep(0.5)

    summary = summarize(results, key_present=env["google_api_key_present"])
    summary["fatal"] = False
    return DiagnosticReport(
        environment=env,
        available_models=available,
        selected_model=model_name,
        loop_count=args.loops,
        results=results,
        summary=summary,
    )

def report_to_dict(report: DiagnosticReport) -> Dict[str, Any]:
    return {
        "environment": report.environment,
        "available_models": report.available_models,
        "selected_model": report.selected_model,
        "loop_count": report.loop_count,
        "results": [asdict(r) for r in report.results],
        "summary": report.summary,
    }

def write_json(path: str, data: Dict[str, Any]) -> None:
    try:
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"JSON report written to: {path}")
    except Exception as e:
        sys.stderr.write(f"Failed to write JSON report: {e}\n")

def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    report = run_diagnostic(args)

    # Special handling for list-only
    if report.summary.get("mode") == "list_only":
        print("---- Available Models ----")
        for m in report.available_models:
            print(m)
        if report.environment.get("dotenv_loaded"):
            print(f"(dotenv loaded from: {report.environment['dotenv_loaded']})")
        if args.json_out:
            write_json(args.json_out, report_to_dict(report))
        # list_only isn't fatal; exit 0
        return EXIT_SUCCESS

    # Print summary (fatal or not)
    print_summary(report.summary)

    if args.json_out:
        write_json(args.json_out, report_to_dict(report))

    exit_code = decide_exit_code(report.summary)
    return exit_code

if __name__ == "__main__":
    try:
        rc = main()
        sys.exit(rc)
    except KeyboardInterrupt:
        sys.stderr.write("Interrupted by user.\n")
        sys.exit(130)
    except Exception:
        traceback.print_exc()
        sys.exit(EXIT_FATAL)