import streamlit as st
import requests

API_URL = 'http://127.0.0.1:8000/agentRun'

st.set_page_config(
    page_icon="🤝",
    page_title='Video Intelligence Agent',
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🎥 Video Intelligence Research Agent")

url = st.sidebar.text_input('YouTube Video URL')
question = st.sidebar.text_input('Question (Optional)')

if st.sidebar.button('Analyze Video'):
    if not url.strip():
        st.warning("Please enter a valid YouTube video URL.")
    else:
        with st.spinner("Analyzing transcript & running research agents..."):
            try:
                response = requests.post(API_URL, json={
                    'yt_url': url,
                    'question': question
                })

                if response.status_code == 200:
                    result = response.json()

                    video_transcript = result.get("video_transcript", "")
                    summary = result.get("summary", "")
                    key_points = result.get("key_points", [])
                    claims = result.get("claims", [])
                    fact_check = result.get("fact_check", [])
                    topics = result.get("topics", [])
                    references = result.get("references", [])
                    answer = result.get("answer", "")

                    if answer:
                        st.subheader("❓ Q&A Answer")
                        st.info(answer)

                    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                        "📜 Transcript", 
                        "📝 Summary", 
                        "🔑 Key Points", 
                        "✅ Claims & Fact Check", 
                        "🏷️ Topics", 
                        "📚 References"
                    ])

                    with tab1:
                        st.header("YouTube Video Transcript")
                        st.write(video_transcript if video_transcript else "No transcript available.")

                    with tab2:
                        st.header("Summary")
                        st.write(summary if summary else "No summary available.")

                    with tab3:
                        st.header("Key Points")
                        if key_points:
                            for point in key_points:
                                st.markdown(f"- {point}")
                        else:
                            st.info("No key points found.")

                    with tab4:
                        st.header("Claims & Fact Check")
                        if claims:
                            st.subheader("Extracted Factual Claims")
                            for c in claims:
                                st.markdown(f"- {c}")
                        else:
                            st.info("No explicit factual claims extracted from the video.")

                        if fact_check:
                            st.subheader("Fact Check Verification Results")
                            for fact in fact_check:
                                if isinstance(fact, dict):
                                    verdict = fact.get("verdict", "UNKNOWN")
                                    color = "green" if verdict == "TRUE" else ("red" if verdict == "FALSE" else "orange")
                                    st.markdown(f"**Claim**: {fact.get('claim', '')}")
                                    st.markdown(f"**Verdict**: :{color}[{verdict}]")
                                    if fact.get("explanation"):
                                        st.markdown(f"**Explanation**: {fact.get('explanation')}")
                                    if fact.get("evidence"):
                                        st.markdown(f"**Evidence**: {fact.get('evidence')}")
                                    if fact.get("sources"):
                                        st.markdown(f"**Sources**: {', '.join(fact.get('sources', []))}")
                                    st.divider()
                                else:
                                    st.write(fact)
                        else:
                            st.info("No fact-check results available.")

                    with tab5:
                        st.header("Topics Included in Video")
                        if topics:
                            for topic in topics:
                                st.markdown(f"- {topic}")
                        else:
                            st.info("No main topics identified.")

                    with tab6:
                        st.header("External References")
                        if references:
                            for ref in references:
                                if isinstance(ref, dict):
                                    st.markdown(f"### {ref.get('title', 'Reference')}")
                                    st.write(ref.get("relevance", ""))
                                    if ref.get("url"):
                                        st.markdown(f"[Source Link ↗]({ref['url']})")
                                    st.divider()
                                else:
                                    st.write(ref)
                        else:
                            st.info("No external references found.")

                else:
                    st.error(
                        f"API Error {response.status_code}: "
                        f"{response.text}"
                    )

            except requests.exceptions.ConnectionError:
                st.error("FastAPI server is not running. Please start backend/main.py first.")




