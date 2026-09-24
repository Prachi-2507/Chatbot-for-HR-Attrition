import { useState, useRef, useEffect } from "react";

const API_URL = "http://localhost:8000";

const ROUTE_LABELS = {
  sql: { label: "Data lookup", color: "#2563eb" },
  rag: { label: "Policy lookup", color: "#059669" },
  hybrid: { label: "Data + Policy", color: "#7c3aed" },
};

function RouteBadge({ type }) {
  const info = ROUTE_LABELS[type] || { label: type, color: "#6b7280" };
  return (
    <span
      style={{
        display: "inline-block",
        fontSize: "0.7rem",
        fontWeight: 600,
        color: "#fff",
        background: info.color,
        borderRadius: "999px",
        padding: "2px 10px",
        marginBottom: "6px",
      }}
    >
      {info.label}
    </span>
  );
}

function Message({ role, content, sourceType, sources, reasoning }) {
  const isUser = role === "user";
  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: "16px",
      }}
    >
      <div
        style={{
          maxWidth: "75%",
          background: isUser ? "#111827" : "#f3f4f6",
          color: isUser ? "#fff" : "#111827",
          borderRadius: "14px",
          padding: "12px 16px",
          whiteSpace: "pre-wrap",
        }}
      >
        {!isUser && sourceType && <RouteBadge type={sourceType} />}
        <div>{content}</div>
        {!isUser && sources && sources.length > 0 && (
          <div style={{ marginTop: "8px", fontSize: "0.75rem", color: "#6b7280" }}>
            Sources: {sources.join(", ")}
          </div>
        )}
        {!isUser && reasoning && (
          <div style={{ marginTop: "4px", fontSize: "0.7rem", color: "#9ca3af", fontStyle: "italic" }}>
            Routing: {reasoning}
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hi! I'm InsightHR. Ask me about HR data (e.g. attrition rates) or company policy (e.g. overtime rules) — or both at once.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage() {
    const question = input.trim();
    if (!question || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.detail || "Request failed");
      }

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          sourceType: data.source_type,
          sources: data.rag_sources,
          reasoning: data.routing?.reasoning,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${err.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div
      style={{
        maxWidth: "720px",
        margin: "0 auto",
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <header style={{ padding: "20px 16px 12px", borderBottom: "1px solid #e5e7eb" }}>
        <h1 style={{ fontSize: "1.25rem", margin: 0 }}>InsightHR</h1>
        <p style={{ fontSize: "0.8rem", color: "#6b7280", margin: "4px 0 0" }}>
          Hybrid RAG + SQL assistant over HR data and policy docs
        </p>
      </header>

      <div style={{ flex: 1, overflowY: "auto", padding: "16px" }}>
        {messages.map((m, i) => (
          <Message key={i} role={m.role} content={m.content} sourceType={m.sourceType} sources={m.sources} reasoning={m.reasoning} />
        ))}
        {loading && (
          <div style={{ color: "#9ca3af", fontSize: "0.85rem" }}>Thinking...</div>
        )}
        <div ref={bottomRef} />
      </div>

      <div style={{ display: "flex", gap: "8px", padding: "16px", borderTop: "1px solid #e5e7eb" }}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about attrition, policy, or both..."
          rows={1}
          style={{
            flex: 1,
            resize: "none",
            padding: "10px 12px",
            borderRadius: "10px",
            border: "1px solid #d1d5db",
            fontFamily: "inherit",
            fontSize: "0.9rem",
          }}
        />
        <button
          onClick={sendMessage}
          disabled={loading}
          style={{
            padding: "10px 18px",
            borderRadius: "10px",
            border: "none",
            background: "#111827",
            color: "#fff",
            fontWeight: 600,
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
