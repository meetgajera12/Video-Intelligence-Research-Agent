/*
  Vercel frontend for Video Intelligence Agent.
  Backend remains FastAPI. Set API_URL in Vercel Environment Variables.
*/
const API_URL = (window.VIDEO_INTELLIGENCE_API_URL || "").replace(/\/$/, "") || "https://video-intelligence-research-agent.onrender.com";
const ANALYZE_ENDPOINT = `${API_URL}/agentRun`;

const state = {
  videoUrl: "",
  result: {},
  comparison: {},
  comparisonVideoUrl: "",
  chat: [],
  analysisTab: "transcript",
  comparisonTab: "overview"
};

const $ = (id) => document.getElementById(id);
const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;")
  .replaceAll('"',"&quot;").replaceAll("'","&#039;");

function showLoading(title, text="This can take a while.") {
  $("loadingTitle").textContent = title;
  $("loadingText").textContent = text;
  $("loading").classList.remove("hidden");
}
function hideLoading(){ $("loading").classList.add("hidden"); }
function toast(message){ $("toast").textContent=message; $("toast").classList.remove("hidden"); setTimeout(()=> $("toast").classList.add("hidden"),5000); }

async function postAgent(payload, timeoutMs=1200000) {
  const controller = new AbortController();
  const timer = setTimeout(()=>controller.abort(), timeoutMs);
  try {
    const response = await fetch(ANALYZE_ENDPOINT, {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify(payload),
      signal:controller.signal
    });
    const raw = await response.text();
    let data;
    try { data = JSON.parse(raw); } catch { data = {detail: raw}; }
    if (!response.ok) throw new Error(`API Error ${response.status}: ${data.detail || raw}`);
    return data;
  } finally { clearTimeout(timer); }
}

async function analyzeVideo() {
  const url = $("videoUrlInput").value.trim();
  if (!url) return toast("Please enter a valid YouTube video URL.");
  state.videoUrl = url;
  showLoading("Analyzing transcript & running research agents...", "The backend may take several minutes.");
  try {
    state.result = await postAgent({yt_url:url, question:null}, 1200000);
    state.chat = [];
    state.comparison = {};
    state.comparisonVideoUrl = "";
    renderWorkspace();
    toast("Video analysis completed.");
  } catch (err) {
    toast(err.name === "AbortError" ? "The request timed out." : err.message);
  } finally { hideLoading(); }
}

function clearAnalysis(){
  state.videoUrl=""; state.result={}; state.comparison={}; state.chat=[]; state.comparisonVideoUrl="";
  $("videoUrlInput").value="";
  $("workspace").classList.add("hidden"); $("emptyState").classList.remove("hidden"); $("clearBtn").classList.add("hidden");
}

function array(v){ return Array.isArray(v) ? v : []; }
function valueText(v){ return typeof v === "object" ? JSON.stringify(v, null, 2) : String(v ?? ""); }

