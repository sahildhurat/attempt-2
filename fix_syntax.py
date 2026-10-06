import os
files = ['scripts/collectors/youtube.py', 'scripts/collectors/stackexchange.py', 'scripts/collectors/hn.py', 'scripts/collectors/appstore.py']
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    content = content.replace('        except Exception as e:\n        if "RATE_LIMITED"', '        except Exception as e:\n            if "RATE_LIMITED"')
    content = content.replace('        if isinstance(e, requests.exceptions.RequestException):\n        return "NETWORK", None', '        if isinstance(e, requests.exceptions.RequestException):\n            return "NETWORK", None')
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

hc = 'scripts/collectors/help_community.py'
with open(hc, 'r', encoding='utf-8') as file:
    content = file.read()
content = content.replace('f.write(json.dumps(u)\n    if os.path.exists(tmp_file):\n        os.replace(tmp_file, out_file) + "\\n")', 'f.write(json.dumps(u) + "\\n")\n    if os.path.exists(tmp_file):\n        os.replace(tmp_file, out_file)')
with open(hc, 'w', encoding='utf-8') as file:
    file.write(content)

ps = 'scripts/collectors/playstore.py'
with open(ps, 'r', encoding='utf-8') as file:
    content = file.read()
content = content.replace('f.write(json.dumps(u, default=str)\n    if os.path.exists(tmp_file):\n        os.replace(tmp_file, out_file) + "\\n")', 'f.write(json.dumps(u, default=str) + "\\n")\n    if os.path.exists(tmp_file):\n        os.replace(tmp_file, out_file)')
with open(ps, 'w', encoding='utf-8') as file:
    file.write(content)
