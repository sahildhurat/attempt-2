import json
import re

def extract_replies(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    replies = []
    
    def walk(node, path=""):
        if isinstance(node, list):
            # A typical message node might have a string ID and a string HTML text.
            # In the dump above: reply[0][3] is text, reply[0][0][0] is ID. 
            # Or reply is a list where index 3 is text.
            # Let's just find any list where length >= 4, index 3 is a string with <div> or <br> or length > 20
            # and index 0 might be an array or string.
            if len(node) >= 4 and isinstance(node[3], str) and ('<div' in node[3] or '<br' in node[3] or len(node[3]) > 10):
                # Is this a reply?
                text = node[3]
                # Try to find ID
                msg_id = None
                if isinstance(node[0], list) and len(node[0]) > 0:
                    msg_id = node[0][0]
                elif isinstance(node[0], str):
                    msg_id = node[0]
                
                # Check if it's the OP or a reply
                # OP usually has the title nearby or is the first one.
                # Let's just collect all message-like lists
                replies.append({"id": msg_id, "text": text, "path": path})
            
            for i, item in enumerate(node):
                walk(item, f"{path}[{i}]")
        elif isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}[{k}]")
                
    walk(data)
    
    # OP is usually the first, let's just print all found:
    print(f"\n--- {file_path} ---")
    for r in replies:
        print(f"Msg ID: {r['id']}, Length: {len(r['text'])}, Path: {r['path']}")

extract_replies("thread_367230169_data.json")
extract_replies("thread_319380955_data.json")
