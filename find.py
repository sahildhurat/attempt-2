import re
with open('test_thread.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Try to find the question content within WIZ_global_data or similar JSON blob, or just clean the HTML
import html as html_lib
matches = re.findall(r'window\.WIZ_global_data\s*=\s*(\{.*?\});', html)
if matches:
    print("Found WIZ_global_data!")
    # the JSON string has a lot of escaping, let's just find the text in it
    text_matches = re.findall(r'"([^"]*music[^"]*family[^"]*)"', matches[0], re.IGNORECASE)
    print("Text matches:", text_matches)

# Let's also look for standard text nodes
text_nodes = re.findall(r'>([^<]+)<', html)
for text in text_nodes:
    if 'music' in text.lower():
        print("Found in text node:", text.strip())