function renderItems(items, emptyMessage="No data available.") {
  if (!items || (Array.isArray(items) && !items.length)) return `<div class="empty">${escapeHtml(emptyMessage)}</div>`;
  if (typeof items !== "object") return `<div class="data-block">${escapeHtml(valueText(items))}</div>`;
  if (!Array.isArray(items)) {
    return Object.entries(items).map(([k,v]) =>
      `<div class="fact"><div class="label">${escapeHtml(k.replaceAll("_"," "))}</div><div>${escapeHtml(valueText(v))}</div></div>`
    ).join("");
  }
  return items.map(item => {
    if (item && typeof item === "object" && !Array.isArray(item)) {
      if ("video_a_claim" in item || "video_b_claim" in item || "relationship" in item) {
        return `<div class="fact">
          ${item.relationship ? `<div class="label">${escapeHtml(String(item.relationship).replaceAll("_"," "))}</div>` : ""}
          ${item.video_a_claim ? `<div><span class="label">Video A:</span> ${escapeHtml(item.video_a_claim)}</div>` : ""}
          ${item.video_b_claim ? `<div><span class="label">Video B:</span> ${escapeHtml(item.video_b_claim)}</div>` : ""}
          ${item.explanation ? `<div><span class="label">Explanation:</span> ${escapeHtml(item.explanation)}</div>` : ""}
        </div>`;
      }
      if ("claim" in item || "verdict" in item || "evidence" in item || "sources" in item) {
        const verdict = String(item.verdict || "UNKNOWN");
        const cls = verdict === "TRUE" ? "true" : verdict === "FALSE" ? "false" : "unknown";
        return `<div class="fact">
          ${item.claim ? `<div><span class="label">Claim:</span> ${escapeHtml(item.claim)}</div>` : ""}
          ${item.verdict ? `<div><span class="label">Verdict:</span> <span class="verdict ${cls}">${escapeHtml(verdict)}</span></div>` : ""}
          ${item.explanation ? `<div><span class="label">Explanation:</span> ${escapeHtml(item.explanation)}</div>` : ""}
          ${item.evidence ? `<div><span class="label">Evidence:</span> ${escapeHtml(item.evidence)}</div>` : ""}
          ${item.sources ? `<div><span class="label">Sources:</span> ${escapeHtml(array(item.sources).join(", ") || item.sources)}</div>` : ""}
        </div>`;
      }
      return `<pre class="data-block">${escapeHtml(JSON.stringify(item,null,2))}</pre>`;
    }
    return `<div class="fact">• ${escapeHtml(valueText(item))}</div>`;
  }).join("");
}

function renderAnalysisContent(){
  const r=state.result, tab=state.analysisTab;
  let html="";
  if(tab==="transcript") html=`<div class="section-kicker">SOURCE MATERIAL</div><h2>YouTube Video Transcript</h2><p class="section-description">The source text used by the research workflow.</p><div class="data-block prose">${escapeHtml(r.video_transcript || "No transcript available.")}</div>`;
  if(tab==="summary") html=`<div class="section-kicker">AT A GLANCE</div><h2>Summary</h2><p class="section-description">A concise synthesis of the video’s main argument and ideas.</p><div class="data-block prose">${escapeHtml(r.summary || "No summary available.")}</div>`;
  if(tab==="keypoints") html=`<div class="section-kicker">TAKEAWAYS</div><h2>Key Points</h2><p class="section-description">The main ideas worth remembering or revisiting.</p><div class="data-block"><ul class="list">${array(r.key_points).map(x=>`<li>${escapeHtml(x)}</li>`).join("") || "<li>No key points found.</li>"}</ul></div>`;
  if(tab==="claims") html=`<div class="section-kicker">EVIDENCE REVIEW</div><h2>Claims &amp; Fact Check</h2><p class="section-description">Separate what the video claims from what the verification workflow found.</p><h3>Extracted Factual Claims</h3>${renderItems(r.claims,"No explicit factual claims extracted from the video.")}<h3>Fact Check Verification Results</h3>${renderItems(r.fact_check,"No fact-check results available.")}`;
  if(tab==="topics") html=`<div class="section-kicker">MAP THE CONTENT</div><h2>Topics Included in Video</h2><p class="section-description">The major subjects detected across the video.</p><div class="data-block"><ul class="list">${array(r.topics).map(x=>`<li>${escapeHtml(x)}</li>`).join("") || "<li>No main topics identified.</li>"}</ul></div>`;
  if(tab==="references") html=`<div class="section-kicker">RESEARCH TRAIL</div><h2>External References</h2><p class="section-description">Sources gathered to extend or support the video’s discussion.</p>${array(r.references).map(ref=> typeof ref==="object" ? `<div class="reference"><div class="reference-title">${escapeHtml(ref.title||"Reference")}</div><div class="reference-text">${escapeHtml(ref.relevance||"")}</div>${ref.url?`<a href="${escapeHtml(ref.url)}" target="_blank" rel="noopener noreferrer">Open source ↗</a>`:""}</div>`:`<div class="reference">${escapeHtml(ref)}</div>`).join("") || '<div class="empty">No external references found.</div>'}`;
  if(tab==="qa") html=renderQA();
  $("analysisContent").innerHTML=html;
}

