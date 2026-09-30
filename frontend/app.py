import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/agentRun"

st.set_page_config(
    page_icon="🤝",
    page_title="Video Intelligence Agent",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ---------- Editorial / research UI ---------- */

.stApp {
    background:
        radial-gradient(circle at 12% 8%, rgba(126, 154, 137, 0.07), transparent 28%),
        radial-gradient(circle at 88% 82%, rgba(183, 157, 117, 0.045), transparent 26%),
        #111311;
    color: #e7e3d9;
}

.block-container {
    max-width: 1180px;
    padding-top: 3.6rem;
    padding-bottom: 4rem;
}

/* Quiet paper-like texture without a glossy effect */
.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    opacity: 0.025;
    background-image:
        repeating-linear-gradient(
            0deg,
            rgba(255,255,255,0.7) 0px,
            rgba(255,255,255,0.7) 1px,
            transparent 1px,
            transparent 4px
        );
    z-index: 0;
}

.block-container > div {
    position: relative;
    z-index: 1;
}


/* Tight, even spacing inside the four overview columns */
div[data-testid="stHorizontalBlock"] {
    align-items: stretch;
}

div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #151815;
    border-right: 1px solid #292e29;
}

section[data-testid="stSidebar"] .block-container {
    padding: 2rem 1.35rem;
}

/* Typography */
html, body, [class*="css"] {
    font-family: "Inter", "Segoe UI", system-ui, sans-serif;
}

h1 {
    color: #f0ece2 !important;
    font-family: Georgia, "Times New Roman", serif !important;
    font-size: 3.15rem !important;
    font-weight: 500 !important;
    letter-spacing: -0.045em;
    line-height: 1.05 !important;
}

h2, h3 {
    color: #eeeae0 !important;
    font-family: Georgia, "Times New Roman", serif !important;
    font-weight: 500 !important;
    letter-spacing: -0.025em;
}

p, li, label {
    color: #b9b7ae;
}

.app-subtitle {
    max-width: 720px;
    color: #92968e;
    font-size: 1rem;
    line-height: 1.7;
    margin: 0.35rem 0 2.2rem;
}

/* Small product label */
.product-label {
    color: #91a997;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-bottom: 0.55rem;
}

/* Video context strip */
.status-card {
    background: #171a17;
    border: 1px solid #30352f;
    border-left: 3px solid #91a997;
    border-radius: 5px;
    padding: 0.9rem 1.1rem;
    margin: 1rem 0 1.7rem;
}

.status-title {
    color: #dcd9cf;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.status-url {
    color: #777d75;
    font-size: 0.78rem;
    margin-top: 0.35rem;
    word-break: break-all;
}

/* ---------- Workspace navigation ---------- */

div[data-baseweb="tab-list"] {
    gap: 0.35rem;
    background: #151815;
    border: 1px solid #292f29;
    border-radius: 7px;
    padding: 0.35rem;
    margin: 1.5rem 0 1.8rem;
    overflow-x: auto;
    scrollbar-width: none;
}

div[data-baseweb="tab-list"]::-webkit-scrollbar {
    display: none;
}

button[data-baseweb="tab"] {
    position: relative;
    color: #858a82 !important;
    font-weight: 600;
    font-size: 0.79rem;
    min-height: 40px;
    border-radius: 5px !important;
    padding: 0.55rem 0.78rem !important;
    border: 1px solid transparent !important;
    background: transparent !important;
    transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
}

button[data-baseweb="tab"]:hover {
    color: #d4d8d0 !important;
    background: #1c211c !important;
    border-color: #303730 !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #e2e6df !important;
    background: #202720 !important;
    border-color: #3a443b !important;
    box-shadow: inset 0 -2px 0 #91a997;
}

button[data-baseweb="tab"][aria-selected="true"]::after {
    content: "";
    position: absolute;
    left: 14%;
    right: 14%;
    bottom: -1px;
    height: 2px;
    background: #91a997;
    border-radius: 2px;
}

div[data-baseweb="tab-highlight"] {
    display: none !important;
}

/* Give the tab panel a little separation from navigation */
div[data-baseweb="tab-panel"] {
    padding-top: 0.25rem;
}

/* Inputs */
[data-baseweb="input"],
[data-baseweb="textarea"] {
    background: #171a17 !important;
    border-color: #30352f !important;
}

[data-baseweb="input"]:focus-within,
[data-baseweb="textarea"]:focus-within {
    border-color: #667c6b !important;
    box-shadow: none !important;
}

/* Buttons */
.stButton > button {
    background: #1d221e;
    color: #d9ddd5;
    border: 1px solid #353b35;
    border-radius: 5px;
    font-weight: 650;
    transition: 0.15s ease;
}

