"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import { User, Cpu, ExternalLink, FileText } from "lucide-react";

interface Message {
  role: "user" | "model";
  parts: Array<{ text: string }>;
}

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const text = message.parts[0]?.text || "";

  // Regex to detect UUIDs (often Notion Page/Database IDs) to render interactive buttons
  const uuidRegex = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi;
  const ids = text.match(uuidRegex);

  return (
    <div className={`flex w-full space-x-4 p-4 rounded-2xl transition-all duration-300 ${
      isUser 
        ? "justify-end" 
        : "justify-start"
    }`}>
      {/* Avatar (Left for model, none/right for user) */}
      {!isUser && (
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center purple-glow shrink-0 mt-0.5">
          <Cpu className="w-4.5 h-4.5 text-white" />
        </div>
      )}

      {/* Message Content Bubble */}
      <div className={`max-w-[75%] rounded-2xl p-4 flex flex-col space-y-3 ${
        isUser
          ? "bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-900/10 rounded-tr-none"
          : "glass-panel text-gray-200 rounded-tl-none"
      }`}>
        <div className="markdown-content text-sm leading-relaxed break-words select-text">
          {isUser ? (
            <p className="whitespace-pre-wrap">{text}</p>
          ) : (
            <ReactMarkdown>{text}</ReactMarkdown>
          )}
        </div>

        {/* Dynamic Notion resource integration */}
        {!isUser && ids && ids.length > 0 && (
          <div className="pt-2.5 border-t border-white/5 mt-1 space-y-1.5">
            <p className="text-xxs font-semibold text-violet-400 tracking-wider uppercase">
              Detected Notion Reference(s):
            </p>
            <div className="flex flex-wrap gap-2">
              {Array.from(new Set(ids)).map((id) => (
                <a
                  key={id}
                  href={`https://notion.so/${id.replace(/-/g, "")}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-xxs font-medium text-gray-300 hover:text-white hover:bg-white/10 hover:border-violet-500/30 transition-all duration-200"
                >
                  <FileText className="w-3.5 h-3.5 text-violet-400" />
                  <span className="truncate max-w-[120px]">{id}</span>
                  <ExternalLink className="w-3 h-3 text-gray-500" />
                </a>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Avatar for user */}
      {isUser && (
        <div className="w-9 h-9 rounded-xl bg-white/10 border border-white/20 flex items-center justify-center shrink-0 mt-0.5">
          <User className="w-4.5 h-4.5 text-white" />
        </div>
      )}
    </div>
  );
}
