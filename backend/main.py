import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from fastapi import FastAPI, HTTPException
import uvicorn
from backend.schema.user_input_schema import User
from backend.Agent.agents import yt_agent, create_retriever
from backend.youtube.ytID import extract_video_id
from backend.youtube.ytTranscript import yt_transcript


app = FastAPI(title="Video Intelligence Research Agent")

@app.get('/')
def home():
    return {'message': 'This is Video-Intelligence-Research-Agent'}

@app.get('/health')
def health_check():
    return {'status': 'OK'}


@app.post('/agentRun')
def run(user: User):
    question = user.question.strip() if user.question and user.question.strip() else None
    video_url = str(user.yt_url)
    video_id = extract_video_id(video_url)

    if not video_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube video URL"
        )
    
    transcript = yt_transcript(video_id)

    if not transcript:
        raise HTTPException(
            status_code=404,
            detail="No transcript available for this video (disabled, private, or not found)"
        )

    try:
        retriever = create_retriever(transcript)

        result = yt_agent.invoke(
            {
                "video_transcript": transcript,
                "summary": "",
                "KeyPoints": [],
                "claims": [],
                "fact_check": [],
                "topics": [],
                "references": [],
                "question": question,
                "context": "",
                "answer": "",
                "retriever": retriever
            }
        )

        return {
            "video_transcript": result.get("video_transcript", ""),
            "summary": result.get("summary", ""),
            "key_points": result.get("KeyPoints", []),
            "claims": result.get("claims", []),
            "fact_check": result.get("fact_check", []),
            "topics": result.get("topics", []),
            "references": result.get("references", []),
            "answer": result.get("answer", "")
        }
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg or "rate_limit" in err_msg.lower() or "tpm" in err_msg.lower():
            raise HTTPException(
                status_code=429,
                detail="Groq API rate limit reached (Tokens Per Minute limit exceeded). Retried multiple times. Please wait 10 seconds and try again."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution error: {err_msg}"
        )



if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
