import bs4

with open('test_thread.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = bs4.BeautifulSoup(html, 'html.parser')
title = soup.title.string if soup.title else 'No Title'
print("TITLE:", title.replace(' - Google Photos Community', ''))

# In Google forums, the main post is usually a div with class "thread-question__payload" or similar
# Let's just find the first very long text block that's not a script.
texts = soup.find_all(string=True)
visible_texts = filter(lambda t: t.parent.name not in ['style', 'script', 'head', 'title', 'meta', '[document]'], texts)
clean_texts = [t.strip() for t in visible_texts if t.strip()]

# print the longest text blocks
clean_texts.sort(key=len, reverse=True)
for t in clean_texts[:3]:
    print("TEXT:", t.encode('ascii', 'ignore').decode('ascii'))
