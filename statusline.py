#!/usr/bin/env python3
"""
Antigravity Pure HUD Engine
A lightweight, zero-dependency status line generator for Antigravity CLI (AGY).
Features smart dynamic quota polling, atomic file caching, real-time countdown decay, and robust model matching.
"""

import sys
import json
import os
import glob
import re
import time
import urllib.request
import subprocess
from datetime import datetime

CACHE_FILE = os.path.expanduser(r"~\.antigravity\live-cache.json")
LONG_TASK_TTL = 60  # Fallback sync interval for long tasks
SHORT_CHAT_TTL = 5   # Cooldown interval after AI finishes answering

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def format_seconds(seconds):
    if not seconds or seconds <= 0:
        return ""
    mins = int(seconds) // 60
    hrs = mins // 60
    remaining_mins = mins % 60
    if hrs > 0:
        return f"{hrs}h {remaining_mins}m"
    return f"{remaining_mins}m"

def make_bar(pct, length=10, fill_char="█", empty_char="░"):
    pct = max(0.0, min(100.0, float(pct)))
    filled_len = int(round(length * pct / 100))
    return fill_char * filled_len + empty_char * (length - filled_len)

def normalize_model_name(name):
    """Normalize model string for accurate tier matching."""
    return re.sub(r"[^a-z0-9]", "", str(name).lower())

def sync_live_quota():
    """Queries local AGY language server endpoint to get fresh live model quotas."""
    try:
        log_pattern = os.path.expanduser(r"~\.gemini\antigravity-cli\log\cli-*.log")
        logs = sorted(glob.glob(log_pattern), key=os.path.getmtime, reverse=True)
        if not logs:
            return
        
        port = None
        with open(logs[0], "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                m = re.search(r"listening on random port at (\d+) for HTTP", line)
                if m:
                    port = m.group(1)

        if not port:
            return

        url = f"http://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/GetUserStatus"
        req = urllib.request.Request(url, data=b"{}", headers={"Content-Type": "application/json"})
        res = urllib.request.urlopen(req, timeout=3)
        data = json.loads(res.read().decode("utf-8"))

        models = data.get("userStatus", {}).get("cascadeModelConfigData", {}).get("clientModelConfigs", [])
        model_map = {}
        for m in models:
            label = m.get("label")
            q = m.get("quotaInfo", {})
            if label and "remainingFraction" in q:
                reset_sec = 0
                reset_time_str = q.get("resetTime")
                if reset_time_str:
                    try:
                        clean_ts = reset_time_str.replace("Z", "+00:00")
                        dt = datetime.fromisoformat(clean_ts)
                        now = datetime.now(dt.tzinfo)
                        reset_sec = max(0, int((dt - now).total_seconds()))
                    except Exception:
                        pass
                
                model_map[label] = {
                    "remaining_fraction": q.get("remainingFraction"),
                    "reset_in_seconds": reset_sec
                }

        cache_data = {
            "timestamp": time.time(),
            "models": model_map
        }

        # Atomic write to prevent file read conflicts
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        tmp_file = CACHE_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)
        os.replace(tmp_file, CACHE_FILE)
    except Exception:
        pass

def load_cached_live_quota(model_name, is_idle=False):
    """Loads cached live quota if fresh, dynamically decays reset seconds, and triggers background sync."""
    cached = None
    cache_age = 999999

    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                ts = data.get("timestamp", 0)
                cache_age = time.time() - ts
                models = data.get("models", {})
                
                # 1. Exact match
                cached = models.get(model_name)
                
                # 2. Normalized match if exact match fails
                if not cached:
                    norm_target = normalize_model_name(model_name)
                    for k, v in models.items():
                        norm_k = normalize_model_name(k)
                        if norm_target == norm_k or norm_target in norm_k or norm_k in norm_target:
                            cached = v
                            break

                # 3. Dynamic countdown decay based on elapsed cache age
                if cached and "reset_in_seconds" in cached:
                    orig_sec = cached.get("reset_in_seconds", 0)
                    decayed_sec = max(0, orig_sec - int(cache_age))
                    cached = dict(cached)
                    cached["reset_in_seconds"] = decayed_sec
        except Exception:
            pass

    target_ttl = SHORT_CHAT_TTL if is_idle else LONG_TASK_TTL

    if cache_age >= target_ttl:
        try:
            py_exe = sys.executable
            script_path = os.path.abspath(__file__)
            subprocess.Popen([py_exe, script_path, "--sync-live"], creationflags=0x08000000 if os.name == 'nt' else 0)
        except Exception:
            pass

    return cached

def main():
    if "--sync-live" in sys.argv:
        sync_live_quota()
        return

    try:
        raw = sys.stdin.read()
        if not raw or not raw.strip():
            return
        data = json.loads(raw)
    except Exception:
        print("[AGY Status] Active")
        return

    # 1. Model Name
    model_obj = data.get("model", {})
    if isinstance(model_obj, dict):
        model_name = model_obj.get("display_name") or model_obj.get("id") or "Gemini"
    else:
        model_name = str(model_obj)

    # 2. Context Window (Forward: Used %)
    ctx = data.get("context_window", {})
    used_pct = ctx.get("used_percentage")
    if used_pct is not None:
        used_pct_val = float(used_pct)
    else:
        tot_in = ctx.get("total_input_tokens", 0)
        tot_out = ctx.get("total_output_tokens", 0)
        size = ctx.get("context_window_size", 1048576)
        used_pct_val = ((tot_in + tot_out) / max(1, size)) * 100

    ctx_bar = make_bar(used_pct_val, length=10)
    ctx_disp = f"[{ctx_bar}] {used_pct_val:.1f}% used"

    # Check agent state
    agent_state = data.get("agent_state", "idle")
    is_idle = (agent_state == "idle")

    # 3. Usage / Quota (Reverse: Remaining %)
    rem_fraction = None
    reset_sec = 0

    # Priority 1: Always check live background cache (updated every 5s on chat finish, 60s for long tasks)
    live_q = load_cached_live_quota(model_name, is_idle=is_idle)
    if live_q and live_q.get("remaining_fraction") is not None:
        rem_fraction = live_q.get("remaining_fraction")
        if "reset_in_seconds" in live_q:
            reset_sec = live_q.get("reset_in_seconds")

    # Priority 2: Fallback to stdin quota if live background cache is not available
    if rem_fraction is None:
        quota_data = data.get("quota", {})
        quota_item = {}
        if isinstance(quota_data, dict):
            quota_item = quota_data.get("gemini-5h") or quota_data.get("3p-5h") or {}
            if not quota_item:
                for k, v in quota_data.items():
                    if isinstance(v, dict) and "remaining_fraction" in v:
                        quota_item = v
                        break

        rem_fraction = quota_item.get("remaining_fraction")
        reset_sec = quota_item.get("reset_in_seconds", 0)

    if rem_fraction is not None:
        rem_pct_val = float(rem_fraction) * 100
        quota_bar = make_bar(rem_pct_val, length=10)
        usage_disp = f"[{quota_bar}] {rem_pct_val:.1f}% left"
        reset_str = format_seconds(reset_sec)
        if reset_str:
            usage_disp += f" (resets in {reset_str})"
    else:
        usage_disp = "Active"

    print(f"Model: {model_name} | Context: {ctx_disp} | Usage: {usage_disp}")

if __name__ == "__main__":
    main()