.stButton > button:hover {
    background: #232923;
    color: #eef0e9;
    border-color: #5d6b5f;
}

/* Q&A section */
.qa-kicker {
    color: #91a997;
    font-size: 0.68rem;
    font-weight: 750;
    letter-spacing: 0.17em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
}

.qa-title {
    color: #eeeae0;
    font-family: Georgia, "Times New Roman", serif;
    font-size: 2.25rem;
    line-height: 1.05;
    letter-spacing: -0.035em;
    margin-bottom: 0.65rem;
}

.qa-description {
    max-width: 720px;
    color: #92968e;
    font-size: 0.94rem;
    line-height: 1.65;
    margin-bottom: 0.85rem;
}

.context-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    color: #aeb8af;
    background: #151915;
    border: 1px solid #30362f;
    border-radius: 4px;
    padding: 0.38rem 0.62rem;
    font-size: 0.69rem;
    margin-bottom: 1.7rem;
}

.context-dot {
    width: 6px;
    height: 6px;
    background: #91a997;
    border-radius: 50%;
}

/* Welcome area */
.welcome-card {
    background: #151815;
    border-top: 1px solid #30352f;
    border-bottom: 1px solid #30352f;
    padding: 1.35rem 0 1.15rem;
    margin-bottom: 1rem;
}

.welcome-icon {
    display: none;
}

.welcome-title {
    color: #ddd9cf;
    font-family: Georgia, "Times New Roman", serif;
    font-size: 1.25rem;
    margin-bottom: 0.3rem;
}

.welcome-text {
    color: #858b83;
    font-size: 0.82rem;
    line-height: 1.55;
    max-width: 650px;
}

.prompt-label {
    color: #727970;
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    margin: 1.1rem 0 0.55rem;
}

/* Suggested question buttons */
.prompt-button {
    font-size: 0.78rem;
}

/* Chat messages: quiet research-notebook style */
[data-testid="stChatMessage"] {
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 0.25rem 0 1rem;
    margin-bottom: 0.4rem;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
    max-width: 790px;
    line-height: 1.72;
}

[data-testid="stChatMessage"] [data-testid="stChatMessageAvatar"] {
    background: #202620;
    border: 1px solid #394139;
}

/* Keep assistant response understated */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    background: #151815;
    border: 1px solid #2b302b;
    border-left: 2px solid #91a997;
    border-radius: 4px;
    padding: 0.9rem 1rem;
    margin: 0.2rem 0 1rem;
}

/* Chat input */
[data-testid="stChatInput"] {
    border: 1px solid #353b35 !important;
    border-radius: 6px !important;
    background: #171a17 !important;
}

[data-testid="stChatInput"] textarea {
    color: #e5e2d9 !important;
}

/* Dividers */
hr {
    border-color: #292e29 !important;
}

/* Alerts */
[data-testid="stAlert"] {
    background: #171a17;
    border: 1px solid #30352f;
    border-radius: 5px;
}



/* ---------- Top utility area ---------- */
.workspace-meta {
    position: fixed;
    top: 13px;
    right: 92px;
    z-index: 999;
    color: #777d75;
    font-size: 0.64rem;
    font-weight: 750;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 0.32rem 0.55rem;
    border: 1px solid #292f29;
    border-radius: 4px;
    background: #111311;
}

.workspace-meta-dot {
    display: inline-block;
    width: 5px;
    height: 5px;
    margin-right: 0.35rem;
    border-radius: 50%;
    background: #91a997;
    vertical-align: middle;
}

/* ---------- Usability components ---------- */

/* Main context container */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #131613;
    border: 1px solid #292f29;
    border-radius: 7px;
    padding: 1rem 1rem 1.15rem;
    margin: 0.7rem 0 1.15rem;
    box-sizing: border-box;
    overflow: visible;
}

div[data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: 0 !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] {
    gap: 0.45rem;
}

.overview-label {
    color: #777d75;
    font-size: 0.67rem;
    font-weight: 750;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin: 0.75rem 0 0.35rem;
}

.overview-card {
    background: #151815;
    border: 1px solid #2b302b;
    border-radius: 5px;
    padding: 0.7rem 0.85rem;
    min-height: 62px;
    box-sizing: border-box;
    margin-bottom: 0.15rem;
}

.overview-value {
    color: #e3dfd5;
    font-family: Georgia, "Times New Roman", serif;
    font-size: 1.35rem;
    line-height: 1.1;
}

.overview-name {
    color: #777d75;
    font-size: 0.69rem;
    margin-top: 0.3rem;
}

