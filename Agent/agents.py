import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_tavily import TavilySearch
from langchain_community.vectorstores import FAISS
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langchain_core.messages import SystemMessage, HumanMessage
from sklearn.metrics.pairwise import cosine_similarity
from typing import TypedDict, Annotated, Any
import operator
from dotenv import load_dotenv
from youtube.ytTranscript import yt_transcript
from schema.agent_schema import Summary, Key_points, FactCheckResult, Topics, ReferenceResult, QueAns, Claims

load_dotenv()



# embedding model
embedding = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

# retriever
def create_retriever(transcript: str):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = splitter.create_documents([transcript])


    vector_store = FAISS.from_documents(
        chunks,
        embedding
    )

    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
    )


import time
import re

# LLM model
model = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    max_retries=5,
    reasoning_effort="low"
)

def create_structured_chain(pydantic_model):
    return model.with_structured_output(
        pydantic_model,
        method="json_schema"
    )

def invoke_with_retry(runnable, prompt_input, max_attempts=5):
    for attempt in range(1, max_attempts + 1):
        try:
            return runnable.invoke(prompt_input)
        except Exception as e:
            err_str = str(e)
            if ("429" in err_str or "rate_limit" in err_str.lower() or "tpm" in err_str.lower()) and attempt < max_attempts:
                match = re.search(r"try again in ([\d\.]+)s", err_str, re.IGNORECASE)
                wait_time = float(match.group(1)) + 2.0 if match else (5.0 * attempt)
                print(f"[RateLimit 429] Waiting {wait_time:.1f}s before retry (attempt {attempt}/{max_attempts})...")
                time.sleep(wait_time)
            else:
                raise e


# search tool
search = TavilySearch(
    max_results=3
)

# state
class State(TypedDict):
    video_transcript : str
    summary : str
    KeyPoints : list[str]
    claims: Annotated[list[str], operator.add]
    fact_check : list
    topics : list[str]
    references : list
    question : str | None
    context : str
    answer  : str
    retriever: Any


#==================== Agents ====================#


# que-ans agent

def QueAns_agent(state: State) -> dict:
    question = state["question"]
    retriever = state["retriever"]

    if not question:
        return {
            "context": "",
            "answer": ""
        }

    docs = retriever.invoke(question)

    context = "\n\n".join(
        doc.page_content
        for doc in docs
    )

    chain = create_structured_chain(QueAns)
    
    response = invoke_with_retry(
        chain,
        [
            SystemMessage(
                content=f"""
You are a helpful QA assistant.

Answer ONLY from the provided video transcript context.

Do not use outside knowledge.

If the answer is not available in the context,
say that the information is not available in the video.

Give answers in 5-6 lines.

Context:
{context}
"""
            ),
            HumanMessage(
                content=f"Question: {question}"
            )
        ]
    )

    return {
        "context": context,
        "answer": getattr(response, "answer", "") if response else ""
    }


# summary agent

def summary_agent(state: State) -> dict:
    transcript = state.get("video_transcript", "")[:12000]

    chain = create_structured_chain(Summary)
    response = invoke_with_retry(
        chain,
        [
            SystemMessage(
                content=f"""
                You are a helpful summary assistant.

                Create a detailed but concise summary of the YouTube video transcript.

                Use ONLY information present in the transcript.
                Do not add outside information.

                Transcript:
                {transcript}
                """
            )
        ]
    )

    return {'summary': getattr(response, "summary", "") if response else ""}


# key point extractor agent

def KeyPoint_agent(state: State) -> dict:
    transcript = state.get("video_transcript", "")[:12000]

    chain = create_structured_chain(Key_points)
    response = invoke_with_retry(
        chain,
        [
            SystemMessage(
                content=f"""
                You are a key points extractor agent from provided youtube video transcripts.

                refere only provided transcrip. if you dont find any key points just say: 'can't find any usefull key points from the video.'

                Transcript:
                {transcript}
                """
            )
        ]
    )

    return {'KeyPoints': getattr(response, "KeyPoints", []) if response else []}


# splitting

def split_transcript_for_claims(state: State):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=8000,
        chunk_overlap=500
    )

    chunks = splitter.split_text(
        state["video_transcript"]
    )[:3]  # Limit to max 3 chunks to prevent exceeding rate limits

    return [
        Send(
            "claim_extractor",
            {
                "video_transcript": chunk
            }
        )
        for chunk in chunks
    ]


# claim extracting agent

def claim_chunk_agent(state: State) -> dict:
    chain = create_structured_chain(Claims)
    
    response = invoke_with_retry(
        chain,
        f"""
Extract objectively verifiable factual claims from this transcript
chunk.

Rules:
- Extract only claims explicitly stated in the text.
- Do not add outside knowledge.
- Do not extract opinions.
- Do not extract questions.
- Do not extract advertisements.
- Do not extract calls to action.
- Do not repeat the same claim.
- Keep each claim short and factual.
- If there are no factual claims, return an empty list.

Transcript chunk:

{state["video_transcript"]}

"""
    )

    return {
        "claims": getattr(response, "claims", []) if response else []
    }


# deduplication

def deduplicate_claims(state: State) -> dict:
    claims = state.get('claims', [])

    if len(claims) <= 1:
        return {'claims': claims}

    vectors = embedding.embed_documents(claims)

    unique_claims = []
    unique_vectors = []

    threshold = 0.85

    for claim, vector in zip(claims, vectors):

        if not unique_vectors:
            unique_claims.append(claim)
            unique_vectors.append(vector)
            continue

        similarities = cosine_similarity([vector], unique_vectors)[0]

        max_similarity = max(similarities)

        if max_similarity < threshold:
            unique_claims.append(claim)
            unique_vectors.append(vector)

    return {'claims': unique_claims}