function renderQA(){
  return `<div class="qa-wrap">
    <div class="qa-kicker">VIDEO RESEARCH / CONVERSATION</div>
    <div class="qa-title">Ask the video.</div>
    <div class="qa-description">Explore the ideas in this video through a grounded conversation. Ask for explanations, examples, comparisons, or clarification.</div>
    <div class="context-pill"><span class="status-dot"></span>Context locked to analyzed video</div>
    ${state.chat.length===0 ? `<div class="content-card"><div class="content-card-title">What do you want to understand?</div><div class="content-card-text">Choose a starting point or ask your own question below.</div></div>
    <div class="overview-label">Suggested questions</div>
    <div class="prompt-grid">${[
      "What is the main idea of this video?",
      "Explain the most important concept with an example.",
      "What are the key claims I should verify?"
    ].map((p,i)=>`<button class="btn prompt-btn" data-prompt="${escapeHtml(p)}">${escapeHtml(p)}</button>`).join("")}</div>`:""}
    <div class="chat">${state.chat.map(m=>`<div class="message ${m.role}">${escapeHtml(m.content)}</div>`).join("")}</div>
    <form class="qa-form" id="qaForm"><input id="questionInput" placeholder="Ask a follow-up about this video..." autocomplete="off"/><button class="btn" type="submit">Ask ↗</button></form>
  </div>`;
}

async function askQuestion(question){
  const q=question.trim(); if(!q) return;
  state.chat.push({role:"user",content:q}); renderAnalysisContent();
  showLoading("Researching the video context...","Generating a grounded answer.");
  try {
    const data=await postAgent({yt_url:state.videoUrl,question:q},1200000);
    state.chat.push({role:"assistant",content:data.answer || "No answer returned."});
  } catch(err) { state.chat.push({role:"assistant",content:`Request failed: ${err.message}`}); }
  finally { hideLoading(); renderAnalysisContent(); }
}

function renderWorkspace(){
  $("emptyState").classList.add("hidden"); $("workspace").classList.remove("hidden"); $("clearBtn").classList.remove("hidden");
  $("sourceUrl").textContent=state.videoUrl;
  $("videoAInput").value=state.videoUrl;
  const r=state.result;
  $("metricTranscript").textContent=r.video_transcript ? "Available" : "Missing";
  $("metricKeyPoints").textContent=array(r.key_points).length;
  $("metricClaims").textContent=array(r.claims).length;
  $("metricReferences").textContent=array(r.references).length;
  renderAnalysisContent();
}

async function compareVideos(){
  const b=$("videoBInput").value.trim();
  if(!state.videoUrl) return toast("Please analyze Video A first.");
  if(!b) return toast("Please enter a second YouTube video URL.");
  if(b===state.videoUrl) return toast("Video A and Video B are the same video.");
  showLoading("Comparing both videos & running comparison agents...","This workflow can take several minutes.");
  try {
    const data=await postAgent({yt_url:state.videoUrl,yt2_url:b,question:null},1200000);
    state.comparisonVideoUrl=b;
    state.comparison={
      claims_a:data.claims_a||[],claims_b:data.claims_b||[],topics_a:data.topics_a||[],topics_b:data.topics_b||[],
      similarities:data.similarities||[],differences:data.differences||[],contradictions:data.contradictions||[],
      claim_comparison:data.claim_comparison||[],claims_to_fact_check:data.claims_to_fact_check||[],fact_check_results:data.fact_check_results||[]
    };
    renderComparison();
    toast("Comparison completed.");
  } catch(err){ toast(err.name==="AbortError"?"The comparison request timed out.":err.message); }
  finally{hideLoading();}
}

function renderComparison(){
  const c=state.comparison;
  if(!Object.keys(c).length){$("comparisonResults").classList.add("hidden");return}
  $("comparisonResults").classList.remove("hidden");
  $("comparisonResults").innerHTML=`
    <div class="source-card"><div class="source-label">Comparison sources</div><div class="source-url"><strong>Video A:</strong> ${escapeHtml(state.videoUrl)}</div><div class="source-url"><strong>Video B:</strong> ${escapeHtml(state.comparisonVideoUrl)}</div></div>
    <div class="compare-overview">
      ${[['Similarities',c.similarities],['Differences',c.differences],['Contradictions',c.contradictions],['Claims to verify',c.claims_to_fact_check]].map(([n,v])=>`<div class="overview-card"><div class="overview-value">${array(v).length}</div><div class="overview-name">${n}</div></div>`).join("")}
    </div>
    <nav class="compare-tabs">${[['overview','Overview'],['claims','Claims'],['topics','Topics'],['differences','Differences'],['contradictions','Contradictions'],['factcheck','Fact Check']].map(([id,n])=>`<button class="compare-tab ${state.comparisonTab===id?'active':''}" data-compare-tab="${id}">${n}</button>`).join("")}</nav>
    <div id="compareContent"></div>`;
  renderCompareContent();
}