.source-card {
    background: #151815;
    border: 1px solid #2b302b;
    border-radius: 5px;
    padding: 0.72rem 0.9rem;
    margin: 0.05rem 0 0.15rem;
}

.source-label {
    color: #777d75;
    font-size: 0.67rem;
    font-weight: 750;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

.source-url {
    color: #b5b7ae;
    font-size: 0.78rem;
    margin-top: 0.35rem;
    overflow-wrap: anywhere;
}

.section-kicker {
    color: #91a997;
    font-size: 0.68rem;
    font-weight: 750;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.45rem;
}

.section-description {
    color: #858b83;
    font-size: 0.86rem;
    line-height: 1.6;
    margin-bottom: 1.15rem;
}

.content-card {
    background: #151815;
    border: 1px solid #2b302b;
    border-radius: 5px;
    padding: 1rem 1.1rem;
    margin: 0.7rem 0;
}

.content-card-title {
    color: #dedbd1;
    font-size: 0.88rem;
    font-weight: 650;
    margin-bottom: 0.35rem;
}

.content-card-text {
    color: #8d928a;
    font-size: 0.8rem;
    line-height: 1.55;
}

.action-note {
    color: #777d75;
    font-size: 0.7rem;
    margin-top: 0.45rem;
}

/* Better keyboard/focus accessibility without changing the visual palette */
button:focus-visible,
input:focus-visible,
textarea:focus-visible,
[data-baseweb="tab"]:focus-visible {
    outline: 2px solid #91a997 !important;
    outline-offset: 2px !important;
}

/* Make clickable controls feel clickable */
.stButton > button {
    min-height: 42px;
}

.stButton > button:active {
    transform: translateY(1px);
}

/* Better tab hit area */
button[data-baseweb="tab"] {
    min-height: 42px;
    padding-left: 0.7rem !important;
    padding-right: 0.7rem !important;
}

/* Better readable body width */
[data-testid="stMarkdownContainer"] {
    line-height: 1.65;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: #151815;
    border: 1px solid #2b302b;
    border-radius: 5px;
    padding: 0.75rem 0.9rem;
}

[data-testid="stMetricLabel"] {
    color: #777d75 !important;
}

[data-testid="stMetricValue"] {
    color: #e3dfd5 !important;
}

/* Sidebar action grouping */
.sidebar-help {
    color: #777d75;
    font-size: 0.72rem;
    line-height: 1.55;
    margin: 0.5rem 0 1rem;
}

/* Remove default Streamlit chrome */
#MainMenu,
footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)

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

st.sidebar.markdown("### Video Analysis")
st.sidebar.markdown(
    '<div class="sidebar-help">'
    'Paste a public YouTube URL, then analyze it once. '
    'The results below become your research workspace.'
    '</div>',
    unsafe_allow_html=True,
)

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

st.markdown(
    '<div class="workspace-meta"><span class="workspace-meta-dot"></span>Research mode</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="product-label">VIDEO INTELLIGENCE / RESEARCH WORKSPACE</div>',
    unsafe_allow_html=True,
)
st.title("Understand the video. Go deeper.")
st.markdown(
    '<div class="app-subtitle">A research workspace for turning long-form YouTube content '
    'into structured evidence, references, and grounded conversation.</div>',
    unsafe_allow_html=True,
)

