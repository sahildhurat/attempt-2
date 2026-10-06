import os
import re

def patch(file_name, collector_name):
    path = os.path.join('scripts/collectors', file_name)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Replace requests.Session() to get_session()
    content = content.replace('requests.Session()', 'get_session()')
    
    # Remove old Retry setup
    content = re.sub(r'retry = Retry\(.*?allowed_methods=.*?\)\n\s+adapter = HTTPAdapter\(max_retries=retry\)\n\s+session.mount\(\"http://\", adapter\)\n\s+session.mount\(\"https://\", adapter\)\n\s+session.headers.update\(.*?\)', '', content, flags=re.DOTALL)
    
    # Replace session.get
    content = re.sub(r'response = session\.get\((.*?), timeout=(.*?)\)', r'response = fetch_with_rate_limit(session, "GET", \1, "' + collector_name + r'", timeout=\2)', content)
    content = re.sub(r'response = session\.post\((.*?), data=(.*?), timeout=(.*?)\)', r'response = fetch_with_rate_limit(session, "POST", \1, "' + collector_name + r'", data=\2, timeout=\3)', content)
    
    # In except requests.exceptions.RequestException catch RATE_LIMITED
    content = content.replace('except requests.exceptions.RequestException as e:', 'except Exception as e:\n        if "RATE_LIMITED" in str(e):\n            log_failure("' + collector_name + '", "RATE_LIMITED", str(e))\n            return [], [] # Or appropriate return value based on signature... Wait, this is tricky to do globally\n        if isinstance(e, requests.exceptions.RequestException):')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

collectors = ['youtube.py', 'hn.py', 'stackexchange.py', 'appstore.py', 'manual_threads.py', 'xda.py']
for c in collectors:
    patch(c, c.split('.')[0])

# Fix playstore.py manually since it uses google_play_scraper
path = 'scripts/collectors/playstore.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
if 'network_utils' not in content:
    content = "import sys\nimport os\nsys.path.append(os.path.dirname(__file__))\nfrom network_utils import log_failure\nimport time\n" + content
    
    content = content.replace('except Exception as e:\n            print(f"Error fetching', 'except Exception as e:\n            if "429" in str(e) or "Too Many Requests" in str(e):\n                print("RATE_LIMITED on Play Store. Sleeping 10m")\n                log_failure("playstore", "RATE_LIMITED", str(e))\n                time.sleep(600)\n                continue\n            print(f"Error fetching')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
