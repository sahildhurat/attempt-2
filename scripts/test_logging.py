import os
import sys
import requests
import json

sys.path.append("scripts/collectors")

import network_utils
original_get_session = network_utils.get_session

class BadSession:
    def request(self, *args, **kwargs):
        raise requests.exceptions.ConnectionError("Induced failure for testing")
    def __getattr__(self, attr):
        return lambda *a, **kw: self.request(*a, **kw)
    headers = {}
    
def bad_get_session():
    return BadSession()

network_utils.get_session = bad_get_session

collectors = ['help_community', 'stackexchange', 'playstore', 'appstore', 'youtube', 'hn', 'reddit']

for c in collectors:
    try:
        mod = __import__(c)
        if hasattr(mod, 'collect'):
            print(f"Running {c}...")
            mod.collect()
    except Exception as e:
        print(f"Error in {c}: {e}")

for c in collectors:
    path = f"data/raw/{c}/failures.log"
    if os.path.exists(path):
        with open(path, "r") as f:
            lines = f.readlines()
            print(f"{c}: {len(lines)} failure lines logged.")
    else:
        print(f"{c}: NO failures.log found.")
