import os
import re

collectors = [
    'scripts/collectors/help_community.py',
    'scripts/collectors/stackexchange.py',
    'scripts/collectors/playstore.py',
    'scripts/collectors/appstore.py',
    'scripts/collectors/youtube.py',
    'scripts/collectors/hn.py',
    'scripts/collectors/xda.py'
]

for c in collectors:
    if os.path.exists(c):
        with open(c, 'r', encoding='utf-8') as f:
            content = f.read()
            
        def replacer(match):
            filename = match.group(1)
            iterator = match.group(2)
            write_expr = match.group(3)
            return f'''    import os
    out_file = "{filename}"
    tmp_file = out_file + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        for u in {iterator}:
            f.write({write_expr})
    if os.path.exists(tmp_file):
        os.replace(tmp_file, out_file)'''

        new_content = re.sub(
            r'with open\(\"(data/unified/[^\"]+\.jsonl)\", \"w\"(?:, encoding=\"utf-8\")?\) as f:\s*\n\s*for u in (.*?):\s*\n\s*f\.write\((.*?)\)',
            replacer,
            content
        )
        
        def replacer_youtube(match):
            filename = match.group(1)
            return f'''    import os
    out_file = "{filename}"
    tmp_file = out_file + ".tmp"
    with open(tmp_file, "w") as f:'''
            
        if 'with open("data/unified/youtube.jsonl", "w") as f:' in new_content:
            new_content = new_content.replace(
                'with open("data/unified/youtube.jsonl", "w") as f:\n        pass',
                'import os\n        out_file = "data/unified/youtube.jsonl"\n        tmp_file = out_file + ".tmp"\n        with open(tmp_file, "w") as f:\n            pass\n        if os.path.exists(tmp_file):\n            os.replace(tmp_file, out_file)'
            )
            
        if new_content != content:
            with open(c, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Patched {c}')
        else:
            print(f'No match in {c}')
