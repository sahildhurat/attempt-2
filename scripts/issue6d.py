import json
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

DetectorFactory.seed = 0

def get_dropped_yt():
    dropped = []
    with open("data/unified/youtube.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            u = json.loads(line)
            text = u.get("text", "")
            if not text: continue
            lang = u.get("lang")
            if not lang:
                try: lang = detect(text)
                except LangDetectException: lang = "unknown"
            if lang != "en":
                dropped.append(text)
                if len(dropped) >= 20:
                    break
    
    with open("issue6d_output.txt", "w", encoding="utf-8") as out:
        out.write("--- 20 Dropped YouTube Units ---\n")
        for i, t in enumerate(dropped):
            out.write(f"Unit {i+1}: {repr(t)}\n")

if __name__ == "__main__":
    get_dropped_yt()