# fact_check agent

def fact_checker(state: State) -> dict:
    results = []
    claims = state.get("claims", [])[:5]  # Process max 5 claims to respect rate limits
    if not claims:
        return {"fact_check": []}

    chain = create_structured_chain(FactCheckResult)

    for claim in claims:
        try:
            time.sleep(1)  # Pacing delay to avoid rate limits
            search_result = search.invoke({
                "query": claim
            })

            response = invoke_with_retry(
                chain,
                [
                    SystemMessage(
                        content="""
You are an expert fact checker.

Verify the provided claim using the external
search results.

Possible verdicts:

TRUE
FALSE
MISLEADING
UNVERIFIED

Rules:

- TRUE:
  Reliable evidence supports the claim.

- FALSE:
  Reliable evidence contradicts the claim.

- MISLEADING:
  The claim contains some truth but gives
  a misleading impression or lacks important context.

- UNVERIFIED:
  There isn't enough reliable evidence to determine
  whether the claim is true or false.

Do NOT rely on your internal knowledge when
the provided evidence is insufficient.

Prefer reliable sources such as:
- government websites
- official statistics
- scientific papers
- universities
- established news organizations
- primary sources

Claim:
"""
                        + str(claim)
                        + """

Search results:
"""
                        + str(search_result)
                        + f"""

"""
                    )
                ]
            )

            if response:
                if hasattr(response, "claims") and response.claims:
                    for item in response.claims:
                        results.append(item.model_dump() if hasattr(item, "model_dump") else item)
                elif hasattr(response, "model_dump"):
                    results.append(response.model_dump())
                elif isinstance(response, dict):
                    results.append(response)
        except Exception as e:
            print(f"Fact check error for claim '{claim}': {e}")

    return {
        "fact_check": results
    }


# topic extractor agent

def topic_agent(state: State) -> dict:
    transcript = state.get("video_transcript", "")[:12000]
    chain = create_structured_chain(Topics)
    
    try:
        response = invoke_with_retry(
            chain,
            [
                SystemMessage(
                    content=f"""
You are a topic extraction agent.

Extract important topics explicitly discussed in the transcript.

Rules:
- Return only topics explicitly mentioned or clearly discussed.
- Do not infer additional topics.
- Do not summarize the transcript.
- Do not return complete sentences.
- Do not return opinions.
- Do not return promotional content.
- Do not return generic topics such as YouTube, video, speaker, channel, or tutorial.
- Combine duplicate topics.
- Prefer specific technical/scientific concepts.
- If no meaningful topics exist, return an empty list.

Return the result using ONLY the provided structured schema.

Transcript:
{transcript}

"""
                )
            ]
        )
        return {
            "topics": getattr(response, "topics", []) or []
        }
    except Exception as e:
        print(f"Topic extraction error: {e}")
        return {"topics": []}


# reference agent

def reference_agent(state: State) -> dict:
    all_references = []
    topics = state.get("topics", [])[:3]  # Process max 3 topics to respect rate limits
    if not topics:
        return {"references": []}

    chain = create_structured_chain(ReferenceResult)

    for topic in topics:
        try:
            time.sleep(1)  # Pacing delay to avoid rate limits
            search_response = search.invoke({
                "query": topic
            })

            if isinstance(search_response, dict):
                results = search_response.get("results", [])
            elif isinstance(search_response, list):
                results = search_response
            else:
                results = []

            results = results[:3]

            if not results:
                continue

            results_text = "\n\n".join(
                f"""
                    Title: {result.get("title", "") if isinstance(result, dict) else getattr(result, "title", "")}
                    URL: {result.get("url", "") if isinstance(result, dict) else getattr(result, "url", "")}
                    Content: {str(result.get("content", "") if isinstance(result, dict) else getattr(result, "content", ""))[:800]}
                """
                for result in results
            )

            response = invoke_with_retry(
                chain,
                f"""
Find the best reliable references for this topic.

Topic:
{topic}

Search results:
{results_text}

Rules:
- Select only sources present in the search results.
- Do not invent URLs.
- Prefer official documentation, research papers,
  universities, government sources, textbooks,
  and reputable articles.
- Return the most relevant sources.
"""
            )

            if response and hasattr(response, "references") and response.references:
                for ref in response.references:
                    all_references.append(ref.model_dump() if hasattr(ref, "model_dump") else ref)
        except Exception as e:
            print(f"Reference search error for topic '{topic}': {e}")

    return {
        "references": all_references[:3]
    }


# --- building graph ---

g = StateGraph(State)

g.add_node("QueAns_agent", QueAns_agent)
g.add_node("summary_agent", summary_agent)
g.add_node('KeyPoint_agent', KeyPoint_agent)
g.add_node("claim_extractor", claim_chunk_agent)
g.add_node('deduplicate_claims',deduplicate_claims)
g.add_node("fact_checker", fact_checker)
g.add_node('topic_agent', topic_agent)
g.add_node('reference_agent', reference_agent)


g.add_edge(START, 'QueAns_agent')
g.add_edge('QueAns_agent',END)

g.add_edge(START,"summary_agent")
g.add_edge("summary_agent","KeyPoint_agent")
g.add_edge("KeyPoint_agent",END)

g.add_conditional_edges(START,split_transcript_for_claims)
g.add_edge('claim_extractor','deduplicate_claims')
g.add_edge('deduplicate_claims','fact_checker')
g.add_edge("fact_checker",END)

g.add_edge(START, 'topic_agent')
g.add_edge('topic_agent','reference_agent')
g.add_edge('reference_agent',END)


yt_agent = g.compile()