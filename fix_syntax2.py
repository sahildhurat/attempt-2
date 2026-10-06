import os
import py_compile

with open('scripts/collectors/stackexchange.py', 'r', encoding='utf-8') as f: content = f.read()
content = content.replace('        except Exception as e:\n            if "RATE_LIMITED"', '        except Exception as e:\n            if "RATE_LIMITED" in str(e):\n                pass\n            if "RATE_LIMITED"')
with open('scripts/collectors/stackexchange.py', 'w', encoding='utf-8') as f: f.write(content)

with open('scripts/collectors/youtube.py', 'r', encoding='utf-8') as f: content = f.read()
content = content.replace('        except Exception as e:\n            if "RATE_LIMITED"', '        except Exception as e:\n            if "RATE_LIMITED" in str(e):\n                pass\n            if "RATE_LIMITED"')
with open('scripts/collectors/youtube.py', 'w', encoding='utf-8') as f: f.write(content)

with open('scripts/collectors/appstore.py', 'r', encoding='utf-8') as f: content = f.read()
content = content.replace('        except Exception as e:\n        if "RATE_LIMITED"', '        except Exception as e:\n            if "RATE_LIMITED" in str(e):\n                pass')
with open('scripts/collectors/appstore.py', 'w', encoding='utf-8') as f: f.write(content)

with open('scripts/collectors/hn.py', 'r', encoding='utf-8') as f: content = f.read()
content = content.replace('f.write(json.dumps(u, default=str)\n    if os.path.exists', 'f.write(json.dumps(u, default=str) + "\\n")\n    if os.path.exists')
with open('scripts/collectors/hn.py', 'w', encoding='utf-8') as f: f.write(content)

for c in ['scripts/collectors/help_community.py', 'scripts/collectors/playstore.py', 'scripts/collectors/stackexchange.py', 'scripts/collectors/appstore.py', 'scripts/collectors/youtube.py', 'scripts/collectors/hn.py']:
    with open(c, 'r', encoding='utf-8') as f: content = f.read()
    content = content.replace('    import os\n    out_file = ', '    out_file = ')
    with open(c, 'w', encoding='utf-8') as f: f.write(content)
    try:
        py_compile.compile(c, doraise=True)
        print(f'{c} OK')
    except Exception as e:
        print(f'{c} ERROR: {e}')