function renderCompareContent(){
  const c=state.comparison,t=state.comparisonTab;let html="";
  if(t==="overview") html=`<div class="section-kicker">HIGH-LEVEL COMPARISON</div><h3>Similarities</h3>${renderItems(c.similarities,"No similarities identified.")}<h3>Differences</h3>${renderItems(c.differences,"No differences identified.")}`;
  if(t==="claims") html=`<div class="section-kicker">CLAIM ANALYSIS</div><h3>Claims across both videos</h3><div class="two-col"><div><h3>Video A Claims</h3>${renderItems(c.claims_a,"No claims extracted from Video A.")}</div><div><h3>Video B Claims</h3>${renderItems(c.claims_b,"No claims extracted from Video B.")}</div></div><h3>Claim Relationships</h3>${renderItems(c.claim_comparison,"No claim relationships returned.")}`;
  if(t==="topics") html=`<div class="section-kicker">TOPIC ANALYSIS</div><h3>Topics across both videos</h3><div class="two-col"><div><h3>Video A Topics</h3>${renderItems(c.topics_a,"No topics extracted from Video A.")}</div><div><h3>Video B Topics</h3>${renderItems(c.topics_b,"No topics extracted from Video B.")}</div></div>`;
  if(t==="differences") html=`<div class="section-kicker">CONTENT DIFFERENCES</div><h3>How the videos differ</h3>${renderItems(c.differences,"No differences identified.")}`;
  if(t==="contradictions") html=`<div class="section-kicker">CONTRADICTION REVIEW</div><h3>Potentially contradictory claims</h3><p class="section-description">These are comparison-agent findings. They are shown separately from independent fact-check results.</p>${renderItems(c.contradictions,"No contradictions identified.")}`;
  if(t==="factcheck") html=`<div class="section-kicker">INDEPENDENT VERIFICATION</div><h3>Claims selected for verification</h3>${renderItems(c.claims_to_fact_check,"No claims were selected for fact checking.")}<h3>Verification results</h3>${renderItems(c.fact_check_results,"No comparison fact-check results available.")}`;
  $("compareContent").innerHTML=html;
}

document.addEventListener("click",(e)=>{
  const mainTab=e.target.closest("[data-main-tab]");
  if(mainTab){
    document.querySelectorAll(".main-tab").forEach(x=>x.classList.remove("active")); mainTab.classList.add("active");
    const isAnalysis=mainTab.dataset.mainTab==="analysis";
    $("analysisView").classList.toggle("hidden",!isAnalysis); $("comparisonView").classList.toggle("hidden",isAnalysis); return;
  }
  const tab=e.target.closest("[data-tab]");
  if(tab){state.analysisTab=tab.dataset.tab;document.querySelectorAll(".sub-tab").forEach(x=>x.classList.remove("active"));tab.classList.add("active");renderAnalysisContent();return}
  const prompt=e.target.closest("[data-prompt]"); if(prompt){askQuestion(prompt.dataset.prompt);return}
  const ctab=e.target.closest("[data-compare-tab]");
  if(ctab){state.comparisonTab=ctab.dataset.compareTab;renderComparison();return}
});

document.addEventListener("submit",(e)=>{
  if(e.target.id==="qaForm"){e.preventDefault();askQuestion($("questionInput").value)}
});
$("analyzeBtn").addEventListener("click",analyzeVideo);
$("clearBtn").addEventListener("click",clearAnalysis);
$("compareBtn").addEventListener("click",compareVideos);
$("videoUrlInput").addEventListener("keydown",e=>{if(e.key==="Enter")analyzeVideo()});
