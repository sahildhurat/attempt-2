import sys

def find_block(filepath, block_id):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='utf-16') as f:
            content = f.read()
    
    blocks = content.split('================================================================================')
    for block in blocks:
        block = block.strip()
        if block.startswith(block_id):
            with open(r"d:\Attempt 2\scripts\found_block.txt", "w", encoding='utf-8') as out:
                out.write(block)
            return
            
    print("Not found")

if __name__ == "__main__":
    find_block(r"d:\Attempt 2\data\raw\reddit_assisted\conversations.txt.txt", "S031 |")
