import re
import io

with open(r"d:\Attempt 2\scripts\found_block.txt", 'r', encoding='utf-8') as f:
    text = f.read()

# get the quoted part
lines = text.split('\n')
quoted_lines = []
for line in lines:
    if line.startswith("> "):
        quoted_lines.append(line[2:])
    elif line == ">":
        quoted_lines.append("")

quoted_text = '\n'.join(quoted_lines)

# Strip artifacts
quoted_text = quoted_text.replace("Image: Profile Badge for the Achievement Top 1% Commenter Top 1% Commenter", "")
quoted_text = re.sub(r'(More replies\s*)+', '', quoted_text)
quoted_text = re.sub(r'<[^>]+>', '', quoted_text) # strip HTML

# find OP
# title starts with # 
title_match = re.search(r'# (.*?)\n', quoted_text)
if title_match:
    op_start = title_match.end()
    rest = quoted_text[op_start:]
    
    # regex for comment
    comment_pattern = re.compile(r'\n([A-Za-z0-9_.-]+)\n+•\n+(\d+[a-z]+ ago)\n')
    
    parts = comment_pattern.split(rest)
    op_text = parts[0].strip()
    
    out = io.StringIO()
    out.write("OP UNIT:\n")
    out.write(op_text + "\n")
    out.write("\n" + "="*40 + "\n")
    
    comments = []
    for i in range(1, len(parts), 3):
        author = parts[i]
        time = parts[i+1]
        comment_text = parts[i+2].strip()
        comments.append((author, time, comment_text))
        
    for idx, c in enumerate(comments):
        out.write(f"COMMENT {idx+1} ({c[0]}, {c[1]}):\n")
        out.write(c[2] + "\n")
        out.write("\n" + "-"*40 + "\n")
        
    out.write(f"Total units: {1 + len(comments)}\n")
    
    with open(r"d:\Attempt 2\scripts\test_s031_output.txt", "w", encoding='utf-8') as f:
        f.write(out.getvalue())
