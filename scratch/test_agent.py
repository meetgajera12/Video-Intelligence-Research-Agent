import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from youtube.ytID import extract_video_id
from youtube.ytTranscript import yt_transcript
from schema.user_input_schema import User
from Agent.agents import yt_agent, create_retriever

print("=== Testing URL Extraction ===")
urls = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://www.youtube.com/shorts/dQw4w9WgXcQ",
    "https://youtu.be/dQw4w9WgXcQ"
]
for u in urls:
    vid_id = extract_video_id(u)
    print(f"URL: {u} -> ID: {vid_id}")
    assert vid_id == "dQw4w9WgXcQ"

print("\n=== Testing User Schema Validation ===")
user_no_q = User(yt_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
print("User with no question parsed successfully:", user_no_q.yt_url, "| Question:", repr(user_no_q.question))

print("\n=== Testing Agent Execution ===")
sample_transcript = "Python is an interpreted high-level general-purpose programming language created by Guido van Rossum in 1991."
retriever = create_retriever(sample_transcript)

res = yt_agent.invoke({
    "video_transcript": sample_transcript,
    "summary": "",
    "KeyPoints": [],
    "claims": [],
    "fact_check": [],
    "topics": [],
    "references": [],
    "question": "Who created Python?",
    "context": "",
    "answer": "",
    "retriever": retriever
})

print("Agent execution finished successfully!")
print("Keys returned:", list(res.keys()))
print("Answer:", res.get("answer"))
print("Summary length:", len(res.get("summary", "")))
