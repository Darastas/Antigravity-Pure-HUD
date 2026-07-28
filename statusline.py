#!/usr/bin/env python3
"""
Antigravity Pure HUD Engine v2
Zero-dependency status line for Antigravity CLI (AGY).

Architecture:
  - AGY CLI calls this script via stdin pipe on EVERY prompt and EVERY response.
  - On each call, we do a SYNCHRONOUS (blocking) HTTP query to the local AGY daemon
    to get the absolute freshest quota data. This is fast (~5ms localhost).
  - If the sync call fails, we fall back to stdin quota data.
  - We cache the result so the next call within TTL skips the HTTP query.
  - Shows all quota pools: Gemini, Claude/GPT (3P).
"""

import sys
import json
import os
import glob
import re
import time
import urllib.request
from datetime import datetime

CACHE_FILE = os.path.expanduser(r"~\.antigravity\live-cache.json")
CACHE_TTL = 4  # Seconds. Re-query if cache older than this.

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# ── Utilities ──────────────────────────────────────────────────────────────

def format_seconds(seconds):
    if not seconds or seconds <= 0:
        return ""
    mins = int(seconds) // 60
    hrs = mins // 60
    remaining_mins = mins % 60
    if hrs > 0:
        return f"{hrs}h{remaining_mins}m"
    return f"{remaining_mins}m"

def make_bar(pct, length=10, fill_char="█", empty_char="░"):
    pct = max(0.0, min(100.0, float(pct)))
    filled_len = int(round(length * pct / 100))
    return fill_char * filled_len + empty_char * (length - filled_len)


# ── Port Discovery ────────────────────────────────────────────────────────

def find_active_http_port():
    """Find the AGY daemon HTTP port by scanning logs and verifying liveness."""
    log_pattern = os.path.expanduser(r"~\.gemini\antigravity-cli\log\cli-*.log")
    logs = sorted(glob.glob(log_pattern), key=os.path.getmtime, reverse=True)
    for log_path in logs[:3]:  # Only check 3 most recent logs
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            ports = re.findall(r"listening on random port at (\d+) for HTTP", content)
            for port in reversed(ports):
                try:
                    url = f"http://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/GetUserStatus"
                    req = urllib.request.Request(url, data=b"{}", headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=1) as res:
                        if res.status == 200:
                            return port
                except Exception:
                    pass
        except Exception:
            continue
    return None


# ── Live Quota Sync ───────────────────────────────────────────────────────

def fetch_live_quota():
    """Synchronously fetch fresh quota from local AGY daemon. Returns dict of quota pools or None."""
    try:
        port = find_active_http_port()
        if not port:
            return None

        url = f"http://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/GetUserStatus"
        req = urllib.request.Request(url, data=b"{}", headers={"Content-Type": "application/json"})
        res = urllib.request.urlopen(req, timeout=2)
        data = json.loads(res.read().decode("utf-8"))

        configs = data.get("userStatus", {}).get("cascadeModelConfigData", {}).get("clientModelConfigs", [])

        # Group models into quota pools
        pools = {}  # pool_name -> {remaining_fraction, reset_in_seconds}
        for m in configs:
            label = m.get("label", "")
            q = m.get("quotaInfo", {})
            if "remainingFraction" not in q:
                continue

            # Determine pool name (Claude + GPT share one 3P quota pool)
            label_lower = label.lower()
            if "gemini" in label_lower:
                pool = "Gemini"
            elif "claude" in label_lower or "gpt" in label_lower:
                pool = "Claude/GPT"
            else:
                pool = label  # Unknown model, use label

            if pool in pools:
                continue  # Same pool already recorded

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

            pools[pool] = {
                "remaining_fraction": q.get("remainingFraction"),
                "reset_in_seconds": reset_sec
            }

        # Save to cache
        cache_data = {"timestamp": time.time(), "pools": pools}
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        tmp_file = CACHE_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)
        os.replace(tmp_file, CACHE_FILE)

        return pools
    except Exception:
        return None


def get_quota_pools():
    """Get quota pools, using cache if fresh, otherwise fetching live."""
    # Check if cache is fresh enough
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            ts = data.get("timestamp", 0)
            cache_age = time.time() - ts
            if cache_age < CACHE_TTL:
                pools = data.get("pools", {})
                # Decay reset timers
                for pool in pools.values():
                    if "reset_in_seconds" in pool:
                        pool["reset_in_seconds"] = max(0, pool["reset_in_seconds"] - int(cache_age))
                return pools
        except Exception:
            pass

    # Cache is stale or missing: fetch live (synchronous, ~5ms on localhost)
    pools = fetch_live_quota()
    if pools:
        return pools

    # Last resort: try to use stale cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            pools = data.get("pools", {})
            cache_age = time.time() - data.get("timestamp", 0)
            for pool in pools.values():
                if "reset_in_seconds" in pool:
                    pool["reset_in_seconds"] = max(0, pool["reset_in_seconds"] - int(cache_age))
            return pools
        except Exception:
            pass

    return None


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    # Legacy background sync entry point (no longer used, kept for compat)
    if "--sync-live" in sys.argv:
        fetch_live_quota()
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
    ctx_disp = f"[{ctx_bar}] {used_pct_val:.1f}%"

    # 3. Multi-Pool Quota Display
    pools = get_quota_pools()

    quota_parts = []
    if pools:
        # Display order: Gemini first, then Claude/GPT
        display_order = ["Gemini", "Claude/GPT"]
        for pool_name in display_order:
            if pool_name not in pools:
                continue
            p = pools[pool_name]
            frac = p.get("remaining_fraction")
            if frac is not None:
                pct = float(frac) * 100
                bar = make_bar(pct, length=8)
                reset_str = format_seconds(p.get("reset_in_seconds", 0))
                if reset_str:
                    quota_parts.append(f"{pool_name}: [{bar}] {pct:.1f}%({reset_str})")
                else:
                    quota_parts.append(f"{pool_name}: [{bar}] {pct:.1f}%")

        # Any pools not in display_order
        for pool_name, p in pools.items():
            if pool_name in display_order:
                continue
            frac = p.get("remaining_fraction")
            if frac is not None:
                pct = float(frac) * 100
                bar = make_bar(pct, length=8)
                quota_parts.append(f"{pool_name}: [{bar}] {pct:.1f}%")

    if not quota_parts:
        # Fallback to stdin quota if live fetch failed entirely
        quota_data = data.get("quota", {})
        if isinstance(quota_data, dict):
            gemini_q = quota_data.get("gemini-5h", {})
            tp_q = quota_data.get("3p-5h", {})
            if gemini_q and "remaining_fraction" in gemini_q:
                g_pct = float(gemini_q["remaining_fraction"]) * 100
                g_bar = make_bar(g_pct, length=8)
                g_reset = format_seconds(gemini_q.get("reset_in_seconds", 0))
                quota_parts.append(f"Gemini: [{g_bar}] {g_pct:.1f}%" + (f"({g_reset})" if g_reset else ""))
            if tp_q and "remaining_fraction" in tp_q:
                t_pct = float(tp_q["remaining_fraction"]) * 100
                t_bar = make_bar(t_pct, length=8)
                t_reset = format_seconds(tp_q.get("reset_in_seconds", 0))
                quota_parts.append(f"Claude/GPT: [{t_bar}] {t_pct:.1f}%" + (f"({t_reset})" if t_reset else ""))

    usage_disp = " | ".join(quota_parts) if quota_parts else "Active"

    print(f"{model_name} | Ctx: {ctx_disp} | {usage_disp}")

if __name__ == "__main__":
    main()
