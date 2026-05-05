import { useCallback, useEffect, useRef, useState } from "react";
import axios from "axios";

const USER_KEY = "trendevo_agent_user_id";
const SESSION_KEY = "trendevo_agent_session_id";

function loadOrCreateUserId() {
  let id = localStorage.getItem(USER_KEY);
  if (!id) {
    id = `browser-${crypto.randomUUID?.() ?? Date.now()}`;
    localStorage.setItem(USER_KEY, id);
  }
  return id;
}

function loadSessionId() {
  return localStorage.getItem(SESSION_KEY) || "";
}

function saveSessionId(sid) {
  if (sid) localStorage.setItem(SESSION_KEY, sid);
}

export default function App() {
  const [userId] = useState(() => loadOrCreateUserId());
  const [city, setCity] = useState("");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setError("");
    setMessages((m) => [...m, { role: "user", text }]);
    setLoading(true);

    const body = {
      user_id: userId,
      message: text,
      session_id: loadSessionId() || undefined,
      city: city.trim() || undefined,
    };

    try {
      const { data } = await axios.post("/agent/chat", body, {
        headers: { "Content-Type": "application/json" },
        validateStatus: () => true,
      });
      if (data.session_id) saveSessionId(data.session_id);
      if (data.success === false || data.message) {
        setError(data.message || "Request failed");
        setMessages((m) => [
          ...m,
          { role: "agent", text: data.reply || String(data.message || "Error"), raw: data },
        ]);
        return;
      }
      setMessages((m) => [
        ...m,
        {
          role: "agent",
          text: data.reply || "",
          reasoning: data.reasoning_chain || [],
          outfits: data.outfits || [],
          tools: data.tools_used || [],
          raw: data,
        },
      ]);
    } catch (e) {
      console.error(e);
      setError(e.message || "Network error — is the API running on port 8000?");
      setMessages((m) => [
        ...m,
        {
          role: "agent",
          text: "Could not reach TrendÉvo Agent. Start FastAPI: `python -m uvicorn agent.main:app --reload --port 8000` from the repo root.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, userId, city]);

  return (
    <div className="layout">
      <header className="header">
        <div>
          <h1 className="title">TrendÉvo Agent</h1>
          <p className="subtitle">LangChain + FastAPI (port 8000) · dev UI (Vite)</p>
        </div>
        <div className="header-actions">
          <a className="pill-link" href="http://127.0.0.1:5000/shop" target="_blank" rel="noreferrer">
            ← TrendÉvo Shop
          </a>
          <a className="pill-link" href="http://127.0.0.1:5000/frontend/shop.html" target="_blank" rel="noreferrer">
            Shop (static)
          </a>
        </div>
      </header>

      <div className="toolbar">
        <label className="field">
          <span>City (optional)</span>
          <input
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="e.g. Mumbai"
          />
        </label>
        <span className="user-pill">User: {userId.slice(0, 12)}…</span>
      </div>

      {error ? <div className="banner error">{error}</div> : null}

      <main className="chat-panel">
        {messages.length === 0 ? (
          <p className="hint">
            Ask for an outfit, trends, or weather-aware styling. This page talks to{" "}
            <code>/agent/chat</code> on the Vite dev server, which proxies to{" "}
            <code>http://127.0.0.1:8000</code>.
          </p>
        ) : null}
        {messages.map((msg, i) =>
          msg.role === "user" ? (
            <div key={i} className="bubble user">
              {msg.text}
            </div>
          ) : (
            <div key={i} className="bubble agent">
              <div className="bubble-text">{msg.text}</div>
              {msg.tools?.length ? (
                <div className="tools">Tools: {msg.tools.join(", ")}</div>
              ) : null}
              {msg.reasoning?.length ? (
                <details className="thinking">
                  <summary>🧠 Agent thinking</summary>
                  <ol className="chain">
                    {msg.reasoning.map((step) => (
                      <li key={step.step}>
                        {step.thought ? (
                          <div className="step thought">🔍 {step.thought}</div>
                        ) : null}
                        {step.action ? (
                          <div className="step action">⚡ {step.action}</div>
                        ) : null}
                        {step.observation ? (
                          <div className="step obs">👁 {step.observation}</div>
                        ) : null}
                      </li>
                    ))}
                  </ol>
                </details>
              ) : null}
              {msg.outfits?.length ? (
                <div className="outfits">
                  {msg.outfits.map((o) => (
                    <div key={o.outfit_id} className="outfit-card">
                      <strong>{o.name}</strong>{" "}
                      <span className="vibe">{o.vibe_tag}</span>
                      <p className="reason">{o.reasoning}</p>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          )
        )}
        {loading ? <div className="bubble agent loading">Thinking…</div> : null}
        <div ref={bottomRef} />
      </main>

      <footer className="composer">
        <input
          className="composer-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Message TrendÉvo Agent…"
        />
        <button type="button" className="send" onClick={send} disabled={loading}>
          Send
        </button>
      </footer>
    </div>
  );
}
