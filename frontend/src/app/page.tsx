"use client";

import React, { useState, useEffect, useRef } from "react";
import Sidebar from "@/components/Sidebar";
import ChatContainer from "@/components/ChatContainer";
import ExecutionTrace from "@/components/ExecutionTrace";
import confetti from "canvas-confetti";
import { AlertCircle, RefreshCw } from "lucide-react";

interface SessionInfo {
  session_id: string;
  created_at: string;
  message_count: number;
}

interface Message {
  role: "user" | "model";
  parts: Array<{ text: string }>;
}

interface HealthStatus {
  status: string;
  mcp_connected: boolean;
  tools_count: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const isAbortError = (err: unknown) =>
  err instanceof DOMException && err.name === "AbortError";

export default function Home() {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const requestIdRef = useRef(0);

  // 1. Fetch Sessions List
  const fetchSessions = async () => {
    try {
      const res = await fetch(`${API_BASE}/sessions`);
      if (!res.ok) throw new Error("Failed to load sessions");
      const data = await res.json();
      setSessions(data);
      setError(null);
    } catch (err: unknown) {
      console.error(err);
      setError("Could not connect to FastAPI server. Make sure it is running on port 8000.");
    }
  };

  // 2. Fetch Server Health
  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        const data = await res.json();
        setHealthStatus(data);
      } else {
        setHealthStatus(null);
      }
    } catch {
      setHealthStatus(null);
    }
  };

  // 3. Load Session Details (History)
  const loadSession = async (sessionId: string) => {
    try {
      handleStopGeneration();
      const res = await fetch(`${API_BASE}/sessions/${sessionId}`);
      if (!res.ok) throw new Error("Failed to load session details");
      const data = await res.json();
      setMessages(data.history || []);
      setActiveSessionId(sessionId);
    } catch (err: unknown) {
      console.error(err);
      setError("Failed to load conversation history.");
    }
  };

  // 4. Create New Session
  const handleCreateSession = async () => {
    try {
      const res = await fetch(`${API_BASE}/sessions`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to create session");
      const newSession: SessionInfo = await res.json();

      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.session_id);
      setMessages([]);
      setError(null);
    } catch (err: unknown) {
      console.error(err);
      setError("Failed to create new conversation.");
    }
  };

  // 5. Delete Session
  const handleDeleteSession = async (sessionId: string) => {
    try {
      const res = await fetch(`${API_BASE}/sessions/${sessionId}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to delete session");

      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
        setMessages([]);
      }
    } catch (err: unknown) {
      console.error(err);
      setError("Failed to delete conversation.");
    }
  };

  // 6. Send Message to Agent
  const handleSendMessage = async (text: string) => {
    let currentSessionId = activeSessionId;
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    abortControllerRef.current?.abort();
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // Optimistic UI updates
    const newUserMsg: Message = { role: "user", parts: [{ text }] };
    setMessages((prev) => [...prev, newUserMsg]);
    setIsGenerating(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          session_id: currentSessionId,
        }),
        signal: abortController.signal,
      });

      if (!res.ok) {
        throw new Error(await res.text() || "Chat failed");
      }

      const data = await res.json();
      if (requestIdRef.current !== requestId || abortController.signal.aborted) {
        return;
      }

      // If we created a session implicitly
      if (data.created_session || !currentSessionId) {
        setActiveSessionId(data.session_id);
        currentSessionId = data.session_id;
        fetchSessions();
      }

      const agentMsg: Message = { role: "model", parts: [{ text: data.response }] };
      setMessages((prev) => [...prev, agentMsg]);

      // Update message counts in sidebar sessions list
      setSessions((prev) =>
        prev.map((s) =>
          s.session_id === currentSessionId
            ? { ...s, message_count: s.message_count + 2 }
            : s
        )
      );

      // Delightful micro-interaction: Pop confetti if page or database was created
      if (
        /created|success|added/i.test(data.response) &&
        /page|database|comment/i.test(data.response)
      ) {
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 },
          colors: ["#8b5cf6", "#6366f1", "#a78bfa", "#c084fc"]
        });
      }

    } catch (err: unknown) {
      if (isAbortError(err)) {
        return;
      }
      console.error(err);
      setError("Failed to send message or receive response from Gemini.");
      // Rollback last message
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      if (requestIdRef.current === requestId) {
        abortControllerRef.current = null;
        setIsGenerating(false);
      }
    }
  };

  const handleStopGeneration = () => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    requestIdRef.current += 1;
    setIsGenerating(false);
  };

  // Initial load and periodic polling
  useEffect(() => {
    const bootTimer = window.setTimeout(() => {
      void fetchSessions();
      void checkHealth();
    }, 0);

    // Poll server health every 8 seconds
    const interval = setInterval(checkHealth, 8000);
    return () => {
      window.clearTimeout(bootTimer);
      clearInterval(interval);
      abortControllerRef.current?.abort();
    };
  }, []);

  return (
    <div className="flex h-screen w-screen bg-[#060608] text-[#f4f4f7] overflow-hidden">
      {/* Sidebar (Session management) */}
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={loadSession}
        onCreateSession={handleCreateSession}
        onDeleteSession={handleDeleteSession}
        healthStatus={healthStatus}
      />

      {/* Main Work Area */}
      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Error Header Alert */}
        {error && (
          <div className="bg-rose-500/10 border-b border-rose-500/20 px-6 py-3 flex items-center justify-between text-sm text-rose-400 z-20">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4.5 h-4.5 shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={() => { fetchSessions(); checkHealth(); }}
              className="p-1 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Chat Window */}
        <ChatContainer
          messages={messages}
          isGenerating={isGenerating}
          onSendMessage={handleSendMessage}
          onStopGeneration={handleStopGeneration}
          activeSessionId={activeSessionId}
        />
      </main>

      {/* Right Drawer (Execution Flow Trace) */}
      <ExecutionTrace isGenerating={isGenerating} healthStatus={healthStatus} />
    </div>
  );
}
