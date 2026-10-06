import sys
import os
import re
sys.path.append('scripts/collectors')
import help_community_v2 as hc2

for tid in ['367230169', '319380955']:
    # Instead of fetching, we just mock the fetch_with_rate_limit to return the file content
    class DummyResponse:
        def __init__(self, text):
            self.text = text
            
    def mock_fetch(*args, **kwargs):
        with open(f"thread_{tid}_raw.txt", "r", encoding="utf-8") as f:
            return DummyResponse(f.read())
            
    hc2.fetch_with_rate_limit = mock_fetch
    
    status, msg, units = hc2.fetch_and_parse(None, tid)
    replies = [u for u in units if u['is_reply']]
    print(f"Thread {tid}: {len(replies)} replies")
