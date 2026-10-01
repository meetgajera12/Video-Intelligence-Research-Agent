import time
import re
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
from langchain_core.prompts import ChatPromptTemplate
from sklearn.metrics.pairwise import cosine_similarity
from typing import TypedDict, Annotated, Any, List, Dict
import operator
from dotenv import load_dotenv
from youtube.ytTranscript import yt_transcript
from backend.schema.agent_schema import Summary, Key_points, FactCheckResult, Topics, ReferenceResult, QueAns, Claims, ComparisonResult
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

# state2
class ComparisonState(TypedDict, total=False):
    # Transcripts
    transcript_a: str
    transcript_b: str
    # Claims
    claims_a: List[Dict[str, Any]]
    claims_b: List[Dict[str, Any]]
    # Topics
    topics_a: List[str]
    topics_b: List[str]
    # Comparison
    similarities: List[Dict[str, Any]]
    differences: List[Dict[str, Any]]
    contradictions: List[Dict[str, Any]]
    claim_comparison: List[Dict[str, Any]]
    # Claims that actually need verification
    claims_to_fact_check: List[Dict[str, Any]]
    # Fact checking
    fact_check_results: List[Dict[str, Any]]
    


#==================== Agents ====================#


#-------main agent-------#

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
You are a factual claim extraction system.

Your task is to extract ONLY objectively verifiable factual claims that are explicitly stated in the provided transcript.

A factual claim is a statement that asserts something about a person, organization, event, object, process, scientific fact, historical fact, technical concept, numerical value, relationship, or other real-world matter that could potentially be verified using reliable external evidence.

STRICT RULES:

1. Extract only claims explicitly stated in the transcript.
   - Do not infer, interpret, assume, or complete missing information.
   - Do not use your own knowledge to create or modify claims.

2. The extracted claim must be a complete factual statement.
   - Preserve the meaning of the original statement.
   - Rewrite only enough to make the claim clear and self-contained.
   - Do not change its factual meaning.

3. Extract statements that can be independently verified.
   Examples of suitable claims include statements about:
   - who created, founded, hosted, developed, or discovered something
   - dates, locations, quantities, measurements, or statistics
   - historical events
   - scientific or technical facts
   - properties or behavior of systems, products, technologies, or organizations
   - relationships between entities or events

4. DO NOT extract:
   - opinions or subjective judgments
   - predictions or speculation
   - recommendations
   - personal preferences
   - rhetorical statements
   - questions
   - commands or instructions
   - advertisements or promotional statements
   - calls to action
   - greetings or conversational filler
   - statements describing what the speaker is about to explain
   - claims that exist only as questions
   - unsupported interpretations or conclusions you derive yourself

5. Be especially careful with subjective language.
   Statements containing words such as "best", "worst", "amazing", "excellent", "easy", "difficult", "important", or "great" are usually opinions unless the transcript provides a clearly measurable factual basis.

6. Do not treat the following as factual claims merely because they contain factual-looking words:
   - video titles
   - section headings
   - speaker introductions
   - descriptions of the video itself
   - statements about what the video will cover
   - promotional descriptions

7. Do not combine multiple unrelated statements into one claim.
   If the transcript contains several independently verifiable facts, extract them as separate claims.

8. Do not duplicate claims.
   If the same fact appears multiple times, extract it only once.

9. Keep claims concise.
   Remove unnecessary wording while preserving the exact factual meaning.

10. Do not correct the speaker.
    If the transcript contains a factual statement that may be false, questionable, outdated, or controversial, still extract it if it satisfies the rules above.
    Verification happens later. Your job is extraction, not fact-checking.

11. If a statement is ambiguous and cannot reasonably be understood as a specific factual assertion, do not extract it.

12. If there are no qualifying factual claims, return an empty list.

OUTPUT REQUIREMENT:

Return ONLY the structured output defined by the provided schema.
Do not include explanations, commentary, headings, Markdown, or additional text outside the schema.

TRANSCRIPT:

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


# --- graph ---

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


#-------comparison agent-------#

# claim extractor agent

