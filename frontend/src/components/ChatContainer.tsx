"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Sparkles, Clipboard, Square } from "lucide-react";
import MessageBubble from "./MessageBubble";

interface Message {
  role: "user" | "model";
  parts: Array<{ text: string }>;
}

interface ChatContainerProps {
  messages: Message[];
  isGenerating: boolean;
  onSendMessage: (text: string) => void;
  onStopGeneration: () => void;
  activeSessionId: string | null;
}

const QUICK_PROMPTS = [
  { label: "🔍 Search pages", prompt: "Search Notion for pages related to 'project'" },
  { label: "➕ Create page", prompt: "Create a new page under my parent page with title 'Meeting Notes' and content 'Discuss roadmap updates.'" },
  { label: "🗄️ Query databases", prompt: "Retrieve and list all databases available in my workspace" },
  { label: "💬 Add comment", prompt: "Add a comment to block/page ID 'PASTE_ID_HERE' saying 'This requires review.'" }
];

export default function ChatContainer({
  messages,
  isGenerating,
  onSendMessage,
  onStopGeneration,
  activeSessionId,
}: ChatContainerProps) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll helper
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isGenerating]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isGenerating) return;
    onSendMessage(input.trim());
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-black/10 overflow-hidden relative">
      {/* Background radial glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-violet-600/5 rounded-full blur-[120px] pointer-events-none z-0" />
      <div className="absolute bottom-1/4 left-1/3 w-[400px] h-[400px] bg-indigo-600/5 rounded-full blur-[100px] pointer-events-none z-0" />

      {/* Message List */}
      <div className="flex-1 overflow-y-auto px-6 py-8 space-y-4 z-10">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center max-w-xl mx-auto text-center space-y-8 py-12">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-violet-600/10 to-indigo-600/10 border border-violet-500/20 flex items-center justify-center purple-glow">
              <Sparkles className="w-8 h-8 text-violet-400" />
            </div>

            <div className="space-y-3">
              <h2 className="text-2xl font-bold tracking-tight text-white">
                Notion AI Workspace Assistant
              </h2>
              <p className="text-sm text-gray-400 leading-relaxed">
                Interact with your Notion pages, databases, blocks, and comments in plain English. Powered by Gemini & Model Context Protocol.
              </p>
            </div>

            {/* Quick Prompts */}
            <div className="grid grid-cols-2 gap-3.5 w-full pt-4">
              {QUICK_PROMPTS.map((qp, idx) => (
                <button
                  key={idx}
                  onClick={() => setInput(qp.prompt)}
                  className="glass-panel hover:border-violet-500/30 text-left p-4 rounded-xl hover:bg-white/5 transition-all duration-300 group cursor-pointer"
                >
                  <p className="text-xs font-semibold text-violet-400 mb-1 flex items-center justify-between">
                    <span>{qp.label}</span>
                    <Clipboard className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </p>
                  <p className="text-xs text-gray-400 line-clamp-2 leading-relaxed">
                    {qp.prompt}
                  </p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <MessageBubble key={idx} message={msg} />
          ))
        )}

        {/* Typing loader */}
        {isGenerating && (
          <div className="flex w-full space-x-4 p-4 rounded-2xl justify-start select-none">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center purple-glow shrink-0 mt-0.5 animate-pulse">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div className="glass-panel text-gray-200 rounded-2xl rounded-tl-none p-5 flex items-center space-x-3">
              <div className="text-xs font-medium text-violet-400 mr-2">Gemini is thinking</div>
              <div className="flex space-x-1.5 items-center h-2">
                <span className="dot-flashing" />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* User Input Area */}
      <div className="p-6 border-t border-white/10 bg-black/30 backdrop-blur-md z-10">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative">
          <div className="relative flex items-center">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                !activeSessionId
                  ? "Select a conversation or type to start a new chat..."
                  : "Ask anything about your Notion workspace..."
              }
              rows={1}
              className="w-full pl-5 pr-14 py-4 rounded-2xl glass-input text-sm resize-none focus:outline-none scrollbar-none max-h-32 text-gray-100 placeholder-gray-500"
              style={{ height: "54px" }}
            />

            {isGenerating ? (
              <button
                type="button"
                onClick={onStopGeneration}
                aria-label="Stop generating"
                title="Stop generating"
                className="absolute right-2 px-4 py-2.5 rounded-xl flex items-center justify-center transition-all duration-300 bg-rose-500/10 text-rose-300 border border-rose-400/20 hover:bg-rose-500/20 hover:text-white hover:scale-105 active:scale-95 cursor-pointer"
              >
                <Square className="w-4 h-4 fill-current" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim()}
                aria-label="Send message"
                title="Send message"
                className={`absolute right-2 px-4 py-2.5 rounded-xl flex items-center justify-center transition-all duration-300 ${input.trim()
                    ? "bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white hover:scale-105 active:scale-95 shadow-md shadow-violet-900/10 cursor-pointer"
                    : "bg-white/5 text-gray-500 border border-white/5 cursor-not-allowed"
                  }`}
              >
                <Send className="w-4 h-4" />
              </button>
            )}
          </div>
          <p className="text-[10px] text-center text-gray-500 mt-2">
            AI can make mistakes. Verify important information in Notion.
          </p>
        </form>
      </div>
    </div>
  );
}
