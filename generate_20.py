import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.append(os.path.abspath('scripts/collectors'))
from help_community_v2 import fetch_and_parse, get_session

session = get_session()
tids = ['378802685', '87305', '286144710', '319380955', '367230169', '455977807', '308953776', '393816022', '311908848', '3478886', '396762620', '470020683', '155282398', '232641836', '142117', '99679', '15395567', '153909723', '205230734', '262560240']

with open('reprove_20_threads.txt', 'w', encoding='utf-8') as f:
    for tid in tids:
        status, msg, units = fetch_and_parse(session, tid)
        if status == 'SUCCESS':
            op = [u for u in units if not u['is_reply']][0]
            replies = [u for u in units if u['is_reply']]
            thread_str = f"--- THREAD {tid} ---\nTitle: {op['context']}\n[OP | Author: {op.get('author_name', 'Unknown')} | Badge: {op.get('author_badge_level', 'None')}]\n{op['text']}\n"
            for j, r in enumerate(replies):
                flags = []
                if r.get('author_is_expert'): flags.append('EXPERT')
                if r.get('is_recommended'): flags.append('RECOMMENDED')
                flag_str = f" | Flags: {', '.join(flags)}" if flags else ""
                thread_str += f"\n[REPLY {j+1} | Author: {r.get('author_name', 'Unknown')} | Badge: {r.get('author_badge_level', 'None')}{flag_str} | Parent: {r.get('parent_id')}]\n{r['text']}\n"
            f.write(thread_str + '\n')
            print(f'Fetched {tid}: {len(replies)} replies')
        else:
            print(f'Failed {tid}: {status} - {msg}')
