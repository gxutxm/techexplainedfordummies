import { useState, useRef } from "react"

const PROFILES = [
  { id: "technical_expert", name: "Technical Expert", desc: "Senior engineer evaluating depth, correctness, and trade-offs." },
  { id: "hiring_manager", name: "Hiring Manager", desc: "Evaluates communication, confidence, and hireability." },
  { id: "executive", name: "Non-Technical Executive", desc: "Evaluates business clarity and ROI relevance." },
  { id: "layman", name: "Layman", desc: "Evaluates simplicity and understandability." },
  { id: "student", name: "Student", desc: "Evaluates teaching clarity and step-by-step explanation." },
  { id: "product_manager", name: "Product Manager", desc: "Evaluates user impact and problem framing." },
  { id: "investor", name: "Investor", desc: "Evaluates scalability and vision." },
  { id: "peer_engineer", name: "Peer Engineer", desc: "Evaluates practical understanding for collaboration." },
  { id: "ux_designer", name: "UX Designer", desc: "Evaluates user experience and usability thinking." },
  { id: "elevator_pitch", name: "Time-Pressed Listener", desc: "Evaluates brevity and clarity in short explanations." },
]

async function apiStartSession(text, persona) {
  const res = await fetch("http://localhost:8000/session/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source_text: text, persona })
  })
  return res.json()
}

async function apiStartFromFile(file) {
  const formData = new FormData()
  formData.append("file", file)
  const res = await fetch("http://localhost:8000/session/start-from-file", {
    method: "POST",
    body: formData
  })
  return res.json()
}

async function apiSendMessage(sessionId, content) {
  const res = await fetch("http://localhost:8000/session/message", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, user_message: content })
  })
  return res.json()
}

