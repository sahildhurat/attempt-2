import json

def analyze_thread(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"--- Analyzing {file_path} ---")
    
    # 1. Thread OP
    op = data[1]
    tid = op[0][0]
    title = op[8]
    op_body = op[12]
    category = op[21]
    print(f"Thread ID: {tid}")
    print(f"Title: {title}")
    print(f"Category: {category}")
    print(f"OP Body Length: {len(op_body) if op_body else 0}")
    
    # 2. OP Author
    op_author = data[3]
    print(f"OP Author Name: {op_author[0][0] if op_author else 'N/A'}")
    
    # 3. Replies
    print("Replies:")
    # Replies seem to be in data[16][2] or similar. Let's write a recursive function to find all objects that look like messages
    
    def find_messages(node, messages):
        if isinstance(node, list):
            # A message object seems to have a specific shape: [ [msg_id, ..., parent_id, ...], null, author_id, "text", ... ]
            # Let's check if node looks like a message
            if len(node) > 15 and isinstance(node[0], list) and len(node[0]) >= 4 and isinstance(node[0][0], int) and isinstance(node[3], str) and len(node[3]) > 0:
                # Check if it has a parent ID that matches thread ID
                if node[0][2] == tid:
                    messages.append(node)
                    return # Don't recurse into the message itself to avoid finding sub-messages as the same thing if any
            
            for child in node:
                find_messages(child, messages)
                
    replies = []
    find_messages(data, replies)
    
    # OP might be caught in find_messages if we search the whole data, so we filter it out
    replies = [r for r in replies if r[0][0] != tid]
    
    unique_replies = {}
    for r in replies:
        unique_replies[r[0][0]] = r
        
    replies = list(unique_replies.values())
    
    print(f"Found {len(replies)} unique replies.")
    for i, r in enumerate(replies[:3]):
        msg_id = r[0][0]
        parent_id = r[0][2]
        text = r[3]
        
        # Try to find author name for reply
        # Author info is often at index 5 or 1 or something, let's see what is at index 1 and 2
        # Actually, author info might be in a separate array or embedded. 
        print(f"  Reply {i+1}: ID={msg_id}, Parent={parent_id}, TextLen={len(text)}")
        
if __name__ == "__main__":
    analyze_thread("thread_367230169_data.json")
    print()
    analyze_thread("thread_319380955_data.json")
