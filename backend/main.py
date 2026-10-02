import sys
import os
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from fastapi import FastAPI, HTTPException
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from backend.schema.user_input_schema import User
from backend.Agent.agents import yt_agent, comparison_agent_, create_retriever
from backend.youtube.ytID import extract_video_id
from backend.youtube.ytTranscript import yt_transcript


app = FastAPI(title="Video Intelligence Research Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
def home():
    return {'message': 'This is Video-Intelligence-Research-Agent'}

@app.get('/health')
def health_check():
    return {'status': 'OK'}

@app.get('/agentRun')
def run_info():
    return {
        'status': 'online',
        'endpoint': '/agentRun',
        'message': 'This endpoint accepts POST requests with a JSON body: {"yt_url": "https://www.youtube.com/watch?v=..."}'
    }


@app.post("/agentRun")
def run(user: User):

    question = (
        user.question.strip()
        if user.question and user.question.strip()
        else None
    )

    # =====================================================
    # VIDEO 1 — REQUIRED
    # =====================================================

    video_url = str(user.yt_url).strip()

    video_id = extract_video_id(video_url)

    print("VIDEO 1 URL:", video_url)
    print("VIDEO 1 ID:", video_id)

    if not video_id:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid YouTube video URL: {video_url}"
        )

    # =====================================================
    # VIDEO 2 — OPTIONAL
    # =====================================================

    video2_id = None

    if user.yt2_url:

        video2_url = str(user.yt2_url).strip()

        video2_id = extract_video_id(video2_url)

        print("VIDEO 2 URL:", video2_url)
        print("VIDEO 2 ID:", video2_id)

        if not video2_id:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid second YouTube video URL: {video2_url}"
            )

    # =====================================================
    # FETCH TRANSCRIPT 1
    # =====================================================

    transcript = yt_transcript(video_id)

    if not transcript:
        raise HTTPException(
            status_code=404,
            detail=(
                "No transcript available for this video "
                "(disabled, private, or not found)"
            )
        )

    # =====================================================
    # SINGLE VIDEO MODE
    # =====================================================

    if video2_id is None:

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
                "video_transcript": result.get(
                    "video_transcript", ""
                ),
                "summary": result.get(
                    "summary", ""
                ),
                "key_points": result.get(
                    "KeyPoints", []
                ),
                "claims": result.get(
                    "claims", []
                ),
                "fact_check": result.get(
                    "fact_check", []
                ),
                "topics": result.get(
                    "topics", []
                ),
                "references": result.get(
                    "references", []
                ),
                "answer": result.get(
                    "answer", ""
                )
            }

        except Exception as e:

            err_msg = str(e)

            if (
                "429" in err_msg
                or "rate_limit" in err_msg.lower()
                or "tpm" in err_msg.lower()
            ):
                raise HTTPException(
                    status_code=429,
                    detail=(
                        "Groq API rate limit reached. "
                        "Please wait and try again."
                    )
                )

            raise HTTPException(
                status_code=500,
                detail=f"Agent execution error: {err_msg}"
            )

    # =====================================================
    # VIDEO 2 TRANSCRIPT
    # =====================================================

    transcript2 = yt_transcript(video2_id)

    if not transcript2:
        raise HTTPException(
            status_code=404,
            detail=(
                "No transcript available for the second video "
                "(disabled, private, or not found)"
            )
        )

    # =====================================================
    # COMPARISON MODE
    # =====================================================

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

        result2 = comparison_agent_.invoke(
            {
                "transcript_a": transcript,
                "transcript_b": transcript2,
                "claims_a": [],
                "claims_b": [],
                "topics_a": [],
                "topics_b": [],
                "similarities": [],
                "differences": [],
                "contradictions": [],
                "claim_comparison": [],
                "claims_to_fact_check": [],
                "fact_check_results": []
            }
        )

        return {
            "video_transcript": result.get(
                "video_transcript", ""
            ),
            "summary": result.get(
                "summary", ""
            ),
            "key_points": result.get(
                "KeyPoints", []
            ),
            "claims": result.get(
                "claims", []
            ),
            "fact_check": result.get(
                "fact_check", []
            ),
            "topics": result.get(
                "topics", []
            ),
            "references": result.get(
                "references", []
            ),
            "answer": result.get(
                "answer", ""
            ),

            "claims_a": result2.get(
                "claims_a", []
            ),
            "claims_b": result2.get(
                "claims_b", []
            ),
            "topics_a": result2.get(
                "topics_a", []
            ),
            "topics_b": result2.get(
                "topics_b", []
            ),
            "similarities": result2.get(
                "similarities", []
            ),
            "differences": result2.get(
                "differences", []
            ),
            "contradictions": result2.get(
                "contradictions", []
            ),
            "claim_comparison": result2.get(
                "claim_comparison", []
            ),
            "claims_to_fact_check": result2.get(
                "claims_to_fact_check", []
            ),
            "fact_check_results": result2.get(
                "fact_check_results", []
            )
        }

    except Exception as e:

        err_msg = str(e)

        if (
            "429" in err_msg
            or "rate_limit" in err_msg.lower()
            or "tpm" in err_msg.lower()
        ):
            raise HTTPException(
                status_code=429,
                detail=(
                    "Groq API rate limit reached. "
                    "Please wait and try again."
                )
            )

        raise HTTPException(
            status_code=500,
            detail=f"Agent execution error: {err_msg}"
        )



if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
    )