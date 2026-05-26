"use client";

import React from "react";
import { MessageSquare, Plus, Trash2, Database, ShieldCheck, Activity } from "lucide-react";

interface SessionInfo {
  session_id: string;
  created_at: string;
  message_count: number;
}

interface HealthStatus {
  status: string;
  mcp_connected: boolean;
  tools_count: number;
}

interface SidebarProps {
  sessions: SessionInfo[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onCreateSession: () => void;
  onDeleteSession: (id: string) => void;
  healthStatus: HealthStatus | null;
}

export default function Sidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  healthStatus,
}: SidebarProps) {
  // Helper to format date nicely
  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) + 
             " - " + 
             date.toLocaleDateString([], { month: "short", day: "numeric" });
    } catch {
      return isoString;
    }
  };

  return (
    <aside className="w-80 glass-panel border-r border-white/10 flex flex-col h-full z-10 shrink-0">
      {/* Brand Header */}
      <div className="p-6 border-b border-white/10 flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center purple-glow">
          <Database className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-lg leading-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
            Notion AI
          </h1>
          <p className="text-xs text-violet-400 font-medium">Gemini + MCP Server</p>
        </div>
      </div>

      {/* Action Button */}
      <div className="p-4">
        <button
          onClick={onCreateSession}
          className="w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-medium transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-violet-900/20 cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Sessions list */}
      <div className="flex-1 overflow-y-auto px-3 space-y-1.5 py-2">
        <div className="px-3 py-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Recent Conversations
        </div>

        {sessions.length === 0 ? (
          <div className="text-center py-8 text-gray-500 text-sm">
            No active conversations
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.session_id}
              onClick={() => onSelectSession(session.session_id)}
              className={`group flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all duration-200 ${
                activeSessionId === session.session_id
                  ? "bg-white/10 text-white border border-white/10"
                  : "text-gray-400 hover:bg-white/5 hover:text-gray-200 border border-transparent"
              }`}
            >
              <div className="flex items-center space-x-3 min-w-0 flex-1">
                <MessageSquare className={`w-4 h-4 shrink-0 ${
                  activeSessionId === session.session_id ? "text-violet-400" : "text-gray-500"
                }`} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium truncate">
                    {session.session_id.slice(0, 8)}...
                  </p>
                  <p className="text-xxs text-gray-500">
                    {formatDate(session.created_at)} • {session.message_count} msgs
                  </p>
                </div>
              </div>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteSession(session.session_id);
                }}
                className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-red-500/10 hover:text-red-400 text-gray-500 transition-all duration-200 cursor-pointer"
                title="Delete Session"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))
        )}
      </div>

      {/* System Health Dashboard */}
      <div className="p-4 border-t border-white/10 bg-black/20">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
            <Activity className="w-3.5 h-3.5" />
            <span>Connection Health</span>
          </div>
        </div>

        <div className="space-y-2.5">
          {/* API Status */}
          <div className="flex items-center justify-between text-xs glass-panel px-3 py-2 rounded-lg">
            <span className="text-gray-400">FastAPI Gateway</span>
            <div className="flex items-center space-x-1.5">
              <span className={`w-2 h-2 rounded-full ${
                healthStatus ? "bg-emerald-500 animate-pulse" : "bg-rose-500"
              }`} />
              <span className={healthStatus ? "text-emerald-400 font-medium" : "text-rose-400 font-medium"}>
                {healthStatus ? "Connected" : "Offline"}
              </span>
            </div>
          </div>

          {/* MCP Server Status */}
          <div className="flex items-center justify-between text-xs glass-panel px-3 py-2 rounded-lg">
            <span className="text-gray-400">Notion MCP Bridge</span>
            <div className="flex items-center space-x-1.5">
              <span className={`w-2 h-2 rounded-full ${
                healthStatus?.mcp_connected ? "bg-emerald-500 animate-pulse" : "bg-rose-500"
              }`} />
              <span className={healthStatus?.mcp_connected ? "text-emerald-400 font-medium" : "text-rose-400 font-medium"}>
                {healthStatus?.mcp_connected ? "Connected" : "Disconnected"}
              </span>
            </div>
          </div>

          {/* Tools Count */}
          {healthStatus?.mcp_connected && (
            <div className="flex items-center justify-between text-xs px-1 text-gray-500">
              <span className="flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3 text-violet-400" />
                <span>Active tools:</span>
              </span>
              <span className="font-semibold text-violet-400">{healthStatus.tools_count} exposed</span>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
