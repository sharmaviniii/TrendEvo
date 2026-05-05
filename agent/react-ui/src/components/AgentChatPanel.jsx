import { useState, useRef, useEffect } from "react";

export default function AgentChatPanel() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [city, setCity] = useState("Delhi");
    const [loading, setLoading] = useState(false);
    
    const messagesEndRef = useRef(null);
    
    // Auto scroll
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);
    
    const sendMessage = async () => {
        if (!input.trim()) return;
        
        const userMessage = {
            role: "user",
            content: input,
        };
        
        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setLoading(true);
        
        try {
            const res = await fetch("http://127.0.0.1:8000/agent/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    user_id: "user123",
                    message: userMessage.content,
                    city: city,
                }),
            });
            
            const data = await res.json();
            
            const agentMessage = {
                role: "agent",
                content: data.reply || "No response from agent",
            };
            
            setMessages((prev) => [...prev, agentMessage]);
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                {
                    role: "agent",
                    content: "⚠️ Error connecting to agent",
                },
            ]);
        }
        
        setLoading(false);
    };
    
    return (
        <div style={{ padding: "20px", color: "white" }}>
        
        <h2>TrendÉvo Agent</h2>
        
        {/* City Input */}
        <input
        value={city}
        onChange={(e) => setCity(e.target.value)}
        placeholder="Enter city"
        style={{ padding: "8px", marginBottom: "10px" }}
        />
        
        {/* Chat Box */}
        <div
        style={{
            height: "400px",
            overflowY: "auto",
            border: "1px solid #333",
            padding: "10px",
            marginBottom: "10px",
        }}
        >
        {messages.map((msg, i) => (
            <div
            key={i}
            style={{
                textAlign: msg.role === "user" ? "right" : "left",
                marginBottom: "10px",
            }}
            >
            <span
            style={{
                display: "inline-block",
                padding: "10px",
                borderRadius: "10px",
                background:
                msg.role === "user" ? "#f3c46b" : "#1f2937",
                color: msg.role === "user" ? "#000" : "#fff",
            }}
            >
            {msg.content}
            </span>
            </div>
        ))}
        
        {loading && (
            <div className="agent-loading">
            <div className="dots">
            <span className="dot"></span>
            <span className="dot"></span>
            <span className="dot"></span>
            </div>
            <p>Thinking...</p>
            </div>
        )}
        
        <div ref={messagesEndRef} />
        </div>
        
        {/* Input */}
        <div style={{ display: "flex", gap: "10px" }}>
        <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask something..."
        style={{ flex: 1, padding: "10px" }}
        />
        <button onClick={sendMessage}>Send</button>
        </div>
        </div>
    );
}