async function apiEvaluate(sessionId) {
  const res = await fetch(`http://localhost:8000/session/${sessionId}/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  })
  return res.json()
}

const sf = "-apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif"
const handwriting = "'Reenie Beanie', cursive"

export default function App() {
  const [screen, setScreen] = useState("profile")
  const [profile, setProfile] = useState(null)
  const [text, setText] = useState("")
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState(null)
  const [error, setError] = useState(null)
  const [fileName, setFileName] = useState(null)
  const [uploadedFile, setUploadedFile] = useState(null)
  const [recording, setRecording] = useState(false)
  const fileRef = useRef()
  const mediaRecorderRef = useRef(null)

  async function handleFile(e) {
    const file = e.target.files[0]
    if (!file) return
    setFileName(file.name)
    setUploadedFile(file)
    if (file.type === "text/plain") {
      const t = await file.text()
      setText(t)
    } else {
      setText(`[File ready: ${file.name}] — will be sent directly to backend.`)
    }
  }

  async function handleStart() {
    if (!text.trim()) return
    setLoading(true)
    setError(null)
    try {
      let res
      if (uploadedFile && uploadedFile.type !== "text/plain") {
        res = await apiStartFromFile(uploadedFile)
      } else {
        res = await apiStartSession(text, profile?.id)
      }
      setSessionId(res.session_id)
      setMessages([{ role: "ai", content: res.first_question }])
      setScreen("chat")
    } catch (e) {
      setError("Could not connect to backend. Is the server running?")
    }
    setLoading(false)
  }

  async function handleSend() {
    if (!input.trim()) return
    const userMsg = { role: "user", content: input }
    setMessages(m => [...m, userMsg])
    setInput("")
    setLoading(true)
    try {
      const res = await apiSendMessage(sessionId, input)
      setMessages(m => [...m, { role: "ai", content: res.agent_reply }])
    } catch (e) {
      setMessages(m => [...m, { role: "ai", content: "⚠️ Error reaching backend." }])
    }
    setLoading(false)
  }

  async function handleRecord() {
    if (recording) {
      mediaRecorderRef.current?.stop()
      setRecording(false)
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      const chunks = []
      mediaRecorder.ondataavailable = e => chunks.push(e.data)
      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunks, { type: "audio/webm" })
        const formData = new FormData()
        formData.append("file", blob, "recording.webm")
        try {
          const res = await fetch("http://localhost:8000/transcribe", {
            method: "POST",
            body: formData
          })
          const data = await res.json()
          if (data.text) setInput(data.text)
        } catch {
          setInput("⚠️ Transcription failed — type instead.")
        }
        stream.getTracks().forEach(t => t.stop())
      }
      mediaRecorder.start()
      setRecording(true)
    } catch {
      alert("Microphone access denied.")
    }
  }

  async function handleEvaluate() {
    setLoading(true)
    try {
      const res = await apiEvaluate(sessionId)
      const report = {
        summary: res.summary,
        top_fix: res.top_fix,
        jargon_terms: res.jargon_terms,
        scores: [
          { label: "Clarity", value: res.clarity },
          { label: "Tone", value: res.tone },
        ]
      }
      setReport(report)
      setScreen("report")
    } catch (e) {
      setError("Could not generate report. Is the server running?")
    }
    setLoading(false)
  }

  function startOver() {
    setScreen("profile"); setText(""); setSessionId(null); setProfile(null)
    setMessages([]); setInput(""); setReport(null); setError(null)
    setFileName(null); setUploadedFile(null); setRecording(false)
  }

  const NavBar = () => (
    <div style={s.nav}>
      <span style={{...s.navLogo, fontFamily: handwriting}}>Tech Explained</span>
      <div style={s.navSteps}>
        {["profile","paste","chat","report"].map((n, i) => (
          <span key={n} style={{display:"flex",alignItems:"center",gap:6}}>
            {i > 0 && <span style={{color:"#ccc",fontSize:12}}>›</span>}
            <span style={{...s.navStep, ...(screen===n ? s.navStepActive : {})}}>{n.charAt(0).toUpperCase()+n.slice(1)}</span>
          </span>
        ))}
      </div>
    </div>
  )

  if (screen === "profile") return (
    <div style={{fontFamily: sf, background:"transparent", minHeight:"100vh", position:"relative", zIndex:1}}>
      <NavBar />
      <div style={s.hero}>
        <h1 style={{...s.heroTitle, fontFamily: handwriting, fontSize: 96}}>Tech Explained<br/>for Dummies</h1>
        <p style={s.heroSub}>Choose your interviewer profile to get started.</p>
        <div style={s.profileGrid}>
          {PROFILES.map(p => (
            <div key={p.id}
              style={{...s.profileCard, ...(profile?.id === p.id ? s.profileCardActive : {})}}
              onClick={() => setProfile(p)}>
              <div style={{...s.profileName, ...(profile?.id === p.id ? {color:"#0071e3"} : {})}}>{p.name}</div>
              <div style={s.profileDesc}>{p.desc}</div>
            </div>
          ))}
        </div>
        <button style={{...s.btnApple, opacity: !profile ? 0.5 : 1, marginTop:32}} onClick={() => profile && setScreen("paste")} disabled={!profile}>
          Continue →
        </button>
      </div>
    </div>
  )

  if (screen === "paste") return (
    <div style={{fontFamily: sf, background:"transparent", minHeight:"100vh", position:"relative", zIndex:1}}>
      <NavBar />
      <div style={s.hero}>
        <p style={s.profileBadge}>👤 {profile?.name}</p>
        <h1 style={{...s.heroTitle, fontFamily: handwriting, fontSize: 72}}>Paste your text</h1>
        <p style={s.heroSub}>Your interviewer will ask the questions a {profile?.name} would ask.</p>
        {error && <div style={s.errorBanner}>{error}</div>}
        <div style={s.inputArea}>
          <textarea style={s.textarea} value={text} onChange={e => setText(e.target.value)} placeholder="Paste your abstract, paper, or technical content here…" rows={5} />
          {fileName && (
            <div style={s.fileTag}>
              📎 {fileName}
              <span style={{cursor:"pointer", marginLeft:8, color:"#999"}} onClick={() => { setFileName(null); setUploadedFile(null); setText("") }}>×</span>
            </div>
          )}
          <div style={s.inputFooter}>
            <div style={{display:"flex",gap:6,alignItems:"center"}}>
              <input ref={fileRef} type="file" accept=".txt,.pdf,.doc,.docx,.ppt,.pptx" style={{display:"none"}} onChange={handleFile} />
              <button style={s.attachBtn} onClick={() => fileRef.current.click()}>📎 Upload file</button>
            </div>
            <button style={{...s.btnApple, opacity: (!text.trim() || loading) ? 0.5 : 1}} onClick={handleStart} disabled={loading || !text.trim()}>
              {loading ? "Starting…" : "Begin →"}
            </button>
          </div>
        </div>
      </div>
    </div>
  )

  if (screen === "chat") return (
    <div style={{fontFamily: sf, background:"transparent", minHeight:"100vh", position:"relative", zIndex:1}}>
      <NavBar />
      <div style={s.section}>
        <div style={s.screenHeader}>
          <div>
            <span style={s.screenTitle}>Session</span>
            <span style={s.profilePill}>👤 {profile?.name}</span>
          </div>
          <button style={s.ghostBtn} onClick={startOver}>Start over</button>
        </div>
        <div style={s.chatWrap}>
          {messages.map((m,i) => (
            <div key={i} style={m.role==="user" ? s.bubbleUser : s.bubbleAi}>{m.content}</div>
          ))}
          {loading && <div style={s.bubbleAi}>…</div>}
        </div>
        <div style={s.chatInputRow}>
          <input style={s.chatInput} value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key==="Enter" && handleSend()} placeholder="Put your points here…" />
          <button style={{...s.sendCircle, background: recording ? "#ff3b30" : "#6e6e73", marginRight:4}} onClick={handleRecord} title={recording ? "Stop recording" : "Record audio"}>
            🎙
          </button>
          <button style={s.sendCircle} onClick={handleSend} disabled={loading}>→</button>
        </div>
        {recording && <p style={{fontSize:12, color:"#ff3b30", marginTop:8, textAlign:"center"}}>🔴 Recording… tap mic to stop</p>}
        <button style={{...s.btnApple, width:"100%", marginTop:16, borderRadius:14}} onClick={handleEvaluate} disabled={loading}>
          {loading ? "Generating…" : "Generate report →"}
        </button>
      </div>
    </div>
  )

  if (screen === "report") return (
    <div style={{fontFamily: sf, background:"transparent", minHeight:"100vh", position:"relative", zIndex:1}}>
      <NavBar />
      <div style={s.section}>
        <div style={s.screenHeader}>
          <span style={s.screenTitle}>Your report</span>
          <button style={s.ghostBtn} onClick={startOver}>Start over</button>
        </div>
        {report && <>
          <p style={{fontSize:15, color:"#1d1d1f", marginBottom:28, lineHeight:1.7}}>{report.summary}</p>

          <p style={s.sectionLabel}>CONVERSATION</p>
          <div style={s.chatLog}>
            {messages.map((m,i) => (
              <div key={i} style={m.role==="user" ? s.logUser : s.logAi}>{m.content}</div>
            ))}
          </div>

          <p style={s.sectionLabel}>SCORES</p>
          <div style={s.reportGrid}>
            {report.scores?.map(sc => (
              <div key={sc.label} style={s.metric}>
                <div style={s.metricLabel}>{sc.label}</div>
                <div style={s.metricVal}>
                  {sc.value}
                  <span style={{fontSize:14, color:"#999", fontWeight:400}}>/10</span>
                </div>
                <div style={s.metricBar}>
                  <div style={{...s.metricFill, width: (sc.value * 10)+"%"}} />
                </div>
              </div>
            ))}
          </div>

          <p style={{...s.sectionLabel, marginTop:12}}>JARGON TO SIMPLIFY</p>
          {report.jargon_terms?.map(j => (
            <div key={j.term} style={s.jargonItem}>
              <span style={{color:"#ff3b30", fontWeight:500}}>"{j.term}"</span>
              <span style={{color:"#999", fontSize:12}}>→</span>
              <span style={{color:"#34c759", fontWeight:500}}>"{j.suggestion}"</span>
            </div>
          ))}

          <p style={{...s.sectionLabel, marginTop:24}}>TOP RECOMMENDATION</p>
          <div style={s.topFix}>
            <div style={{fontSize:11, fontWeight:600, color:"#0071e3", letterSpacing:"0.06em", marginBottom:6}}>PRIORITY FIX</div>
            {report.top_fix}
          </div>
        </>}
      </div>
    </div>
  )
}

const s = {
  nav: { display:"flex", justifyContent:"center", alignItems:"center", padding:"18px 40px", position:"relative", background:"rgba(255,255,255,0.6)", backdropFilter:"blur(20px)" },
  navLogo: { fontSize:24, fontWeight:600, color:"#1d1d1f", position:"absolute", left:40 },
  navSteps: { display:"flex", alignItems:"center", gap:6, fontSize:13, color:"#6e6e73" },
  navStep: { padding:"4px 12px", borderRadius:20 },
  navStepActive: { background:"#1d1d1f", color:"#fff" },
  hero: { textAlign:"center", padding:"48px 24px 48px" },
  heroTitle: { fontWeight:800, color:"#1d1d1f", lineHeight:1.02, marginBottom:20 },
  heroSub: { fontSize:18, color:"#444", lineHeight:1.6, maxWidth:560, margin:"0 auto 32px" },
  profileBadge: { fontSize:14, color:"#0071e3", fontWeight:600, marginBottom:12 },
  profileGrid: { display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(200px, 1fr))", gap:12, maxWidth:900, margin:"0 auto 8px", textAlign:"left" },
  profileCard: { background:"rgba(255,255,255,0.7)", backdropFilter:"blur(20px)", borderRadius:16, padding:"16px 18px", cursor:"pointer", transition:"all 0.2s", border:"2px solid transparent" },
  profileCardActive: { background:"rgba(0,113,227,0.06)", border:"2px solid #0071e3", transform:"scale(1.05)", boxShadow:"0 8px 30px rgba(0,113,227,0.15)" },
  profileName: { fontSize:14, fontWeight:600, marginBottom:4, color:"#1d1d1f" },
  profileDesc: { fontSize:12, color:"#6e6e73", lineHeight:1.5 },
  profilePill: { display:"inline-block", fontSize:12, background:"rgba(0,113,227,0.1)", color:"#0071e3", borderRadius:20, padding:"3px 10px", marginLeft:10, fontWeight:500 },
  errorBanner: { background:"#fff0f0", color:"#c0392b", borderRadius:10, padding:"10px 16px", fontSize:13, marginBottom:16, maxWidth:720, margin:"0 auto 16px" },
  inputArea: { background:"rgba(255,255,255,0.7)", backdropFilter:"blur(20px)", borderRadius:20, padding:"20px 24px", margin:"0 auto", maxWidth:720, width:"100%", boxSizing:"border-box", boxShadow:"0 2px 40px rgba(0,0,0,0.06)" },
  textarea: { width:"100%", background:"transparent", fontSize:15, color:"#1d1d1f", fontFamily:"inherit", resize:"none", lineHeight:1.7, boxSizing:"border-box", display:"block" },
  fileTag: { fontSize:12, color:"#6e6e73", background:"rgba(0,0,0,0.04)", borderRadius:8, padding:"4px 10px", display:"inline-block", marginTop:8 },
  inputFooter: { display:"flex", alignItems:"center", justifyContent:"space-between", marginTop:16, paddingTop:14 },
  attachBtn: { fontSize:13, padding:"8px 16px", borderRadius:20, background:"rgba(255,255,255,0.8)", color:"#1d1d1f", cursor:"pointer", fontFamily:"inherit", fontWeight:500 },
  btnApple: { background:"#0071e3", color:"#fff", borderRadius:980, padding:"11px 26px", fontSize:15, fontWeight:500, cursor:"pointer", fontFamily:"inherit" },
  section: { maxWidth:680, margin:"0 auto", padding:"36px 24px 60px" },
  screenHeader: { display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:24 },
  screenTitle: { fontSize:24, fontWeight:700, letterSpacing:"-0.5px", color:"#1d1d1f" },
  ghostBtn: { background:"transparent", borderRadius:980, padding:"8px 18px", fontSize:13, color:"#444", cursor:"pointer", fontFamily:"inherit" },
  chatWrap: { background:"rgba(255,255,255,0.7)", backdropFilter:"blur(20px)", borderRadius:20, padding:20, marginBottom:16, minHeight:200, display:"flex", flexDirection:"column", gap:12, boxShadow:"0 2px 40px rgba(0,0,0,0.06)" },
  bubbleAi: { alignSelf:"flex-start", background:"#fff", borderRadius:"18px 18px 18px 4px", padding:"12px 16px", fontSize:14, color:"#1d1d1f", maxWidth:"80%", lineHeight:1.6 },
  bubbleUser: { alignSelf:"flex-end", background:"#0071e3", borderRadius:"18px 18px 4px 18px", padding:"12px 16px", fontSize:14, color:"#fff", maxWidth:"80%", lineHeight:1.6 },
  chatInputRow: { display:"flex", gap:8, alignItems:"center" },
  chatInput: { flex:1, background:"rgba(255,255,255,0.7)", borderRadius:980, padding:"12px 20px", fontSize:14, color:"#1d1d1f", fontFamily:"inherit" },
  sendCircle: { width:38, height:38, borderRadius:"50%", background:"#0071e3", cursor:"pointer", color:"#fff", fontSize:16, display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0 },
  chatLog: { background:"rgba(255,255,255,0.7)", backdropFilter:"blur(20px)", borderRadius:20, padding:20, marginBottom:24, display:"flex", flexDirection:"column", gap:10, maxHeight:300, overflowY:"auto" },
  logAi: { alignSelf:"flex-start", background:"#f5f5f7", borderRadius:"14px 14px 14px 4px", padding:"10px 14px", fontSize:13, color:"#1d1d1f", maxWidth:"85%", lineHeight:1.5 },
  logUser: { alignSelf:"flex-end", background:"#0071e3", borderRadius:"14px 14px 4px 14px", padding:"10px 14px", fontSize:13, color:"#fff", maxWidth:"85%", lineHeight:1.5 },
  reportGrid: { display:"grid", gridTemplateColumns:"1fr 1fr", gap:12, marginBottom:8 },
  metric: { background:"rgba(255,255,255,0.7)", backdropFilter:"blur(20px)", borderRadius:16, padding:"18px 20px" },
  metricLabel: { fontSize:11, color:"#6e6e73", fontWeight:600, marginBottom:8, letterSpacing:"0.05em" },
  metricVal: { fontSize:32, fontWeight:700, color:"#1d1d1f", letterSpacing:"-0.5px" },
  metricBar: { height:3, background:"#e0e0e5", borderRadius:99, marginTop:12, overflow:"hidden" },
  metricFill: { height:"100%", borderRadius:99, background:"#0071e3" },
  sectionLabel: { fontSize:11, fontWeight:600, color:"#6e6e73", letterSpacing:"0.06em", marginBottom:12 },
  jargonItem: { display:"flex", alignItems:"center", gap:10, padding:"13px 0", fontSize:14 },
  topFix: { background:"rgba(255,255,255,0.7)", backdropFilter:"blur(20px)", borderRadius:16, padding:"18px 20px", fontSize:14, color:"#1d1d1f", lineHeight:1.7 }
}