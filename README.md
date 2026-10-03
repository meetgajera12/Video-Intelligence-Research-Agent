# 🎥 Video Intelligence Research Agent

<p align="center">
  <b>AI-powered multi-agent system for analyzing and researching YouTube videos.</b>
</p>

---

## 🛠️ Tech Stack

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-Framework-1C3C3C?style=flat-square)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent%20Workflow-FF6B35?style=flat-square)
![Groq](https://img.shields.io/badge/Groq-LLM-F55036?style=flat-square)
![Hugging Face](https://img.shields.io/badge/Hugging%20Face-Models-FFD21E?style=flat-square&logo=huggingface&logoColor=black)
![Tavily](https://img.shields.io/badge/Tavily-Web%20Search-000000?style=flat-square)

---

## 📌 Overview

**Video Intelligence Research Agent** is an AI-powered application that analyzes YouTube videos and converts their content into structured research insights.

Instead of manually watching a long video, the system processes the video transcript through a multi-agent workflow to generate useful information such as:

- Video summary
- Key points
- Main topics
- Research-oriented claims
- Relevant references

The backend is built with **FastAPI**, while **LangGraph** is used to orchestrate the agent workflow.

---
## 🚀 Live Demo  [🔗 Try Video Intelligence Research Agent](https://video-intelligence-research-agent-f.vercel.app/)



## ✨ Features

- 🎥 YouTube video analysis
- 📝 Automatic transcript extraction
- 🤖 Multi-agent AI workflow
- 📄 Video summarization
- 🔑 Key-point extraction
- 🧩 Topic identification
- 📌 Claim extraction
- 🔎 Web/reference search
- 🆚 Comparison between videos
- 🧠 Structured research output
- ⚡ FastAPI backend
- 🌐 Separate frontend
- 🚀 Deployable frontend and backend

---

## 🧠 Agent Workflow

```text
                   YouTube URL
                         │
                         ▼
              ┌────────────────────┐
              │ Transcript / Video │
              │      Processing    │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │     LangGraph      │
              │   Agent Workflow   │
              └─────────┬──────────┘
                        │
          ┌─────────────┼─────────────┐
          │             │             │
          ▼             ▼             ▼
      Summary        Key Points     Topics
          │             │             │
          └─────────────┼─────────────┘
                        │
                        ▼
                Claim Extraction
                        │
                        ▼
                 Web Research
                        │
                        ▼
               Research Synthesis
                        │
                        ▼
                 Final Response
```

---

## 🔄 How It Works

### 1. YouTube URL

The user provides a YouTube video URL.

### 2. Transcript Extraction

The application retrieves the available transcript/data for the video using the configured YouTube data service.

### 3. Agent Processing

The transcript is passed through the LangGraph workflow.

Different branches of the workflow process the content for:

- Summary
- Key points
- Topics
- Claims
- References
- Question answering

### 4. Research

Relevant claims and topics are used for external web research through the reference workflow.

### 5. Video Comparison

The system also supports comparing two YouTube videos.

For each video, the system independently extracts:

- Claims
- Topics

The extracted information from both videos is then passed to the comparison agent.

```text
Video A ──→ Claim Extractor A ──┐
                                │
Video B ──→ Claim Extractor B ──┤
                                │
Video A ──→ Topic Agent A ──────┤
                                │
Video B ──→ Topic Agent B ──────┘
                                │
                                ▼
                       Comparison Agent
                                │
                                ▼
                       Comparison Output
```
---

## 🏗️ Project Structure

```text
Video-Intelligence-Research-Agent/
│
├── backend/
│   ├── agents.py
│   ├── agent_schema.py
│   ├── youtube.py
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
│   └── ...
│
├── streamlit-frontend/
│   └── ...
│
├── scratch/
│   └── ...
│
├── notebook.ipynb
│
├── .gitignore
│
└── README.md
```

### Backend Files

| File | Description |
|---|---|
| `main.py` | FastAPI application and API endpoints |
| `agents.py` | LangGraph agent workflow and agent logic |
| `agent_schema.py` | Structured schemas for agent state and output |
|`user_input_schema.py`| Structured schema for user inputs|
| `youtube.py` | YouTube transcript/data processing |
| `requirements.txt` | Python dependencies |

---

## 🚀 Getting Started

### Prerequisites

Make sure you have:

- Python 3.12+
- Node.js
- Git
- Required API keys

---

### 1. Clone the Repository

```bash
git clone https://github.com/meetgajera12/Video-Intelligence-Research-Agent.git

cd Video-Intelligence-Research-Agent
```

---

## ⚙️ Backend Setup

Navigate to the backend:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

Create a `.env` file inside the `backend` directory.

```env
GROQ_API_KEY=your_groq_api_key
HUGGINGFACE_API_KEY=your_huggingface_api_key
TAVILY_API_KEY=your_tavily_api_key
SUPADATA_API_KEY=your_supadata_api_key
```

### API Services

| Environment Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | LLM inference |
| `HUGGINGFACE_API_KEY` | Hugging Face model access |
| `TAVILY_API_KEY` | Web search and research |
| `SUPADATA_API_KEY` | YouTube transcript/data access |


---

## ▶️ Run the Backend

From the `backend` directory:

```bash
uvicorn backend.main:app --reload
```

The backend will be available at:

```text
http://127.0.0.1:8000
```

FastAPI Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

---

## 💻 Frontend Setup

Navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend communicates with the FastAPI backend through the configured API URL.

---

## 🔌 API

### `POST /agentRun`

Runs the video intelligence research workflow.

#### Request

```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

#### Processing Pipeline

```text
YouTube URL
     ↓
Transcript Extraction
     ↓
LangGraph Workflow
     ↓
AI Analysis
     ↓
Web Research
     ↓
Structured Research Response
```

---

## 🎯 Use Cases

### 📚 Educational Videos

Quickly understand long lectures, tutorials, and educational content.

### 🎙️ Podcasts & Interviews

Extract important ideas, topics, and claims from long conversations.

### 💻 Technical Content

Turn technical videos into structured notes and research points.

### 🔎 Research

Use video content as a starting point for deeper investigation and reference gathering.

### 🧠 Knowledge Extraction

Convert unstructured video content into structured information.

---

## ⚠️ Limitations

The quality of the generated results depends on:

- Transcript availability and quality
- LLM output quality
- External search results
- Third-party API availability
- Video length and complexity

AI-generated claims and research results should be independently verified when accuracy is important.

---

## 🔮 Future Improvements

- [ ] Timestamp-based citations
- [ ] Source credibility analysis
- [ ] Research history
- [ ] PDF/Markdown export

---

## 👨‍💻 Author

**Meet Gajera**

Ai/Ml Student

[GitHub](https://github.com/meetgajera12)  [Linkdin](https://www.linkedin.com/in/meet-gajera-12m32006/)  [Kaggle](https://www.kaggle.com/mitgajera)

---

## ⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub.