if not st.session_state.video_analyzed:
    st.markdown(
        '<div class="content-card">'
        '<div class="section-kicker">START HERE</div>'
        '<div class="content-card-title">Analyze a YouTube video</div>'
        '<div class="content-card-text">'
        'Enter a public YouTube URL in the sidebar. The workspace will build '
        'a transcript, summary, key points, claims, topics, references, and Q&A context.'
        '</div>'
        '<div class="action-note">Your results will appear here after analysis.</div>'
        '</div>',
        unsafe_allow_html=True,
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

with st.container(border=True):
    st.markdown(
        '<div class="section-kicker">VIDEO CONTEXT</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""<div class="source-card">
        <div class="source-label">Analyzed source</div>
        <div class="source-url">{st.session_state.video_url}</div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="overview-label">At a glance</div>',
        unsafe_allow_html=True,
    )

    overview = st.columns(4)

    overview_data = [
        ("Transcript", "Available" if video_transcript else "Missing"),
        ("Key points", str(len(key_points))),
        ("Claims", str(len(claims))),
        ("References", str(len(references))),
    ]

    for col, (label, value) in zip(overview, overview_data):
        with col:
            st.markdown(
                f"""<div class="overview-card">
                <div class="overview-value">{value}</div>
                <div class="overview-name">{label}</div>
                </div>""",
                unsafe_allow_html=True,
            )


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
    st.markdown('<div class="section-kicker">SOURCE MATERIAL</div>', unsafe_allow_html=True)
    st.header("YouTube Video Transcript")
    st.markdown(
        '<div class="section-description">The source text used by the research workflow.</div>',
        unsafe_allow_html=True,
    )
    st.write(
        video_transcript
        if video_transcript
        else "No transcript available."
    )


# -------------------- Summary --------------------

with tab2:
    st.markdown('<div class="section-kicker">AT A GLANCE</div>', unsafe_allow_html=True)
    st.header("Summary")
    st.markdown(
        '<div class="section-description">A concise synthesis of the video’s main argument and ideas.</div>',
        unsafe_allow_html=True,
    )
    st.write(
        summary
        if summary
        else "No summary available."
    )


# -------------------- Key Points --------------------

with tab3:
    st.markdown('<div class="section-kicker">TAKEAWAYS</div>', unsafe_allow_html=True)
    st.header("Key Points")
    st.markdown(
        '<div class="section-description">The main ideas worth remembering or revisiting.</div>',
        unsafe_allow_html=True,
    )

    if key_points:
        for point in key_points:
            st.markdown(f"- {point}")
    else:
        st.info("No key points found.")


# -------------------- Claims & Fact Check --------------------

with tab4:
    st.markdown('<div class="section-kicker">EVIDENCE REVIEW</div>', unsafe_allow_html=True)
    st.header("Claims & Fact Check")
    st.markdown(
        '<div class="section-description">Separate what the video claims from what the verification workflow found.</div>',
        unsafe_allow_html=True,
    )

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
    st.markdown('<div class="section-kicker">MAP THE CONTENT</div>', unsafe_allow_html=True)
    st.header("Topics Included in Video")
    st.markdown(
        '<div class="section-description">The major subjects detected across the video.</div>',
        unsafe_allow_html=True,
    )

    if topics:
        for topic in topics:
            st.markdown(f"- {topic}")
    else:
        st.info("No main topics identified.")


# -------------------- References --------------------

with tab6:
    st.markdown('<div class="section-kicker">RESEARCH TRAIL</div>', unsafe_allow_html=True)
    st.header("External References")
    st.markdown(
        '<div class="section-description">Sources gathered to extend or support the video’s discussion.</div>',
        unsafe_allow_html=True,
    )

    if references:
        for ref in references:
            if isinstance(ref, dict):
                st.markdown(
                    f"""<div class="content-card">
                    <div class="content-card-title">{ref.get('title', 'Reference')}</div>
                    <div class="content-card-text">{ref.get('relevance', '')}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

                if ref.get("url"):
                    st.markdown(
                        f"[Open source ↗]({ref['url']})"
                    )

            else:
                st.write(ref)
    else:
        st.info("No external references found.")


# -------------------- Q&A Chat --------------------

with tab7:
    st.markdown(
        '<div class="qa-kicker">VIDEO RESEARCH / CONVERSATION</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="qa-title">Ask the video.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="qa-description">'
        'Explore the ideas in this video through a grounded conversation. '
        'Ask for explanations, examples, comparisons, or clarification.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="context-pill">'
        '<span class="context-dot"></span>'
        'Context locked to analyzed video'
        '</div>',
        unsafe_allow_html=True,
    )

    # First screen: keep it simple and useful.
    if not st.session_state.chat_history:
        st.markdown(
            '<div class="welcome-card">'
            '<div class="welcome-title">What do you want to understand?</div>'
            '<div class="welcome-text">'
            'Choose a starting point or ask your own question below.'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="prompt-label">Suggested questions</div>',
            unsafe_allow_html=True,
        )

        prompt_cols = st.columns(3)

        prompts = [
            "What is the main idea of this video?",
            "Explain the most important concept with an example.",
            "What are the key claims I should verify?",
        ]

        for index, (col, prompt) in enumerate(zip(prompt_cols, prompts)):
            with col:
                if st.button(
                    prompt,
                    key=f"prompt_{index}",
                    use_container_width=True,
                ):
                    st.session_state.pending_question = prompt
                    st.rerun()

    # Display conversation
    for message in st.session_state.chat_history:
        # Do NOT pass a custom avatar string here.
        # Streamlit's built-in user/assistant avatars are used.
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Suggested question or typed question
    question = st.session_state.pop("pending_question", None)

    typed_question = st.chat_input(
        "Ask a follow-up about this video..."
    )

    if typed_question:
        question = typed_question.strip()

    if question:
        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": question,
            }
        )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Researching the video context..."):
                answer = ask_question(question)

            if answer:
                st.markdown(answer)

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

                st.rerun()
