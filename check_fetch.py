import requests
import re
r = requests.get('https://support.google.com/photos/thread/440606295?hl=en')
print(r.status_code)
print('match?', bool(re.search(r"var thread_view='(.*?)';var ", r.text)))
