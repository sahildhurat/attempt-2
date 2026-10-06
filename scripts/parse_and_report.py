import re
import html
import json
import statistics
import sys
import io

def normalize_text(text):
    # tags, then entities, then whitespace
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='utf-16') as f:
            content = f.read()

    blocks = content.split('================================================================================')
    
    entries_parsed = 0
    units_produced = 0
    units_per_thread = []
    reply_count = 0
    rejections_by_status = {}
    units_lengths = []
    
    all_units = []
    s031_units = []
    verbatim_threads = [] # collect 3
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
            
        # Parse header
        lines = block.split('\n')
        s_line = None
        source_line = None
        status_line = None
        
        for idx, line in enumerate(lines):
            if re.match(r'^S\d+\s+\|', line):
                s_line = line
            elif line.startswith('Source:'):
                source_line = line
            elif line.startswith('Status:'):
                status_line = line
            
            if s_line and source_line and status_line:
                break
                
        if not (s_line and source_line and status_line):
            continue
            
        entries_parsed += 1
        s_id = s_line.split('|')[0].strip()
        url = source_line.replace('Source:', '').strip()
        status = status_line.replace('Status:', '').strip()
        
        # Reject Google Community
        is_community = 'support.google.com' in url
        if is_community:
            rejections_by_status['Google Community'] = rejections_by_status.get('Google Community', 0) + 1
            continue
            
        if status in ["SUMMARY ONLY", "UNAVAILABLE", "UNAVAILABLE / TITLE ONLY"]:
            rejections_by_status[status] = rejections_by_status.get(status, 0) + 1
            continue
            
        # Determine text_completeness
        if status in ["RETRIEVED REDDIT TEXT \u2014 MAY BE INCOMPLETE", "EARLIER REDDIT TEXT \u2014 MAY BE INCOMPLETE", "RETRIEVED REDDIT TEXT - MAY BE INCOMPLETE", "EARLIER REDDIT TEXT - MAY BE INCOMPLETE", "RETRIEVED REDDIT TEXT", "EARLIER REDDIT TEXT"]:
            text_completeness = "full"
        elif status in ["INDEXED REDDIT EXCERPT \u2014 NOT A COMPLETE CONVERSATION", "INDEXED REDDIT EXCERPT - NOT A COMPLETE CONVERSATION", "INDEXED REDDIT EXCERPT"]:
            text_completeness = "snippet"
        else:
            # Check prefix
            if "RETRIEVED REDDIT TEXT" in status or "EARLIER REDDIT TEXT" in status:
                text_completeness = "full"
            elif "INDEXED REDDIT EXCERPT" in status:
                text_completeness = "snippet"
            else:
                rejections_by_status[status] = rejections_by_status.get(status, 0) + 1
                continue
                
        # Base36 ID from URL
        # e.g., https://www.reddit.com/r/googlephotos/comments/1wn0i1g/...
        match = re.search(r'comments/([a-z0-9]+)/', url)
        if match:
            source_id = match.group(1)
        else:
            source_id = "unknown"
            
        # Get body text
        body_lines = []
        in_body = False
        for line in lines:
            if line.startswith('Direct quotation from the linked Reddit thread:'):
                in_body = True
                continue
            if line.startswith('>'):
                in_body = True
            
            if in_body:
                body_lines.append(line)
                
        # Clean up > prefix
        quoted_lines = []
        for line in body_lines:
            if line.startswith("> "):
                quoted_lines.append(line[2:])
            elif line.startswith(">"):
                quoted_lines.append(line[1:])
                
        quoted_text = '\n'.join(quoted_lines)
        
        thread_units = []
        is_snippet = text_completeness == "snippet"
        
        if is_snippet:
            # Handle INDEXED REDDIT EXCERPT as a single multi_speaker=true blob
            # Strip artifacts for this blob
            quoted_text = quoted_text.replace("Image: Profile Badge for the Achievement Top 1% Commenter Top 1% Commenter", "")
            quoted_text = quoted_text.replace("Image: Profile Badge for the Achievement Top 1% Commenter", "")
            quoted_text = re.sub(r'(?i)(More replies\s*|more reply\s*)+', '', quoted_text)
            
            norm_blob = normalize_text(quoted_text)
            if norm_blob:
                thread_units.append({
                    "source": "reddit_assisted",
                    "source_type": "discussion",
                    "source_id": source_id,
                    "url": url,
                    "is_reply": False,
                    "parent_id": None,
                    "created_at": None,
                    "retrieved_at": "2026-09-29",
                    "language": None,
                    "text_completeness": "snippet",
                    "multi_speaker": True,
                    "text": norm_blob
                })
        else:
            # Full thread: split on author blocks FIRST, then strip artifacts
            comment_pattern = re.compile(r'\n([^\n]{1,80}?)\s*\n*•\n*\s*(\d+[a-z]+ ago)\s*\n+')
            
            title_match = re.search(r'# (.*?)\n', quoted_text)
            if title_match:
                op_start = title_match.end()
                rest = quoted_text[op_start:]
                parts = comment_pattern.split(rest)
                op_text_raw = parts[0]
            else:
                parts = comment_pattern.split(quoted_text)
                op_text_raw = parts[0]
                
            def strip_artifacts(t):
                t = t.replace("Image: Profile Badge for the Achievement Top 1% Commenter Top 1% Commenter", "")
                t = t.replace("Image: Profile Badge for the Achievement Top 1% Commenter", "")
                t = re.sub(r'(?i)(More replies\s*|more reply\s*)+', '', t)
                return t
                
            norm_op = normalize_text(strip_artifacts(op_text_raw))
            if norm_op:
                thread_units.append({
                    "source": "reddit_assisted",
                    "source_type": "discussion",
                    "source_id": source_id,
                    "url": url,
                    "is_reply": False,
                    "parent_id": None,
                    "created_at": None,
                    "retrieved_at": "2026-09-29",
                    "language": None,
                    "text_completeness": text_completeness,
                    "multi_speaker": False,
                    "text": norm_op
                })
                
            for i in range(1, len(parts), 3):
                comment_text_raw = parts[i+2]
                norm_comment = normalize_text(strip_artifacts(comment_text_raw))
                if norm_comment:
                    thread_units.append({
                        "source": "reddit_assisted",
                        "source_type": "discussion",
                        "source_id": source_id,
                        "url": url,
                        "is_reply": True,
                        "parent_id": source_id,
                        "created_at": None,
                        "retrieved_at": "2026-09-29",
                        "language": None,
                        "text_completeness": text_completeness,
                        "multi_speaker": False,
                        "text": norm_comment
                    })
                    reply_count += 1
        all_units.extend(thread_units)
        units_produced += len(thread_units)
        units_per_thread.append(len(thread_units))
        for u in thread_units:
            units_lengths.append(len(u['text']))
            
        if s_id == "S031":
            s031_units = thread_units
            
        if len(verbatim_threads) < 3 and len(thread_units) > 0:
            verbatim_threads.append(thread_units)

            
    merged_unit_violations = 0
    merged_pattern = re.compile(r'• \d+[a-z]+ ago', re.IGNORECASE)
    snippet_count = 0
    units_above_floor = 0
    
    violation_texts = []
    for u in all_units:
        if u.get("multi_speaker"):
            snippet_count += 1
            
        if len(u['text']) >= 250:
            units_above_floor += 1
            
        if not u.get("multi_speaker"):
            match = merged_pattern.search(u['text'])
            if match and match.start() > 50:
                merged_unit_violations += 1
                violation_texts.append(u['text'])
                
    if violation_texts:
        with open(r'd:\Attempt 2\scripts\violations.txt', 'w', encoding='utf-8') as f:
            for t in violation_texts:
                f.write(t + "\n===\n")

    # Output reports
    out = io.StringIO()
    out.write("--- ACCEPTANCE TEST: S031 ---\n")
    if s031_units:
        for idx, u in enumerate(s031_units):
            out.write(f"Unit {idx+1} (Reply: {u['is_reply']}):\n")
            out.write(u['text'] + "\n")
            out.write("-" * 40 + "\n")
    else:
        out.write("S031 not found or produced 0 units.\n")
        
    out.write("\n--- REPORT ---\n")
    out.write(f"Entries parsed (total): {entries_parsed}\n")
    out.write(f"Units produced: {units_produced}\n")
    out.write(f"Reply count: {reply_count}\n")
    out.write(f"Rejections by status:\n")
    for k, v in rejections_by_status.items():
        out.write(f"  {k}: {v}\n")
        
    if units_per_thread:
        # Distribution
        out.write(f"Units per thread distribution:\n")
        out.write(f"  Min: {min(units_per_thread)}\n")
        out.write(f"  Max: {max(units_per_thread)}\n")
        out.write(f"  Mean: {statistics.mean(units_per_thread):.1f}\n")
        out.write(f"  Median: {statistics.median(units_per_thread)}\n")
        
    if units_lengths:
        out.write(f"Length deciles (characters):\n")
        deciles = statistics.quantiles(units_lengths, n=10)
        for i, d in enumerate(deciles):
            out.write(f"  {10*(i+1)}th percentile: {d:.1f}\n")
            
    out.write("\n--- 3 VERBATIM THREADS ---\n")
    for i, t in enumerate(verbatim_threads):
        out.write(f"THREAD {i+1}:\n")
        for idx, u in enumerate(t):
            out.write(f"  Unit {idx+1} (Reply: {u['is_reply']}): {u['text']}\n")
        out.write("=" * 40 + "\n")
    out.write(f"\nMerged-unit detector (units containing '• Nd ago' pattern >50 chars in): {merged_unit_violations}\n")
    out.write(f"Snippet entries marked multi_speaker=true: {snippet_count}\n")
    out.write(f"Units above 250-character floor: {units_above_floor}\n")
        
    with open(r"d:\Attempt 2\scripts\parse_report.txt", "w", encoding='utf-8') as f:
        f.write(out.getvalue())
        
    return all_units

if __name__ == "__main__":
    parse_file(r"d:\Attempt 2\data\raw\reddit_assisted\conversations.txt.txt")
