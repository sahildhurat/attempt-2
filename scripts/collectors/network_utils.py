import os
import time
import requests
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import sys

class CircuitBreakerTripped(Exception):
    pass

_cb_state = {
    "consecutive_same": 0,
    "consecutive_any": 0,
    "last_type": None
}

def _record_success():
    _cb_state["consecutive_same"] = 0
    _cb_state["consecutive_any"] = 0
    _cb_state["last_type"] = None

def _record_failure(collector_name, failure_type, details):
    if failure_type not in ["NETWORK", "RATE_LIMITED", "PARSE"]:
        return
        
    _cb_state["consecutive_any"] += 1
    
    if _cb_state["last_type"] == failure_type:
        _cb_state["consecutive_same"] += 1
    else:
        _cb_state["last_type"] = failure_type
        _cb_state["consecutive_same"] = 1
        
    if _cb_state["consecutive_same"] >= 5 or _cb_state["consecutive_any"] >= 10:
        msg = f"ABORT RUN: {collector_name} tripped circuit breaker. Last type: {failure_type}. Details: {details}"
        log_failure(collector_name, "FATAL", msg)
        print(f"\n{msg}\n")
        raise CircuitBreakerTripped(msg)


def log_failure(collector_name, failure_type, details):
    os.makedirs(f"data/raw/{collector_name}", exist_ok=True)
    with open(f"data/raw/{collector_name}/failures.log", "a", encoding="utf-8") as f:
        f.write(json.dumps({"type": failure_type, "details": details}) + "\n")

def get_session():
    session = requests.Session()
    # Notice we do NOT include 429 or 403 in status_forcelist so we can handle them manually
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=None)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": "DiscoveryEngine/1.0 (academic research)"})
    return session

def fetch_with_rate_limit(session, method, url, collector_name, max_rate_limit_retries=3, **kwargs):
    rate_limit_count = 0
    while rate_limit_count < max_rate_limit_retries:
        try:
            response = session.request(method, url, **kwargs)
            if response.status_code in [429, 403]:
                rate_limit_count += 1
                retry_after = response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    sleep_time = int(retry_after)
                else:
                    sleep_time = 600 # 10 minutes
                    
                log_failure(collector_name, "RATE_LIMITED", f"url: {url}, status: {response.status_code}. Sleeping {sleep_time}s. (Attempt {rate_limit_count}/{max_rate_limit_retries})")
                print(f"[{collector_name}] RATE_LIMITED on {url}. Sleeping for {sleep_time} seconds...")
                
                time.sleep(sleep_time)
                continue
                
            response.raise_for_status()
            _record_success()
            return response
            
        except requests.exceptions.RequestException as e:
            if hasattr(e, "response") and e.response is not None and e.response.status_code in [429, 403]:
                rate_limit_count += 1
                retry_after = e.response.headers.get("Retry-After")
                sleep_time = int(retry_after) if (retry_after and retry_after.isdigit()) else 600
                log_failure(collector_name, "RATE_LIMITED", f"url: {url}, status: {e.response.status_code}. Sleeping {sleep_time}s. (Attempt {rate_limit_count}/{max_rate_limit_retries})")
                print(f"[{collector_name}] RATE_LIMITED on {url}. Sleeping for {sleep_time} seconds...")
                time.sleep(sleep_time)
                continue
            _record_failure(collector_name, "NETWORK", str(e))
            raise e
            
    # If we exit the loop, we hit 3 consecutive rate limits
    msg = f"Exceeded {max_rate_limit_retries} consecutive rate limits for {collector_name}"
    _record_failure(collector_name, "RATE_LIMITED", msg)
    raise Exception(f"RATE_LIMITED: {msg}")
