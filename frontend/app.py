import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/agentRun"

st.set_page_config(
    page_icon="🤝",
    page_title="Video Intelligence Agent",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- Session State --------------------

if "video_analyzed" not in st.session_state:
    st.session_state.video_analyzed = False

if "video_url" not in st.session_state:
    st.session_state.video_url = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "result" not in st.session_state:
    st.session_state.result = {}


def analyze_video(video_url):
    """Run the full video analysis and store the result in session state."""
    with st.spinner("Analyzing transcript & running research agents..."):
        try:
            response = requests.post(
                API_URL,
                json={
                    "yt_url": video_url,
                    "question": None,
                },
                timeout=300,
            )

            if response.status_code == 200:
                st.session_state.video_url = video_url
                st.session_state.result = response.json()
                st.session_state.video_analyzed = True

                # New video = new conversation
                st.session_state.chat_history = []

                st.rerun()

            else:
                st.error(
                    f"API Error {response.status_code}: "
                    f"{response.text}"
                )

        except requests.exceptions.ConnectionError:
            st.error(
                "FastAPI server is not running. "
                "Please start backend/main.py first."
            )
        except requests.exceptions.Timeout:
            st.error("The request timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")


def ask_question(question):
    """Send a Q&A question to the backend."""
    try:
        response = requests.post(
            API_URL,
            json={
                "yt_url": st.session_state.video_url,
                "question": question,
            },
            timeout=300,
        )

        if response.status_code == 200:
            return response.json().get("answer", "")

        st.error(
            f"API Error {response.status_code}: "
            f"{response.text}"
        )
        return None

    except requests.exceptions.ConnectionError:
        st.error(
            "FastAPI server is not running. "
            "Please start backend/main.py first."
        )
        return None

    except requests.exceptions.Timeout:
        st.error("The request timed out. Please try again.")
        return None

    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {e}")
        return None


# -------------------- Sidebar --------------------

st.sidebar.text_input(
    "YouTube Video URL",
    key="video_url_input",
    placeholder="https://www.youtube.com/watch?v=...",
)

if st.sidebar.button("🔍 Analyze Video", use_container_width=True):
    video_url = st.session_state.video_url_input.strip()

    if not video_url:
        st.warning("Please enter a valid YouTube video URL.")
    else:
        analyze_video(video_url)

if st.session_state.video_analyzed:
    if st.sidebar.button("🗑️ Clear Analysis", use_container_width=True):
        st.session_state.video_analyzed = False
        st.session_state.video_url = ""
        st.session_state.video_url_input = ""
        st.session_state.result = {}
        st.session_state.chat_history = []
        st.rerun()


# -------------------- Main UI --------------------

st.title("🎥 Video Intelligence Research Agent")

if not st.session_state.video_analyzed:
    st.info(
        "👈 Enter a YouTube URL in the sidebar and click "
        "**Analyze Video** to begin."
    )
    st.stop()


result = st.session_state.result

video_transcript = result.get("video_transcript", "")
summary = result.get("summary", "")
key_points = result.get("key_points", [])
claims = result.get("claims", [])
fact_check = result.get("fact_check", [])
topics = result.get("topics", [])
references = result.get("references", [])


# -------------------- Tabs --------------------

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    [
        "📜 Transcript",
        "📝 Summary",
        "🔑 Key Points",
        "✅ Claims & Fact Check",
        "🏷️ Topics",
        "📚 References",
        "💬 Q&A",
    ]
)


# -------------------- Transcript --------------------

with tab1:
    st.header("YouTube Video Transcript")
    st.write(
        video_transcript
        if video_transcript
        else "No transcript available."
    )


# -------------------- Summary --------------------

with tab2:
    st.header("Summary")
    st.write(
        summary
        if summary
        else "No summary available."
    )


# -------------------- Key Points --------------------

with tab3:
    st.header("Key Points")

    if key_points:
        for point in key_points:
            st.markdown(f"- {point}")
    else:
        st.info("No key points found.")


# -------------------- Claims & Fact Check --------------------

with tab4:
    st.header("Claims & Fact Check")

    if claims:
        st.subheader("Extracted Factual Claims")

        for claim in claims:
            st.markdown(f"- {claim}")
    else:
        st.info(
            "No explicit factual claims extracted from the video."
        )

    if fact_check:
        st.subheader("Fact Check Verification Results")

        for fact in fact_check:
            if isinstance(fact, dict):
                verdict = fact.get("verdict", "UNKNOWN")

                if verdict == "TRUE":
                    color = "green"
                elif verdict == "FALSE":
                    color = "red"
                else:
                    color = "orange"

                st.markdown(
                    f"**Claim:** {fact.get('claim', '')}"
                )
                st.markdown(
                    f"**Verdict:** :{color}[{verdict}]"
                )

                if fact.get("explanation"):
                    st.markdown(
                        f"**Explanation:** "
                        f"{fact.get('explanation')}"
                    )

                if fact.get("evidence"):
                    st.markdown(
                        f"**Evidence:** "
                        f"{fact.get('evidence')}"
                    )

                if fact.get("sources"):
                    st.markdown(
                        f"**Sources:** "
                        f"{', '.join(fact.get('sources', []))}"
                    )

                st.divider()

            else:
                st.write(fact)
    else:
        st.info("No fact-check results available.")


# -------------------- Topics --------------------

with tab5:
    st.header("Topics Included in Video")

    if topics:
        for topic in topics:
            st.markdown(f"- {topic}")
    else:
        st.info("No main topics identified.")


# -------------------- References --------------------

with tab6:
    st.header("External References")

    if references:
        for ref in references:
            if isinstance(ref, dict):
                st.markdown(
                    f"### {ref.get('title', 'Reference')}"
                )

                st.write(
                    ref.get("relevance", "")
                )

                if ref.get("url"):
                    st.markdown(
                        f"[Source Link ↗]({ref['url']})"
                    )

                st.divider()

            else:
                st.write(ref)
    else:
        st.info("No external references found.")


# -------------------- Q&A Chat --------------------

with tab7:
    st.header("💬 Ask About This Video")

    st.caption(
        "Ask follow-up questions about the analyzed video. "
        "Your conversation will stay visible while you explore the video."
    )

    # Display complete conversation
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    question = st.chat_input(
        "Ask anything about this video..."
    )

    if question:
        question = question.strip()

        if question:
            # Add user message
            st.session_state.chat_history.append(
                {
                    "role": "user",
                    "content": question,
                }
            )

            with st.chat_message("user"):
                st.markdown(question)

            # Generate answer
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    answer = ask_question(question)

                if answer:
                    st.markdown(answer)

                    st.session_state.chat_history.append(
                        {
                            "role": "assistant",
                            "content": answer,
                        }
                    )

                    # Prevent the answer from disappearing on rerun
                    st.rerun()
