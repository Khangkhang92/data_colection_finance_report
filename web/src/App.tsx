import { FormEvent, useEffect, useMemo, useState } from "react";

type ChatMessage = { role: "user" | "assistant"; content: string };
type Conversation = { id: string; title: string; updatedAt: number; messages: ChatMessage[] };

type RagSource = { chunk_id: string; score: number; content: string };

type RagResponse = {
  question: string;
  answer: string;
  sources: RagSource[];
};
type RagHistoryMessage = {
  id: number;
  conversation_id: string;
  user_id: string | null;
  role: "user" | "assistant";
  content: string;
};
type RagHistoryResponse = {
  conversation_id: string;
  messages: RagHistoryMessage[];
};

const STORAGE_KEY = "finance_rag_chat_history_v1";
const defaultMessage: ChatMessage = {
  role: "assistant",
  content: "Ask about finance data, metrics, or documents.",
};

function createConversation(): Conversation {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    title: "New chat",
    updatedAt: Date.now(),
    messages: [defaultMessage],
  };
}

export function App() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string>("");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      const first = createConversation();
      setConversations([first]);
      setActiveId(first.id);
      return;
    }
    try {
      const parsed = JSON.parse(raw) as Conversation[];
      if (!parsed.length) throw new Error("empty");
      setConversations(parsed);
      setActiveId(parsed[0].id);
    } catch {
      const first = createConversation();
      setConversations([first]);
      setActiveId(first.id);
    }
  }, []);

  useEffect(() => {
    if (conversations.length) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    }
  }, [conversations]);

  useEffect(() => {
    if (!activeConversation) return;
    const loadHistory = async () => {
      try {
        const res = await fetch(
          `/fireant_data/rag/chat/history?conversation_id=${encodeURIComponent(activeConversation.id)}&limit=200`
        );
        if (!res.ok) return;
        const data = (await res.json()) as RagHistoryResponse;
        const loadedMessages: ChatMessage[] = data.messages.map((m) => ({
          role: m.role,
          content: m.content,
        }));
        if (!loadedMessages.length) return;
        patchActiveConversation((conv) => ({
          ...conv,
          messages: loadedMessages,
          updatedAt: Date.now(),
        }));
      } catch {
        // Keep local conversation state on history fetch failure.
      }
    };
    void loadHistory();
  }, [activeId]);

  const activeConversation = useMemo(
    () => conversations.find((c) => c.id === activeId) ?? conversations[0],
    [conversations, activeId]
  );
  const messages = activeConversation?.messages ?? [defaultMessage];

  const patchActiveConversation = (updater: (conv: Conversation) => Conversation) => {
    setConversations((prev) =>
      prev.map((conv) => (conv.id === activeConversation.id ? updater(conv) : conv))
        .sort((a, b) => b.updatedAt - a.updatedAt)
    );
  };

  const createNewChat = () => {
    const next = createConversation();
    setConversations((prev) => [next, ...prev]);
    setActiveId(next.id);
    setInput("");
  };

  const deleteConversation = (id: string) => {
    setConversations((prev) => {
      const next = prev.filter((c) => c.id !== id);
      if (!next.length) {
        const first = createConversation();
        setActiveId(first.id);
        return [first];
      }
      if (id === activeId) setActiveId(next[0].id);
      return next;
    });
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading || !activeConversation) return;

    setInput("");
    patchActiveConversation((conv) => {
      const nextMessages = [...conv.messages, { role: "user" as const, content: question }];
      return {
        ...conv,
        messages: nextMessages,
        title: conv.title === "New chat" ? question.slice(0, 48) : conv.title,
        updatedAt: Date.now(),
      };
    });
    setLoading(true);

    try {
      const res = await fetch("/fireant_data/rag/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: question,
          conversation_id: activeConversation.id,
          user_id: null,
          top_k: 4,
        }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = (await res.json()) as RagResponse;
      const cites = data.sources
        .slice(0, 3)
        .map((s) => `• ${s.chunk_id} (score ${s.score})`)
        .join("\n");

      patchActiveConversation((conv) => ({
        ...conv,
        messages: [
          ...conv.messages,
          {
            role: "assistant",
            content: cites ? `${data.answer}\n\nSources:\n${cites}` : data.answer,
          },
        ],
        updatedAt: Date.now(),
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      patchActiveConversation((conv) => ({
        ...conv,
        messages: [...conv.messages, { role: "assistant", content: `Request failed: ${message}` }],
        updatedAt: Date.now(),
      }));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="chat-shell accent-border with-history">
        <aside className="history-panel">
          <div className="history-head">
            <h2>Chats</h2>
            <button onClick={createNewChat} type="button">+ New</button>
          </div>
          <div className="history-list">
            {conversations.map((conv) => (
              <div key={conv.id} className={`history-item ${conv.id === activeId ? "active" : ""}`}>
                <button type="button" className="history-select" onClick={() => setActiveId(conv.id)}>
                  <span>{conv.title || "Untitled"}</span>
                </button>
                <button type="button" className="history-delete" onClick={() => deleteConversation(conv.id)}>
                  ×
                </button>
              </div>
            ))}
          </div>
        </aside>
        <section className="chat-main">
          <header className="chat-header">
            <h1>Finance RAG Chat</h1>
            <p>Confluence-style interface, chat-only workflow.</p>
          </header>

          <main className="chat-body">
            {messages.map((msg, idx) => (
              <div key={idx} className={`bubble ${msg.role}`}>
                {msg.content}
              </div>
            ))}
            {loading && <div className="bubble assistant">Thinking...</div>}
          </main>

          <form className="chat-input" onSubmit={onSubmit}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a finance question..."
            />
            <button type="submit" disabled={loading || !input.trim()}>
              Send
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}