def extract_claims_from_transcript(transcript: str) -> list[str]:

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=4000,
        chunk_overlap=500
    )

    chunks = splitter.split_text(transcript)

    all_claims = []

    for chunk in chunks:

        response = model.with_structured_output(
            Claims,
            method="json_schema",
            strict=False
        ).invoke(
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
- Keep each claim short and factual.
- If there are no factual claims, return an empty list.

Transcript chunk:

{chunk}
"""
        )

        all_claims.extend(response.claims)

    return all_claims



def claim_extractor_a(state: ComparisonState):

    claims = extract_claims_from_transcript(
        state["transcript_a"]
    )

    return {
        "claims_a": claims
    }

def claim_extractor_b(state: ComparisonState):

    claims = extract_claims_from_transcript(
        state["transcript_b"]
    )

    return {
        "claims_b": claims
    }


# topic extractor agent

def topic_agent_a(state: ComparisonState):

    temp_state = {
        "video_transcript": state["transcript_a"]
    }

    result = topic_agent(temp_state)

    return {
        "topics_a": result["topics"]
    }


def topic_agent_b(state: ComparisonState):

    temp_state = {
        "video_transcript": state["transcript_b"]
    }

    result = topic_agent(temp_state)

    return {
        "topics_b": result["topics"]
    }


# comparison agent

comparison_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are a video comparison analysis agent.

You are given already-extracted claims and topics from two videos.

Your job is ONLY to compare them.

Do not extract new claims.
Do not extract new topics.
Do not use outside knowledge.
Do not invent information.

Analyze the provided information and produce:

1. similarities
2. differences
3. claim_comparison
4. contradictions
5. claims_to_fact_check

CLAIM COMPARISON:

Only compare claims that are materially related.

Use these relationship types where applicable:

- supporting
- similar
- different
- contradictory
- unrelated

Do not create a comparison merely because both videos discuss the same broad subject.

CONTRADICTIONS:

A contradiction exists only when the factual assertions of Video A
and Video B genuinely conflict under the same context.

A difference in:
- wording
- examples
- emphasis
- scope
- level of detail

is NOT automatically a contradiction.

CLAIMS TO FACT CHECK:

Include only claims where independent external verification
would be useful.

If no claims require fact checking, return an empty list.

SIMILARITIES:

Identify meaningful similarities between the videos.

DIFFERENCES:

Identify meaningful differences between the videos.

IMPORTANT:

Return empty lists when no items exist.

Do not omit fields.
Return only the structured output.
"""
    ),
    (
        "human",
        """
VIDEO A

Topics:
{topics_a}

Claims:
{claims_a}


VIDEO B

Topics:
{topics_b}

Claims:
{claims_b}
"""
    )
])


def comparison_agent(state: ComparisonState):

    structured_llm = model.with_structured_output(
        ComparisonResult,
        method="function_calling",
        strict=False
    )

    result = structured_llm.invoke(
        comparison_prompt.format_messages(
            topics_a=state.get("topics_a", []),
            claims_a=state.get("claims_a", []),
            topics_b=state.get("topics_b", []),
            claims_b=state.get("claims_b", [])
        )
    )

    return {
        # Original extracted data
        "claims_a": state.get("claims_a", []),
        "claims_b": state.get("claims_b", []),
        "topics_a": state.get("topics_a", []),
        "topics_b": state.get("topics_b", []),

        # Comparison output
        "similarities": result.similarities,
        "differences": result.differences,

        "claim_comparison": [
            item.model_dump()
            for item in result.claim_comparison
        ],

        "contradictions": [
            item.model_dump()
            for item in result.contradictions
        ],

        "claims_to_fact_check": result.claims_to_fact_check
    }



# --- graph ---

comparison = StateGraph(ComparisonState)

comparison.add_node("claim_extractor_a", claim_extractor_a)
comparison.add_node("claim_extractor_b",claim_extractor_b)
comparison.add_node("topic_agent_a",topic_agent_a)
comparison.add_node("topic_agent_b",topic_agent_b)
comparison.add_node("comparison_agent",comparison_agent)
comparison.add_node("comparison_report",comparison_report)

comparison.add_edge(START,"claim_extractor_a")
comparison.add_edge(START,"claim_extractor_b")
comparison.add_edge(START,"topic_agent_a")
comparison.add_edge(START,"topic_agent_b")
comparison.add_edge("claim_extractor_a","comparison_agent")
comparison.add_edge("claim_extractor_b","comparison_agent")
comparison.add_edge("topic_agent_a","comparison_agent")
comparison.add_edge("topic_agent_b","comparison_agent")
comparison.add_edge("comparison_agent","comparison_report")
comparison.add_edge("comparison_report",END)

comparison_agent_ = comparison.compile()
