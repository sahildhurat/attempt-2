import urllib.request
import urllib.parse
import json
import time
import re
from bs4 import BeautifulSoup
import hashlib

def generate_id(source, source_id):
    return hashlib.sha256(f"{source}_{source_id}".encode()).hexdigest()

def get_session():
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    session = get_session()
    "})
    return session

def log_failure(collector_name, failure_type, details):
    import os
    os.makedirs(f"data/raw/{collector_name}", exist_ok=True)
    with open(f"data/raw/{collector_name}/failures.log", "a", encoding="utf-8") as f:
        f.write(json.dumps({"type": failure_type, "details": details}) + "\n")

def search_xda():
    query = 'site:xdaforums.com "Google Photos" (search OR missing OR find OR disappeared)'
    url = 'https://lite.duckduckgo.com/lite/'
    data = {'q': query}
    
    threads = set()
    session = get_session()
    try:
        response = fetch_with_rate_limit(session, "POST", url, "xda", data=data, timeout=10)
        response.raise_for_status()
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        for a in soup.find_all('a', class_='result-url'):
            href = a.get('href', '')
            if 'xdaforums.com/t/' in href:
                threads.add(href)
        if not threads:
            log_failure("xda", "EMPTY", f"search DDG query: {query} returned no threads")
    except Exception as e:
        if "RATE_LIMITED" in str(e):
            log_failure("xda", "RATE_LIMITED", str(e))
            return [], [] # Or appropriate return value based on signature... Wait, this is tricky to do globally
        if isinstance(e, requests.exceptions.RequestException):
        print("Error searching DDG:", e)
        log_failure("xda", "NETWORK", f"search DDG error: {e}")
    except Exception as e:
        print("Error parsing DDG:", e)
        log_failure("xda", "PARSE", f"search DDG error: {e}")
        
    return list(threads)

def parse_xda_thread(url):
    session = get_session()
    try:
        response = fetch_with_rate_limit(session, "GET", url, "xda", timeout=10)
        response.raise_for_status()
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        title = ""
        title_el = soup.find('h1', class_='p-title-value')
        if title_el:
            title = title_el.get_text(strip=True)
            
        messages = []
        for post in soup.find_all('article', class_='message'):
            content_el = post.find('div', class_='bbWrapper')
            if content_el:
                # Remove quotes
                for quote in content_el.find_all('blockquote'):
                    quote.decompose()
                messages.append(content_el.get_text(separator=' ', strip=True))
        
        if not messages:
            log_failure("xda", "EMPTY", f"url: {url} returned no messages")
                
        return title, messages
    except Exception as e:
        if "RATE_LIMITED" in str(e):
            log_failure("xda", "RATE_LIMITED", str(e))
            return [], [] # Or appropriate return value based on signature... Wait, this is tricky to do globally
        if isinstance(e, requests.exceptions.RequestException):
        print(f"Error fetching {url}: {e}")
        log_failure("xda", "NETWORK", f"url: {url}, error: {e}")
        return "", []
    except Exception as e:
        print(f"Error parsing {url}: {e}")
        log_failure("xda", "PARSE", f"url: {url}, error: {e}")
        return "", []

def run():
    print("Searching XDA...")
    threads = search_xda()
    print(f"Found {len(threads)} threads.")
    
    units = []
    total_replies = 0
    lengths = []
    
    complete_threads = []
    
    for url in threads:
        print(f"Parsing {url}...")
        m = re.search(r'/t/.*?\.(\d+)/?', url)
        if not m:
            continue
        tid = m.group(1)
        
        title, messages = parse_xda_thread(url)
        if not messages:
            continue
            
        op_text = messages[0]
        replies = messages[1:]
        
        total_replies += len(replies)
        lengths.append(len(op_text))
        for r in replies:
            lengths.append(len(r))
            
        if len(complete_threads) < 3:
            thread_str = f"--- THREAD {tid} ---\nTitle: {title}\nURL: {url}\n[OP]\n{op_text}\n"
            for i, r in enumerate(replies):
                thread_str += f"\n[REPLY {i+1}]\n{r}\n"
            complete_threads.append(thread_str)
            
        for i, text in enumerate(messages):
            is_reply = (i > 0)
            uid = f"{tid}_{i}" if is_reply else tid
            units.append({
                "id": generate_id("xda", uid),
                "source": "xda",
                "source_type": "discussion",
                "source_id": uid,
                "url": url,
                "text": text,
                "created_at": None,
                "is_reply": is_reply,
                "parent_id": tid if is_reply else None,
                "context": title,
                "text_completeness": "full"
            })
            
        time.sleep(1)
        
    import os
    os.makedirs("data/raw/xda", exist_ok=True)
    with open("data/raw/xda/units.jsonl", "w", encoding="utf-8") as f:
        for u in units:
            f.write(json.dumps(u) + "\n")
            
    lengths.sort()
    deciles = {f"{i*10}%": lengths[int(len(lengths)*i/10)] for i in range(1, 10)} if lengths else {}
    
    with open("xda_report.txt", "w", encoding="utf-8") as f:
        f.write(f"Threads fetched: {len(threads)}\n")
        f.write(f"Units produced: {len(units)}\n")
        f.write(f"Average units per thread: {len(units) / len(threads) if threads else 0:.2f}\n")
        f.write(f"Total reply count: {total_replies}\n")
        f.write(f"Character-length deciles: {deciles}\n\n")
        f.write("3 COMPLETE THREADS VERBATIM:\n")
        for ct in complete_threads:
            f.write(ct + "\n")

if __name__ == "__main__":
    run()
