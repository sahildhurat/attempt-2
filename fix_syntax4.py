import py_compile
files = ['scripts/collectors/youtube.py', 'scripts/collectors/appstore.py']
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    content = content.replace('f.write(json.dumps(u, default=str)\n    if os.path.exists(tmp_file):', 'f.write(json.dumps(u, default=str) + "\\n")\n    if os.path.exists(tmp_file):')
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
        
    try:
        py_compile.compile(f, doraise=True)
        print(f'{f} OK')
    except Exception as e:
        print(f'{f} ERROR: {e}')
