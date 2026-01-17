"use client";

import React, { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Plus,
  Search,
  Image as ImageIcon,
  LayoutGrid,
  Code,
  Compass,
  MessageSquare,
  UserCircle,
  Settings,
  Mic,
  ArrowUp,
  History,
  Briefcase,
  GraduationCap,
  Sparkles,
  ChevronDown,
  MoreHorizontal
} from "lucide-react";
import Image from "next/image";

interface Message {
  role: "user" | "assistant" | "error";
  content: string;
}

interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
}

export default function Home() {
  const [message, setMessage] = useState("");
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Initialize with a new chat if no sessions exist
  useEffect(() => {
    if (sessions.length === 0) {
      createNewChat();
    }
  }, []);

  const currentSession = sessions.find(s => s.id === currentSessionId);
  const chatHistory = currentSession?.messages || [];

  const createNewChat = () => {
    const newId = "session_" + Math.random().toString(36).substr(2, 9);
    const newSession: ChatSession = {
      id: newId,
      title: "New chat",
      messages: []
    };
    setSessions(prev => [newSession, ...prev]);
    setCurrentSessionId(newId);
    setMessage("");
  };

  const handleSend = async () => {
    if (!message.trim() || !currentSessionId) return;

    const userMsgContent = message.trim();
    const userMessage: Message = { role: "user", content: userMsgContent };

    // Update local state for messages
    setSessions(prev => prev.map(s => {
      if (s.id === currentSessionId) {
        // Update title if it's the first message
        const newTitle = s.messages.length === 0 ? userMsgContent.substring(0, 30) + (userMsgContent.length > 30 ? "..." : "") : s.title;
        return { ...s, title: newTitle, messages: [...s.messages, userMessage] };
      }
      return s;
    }));

    setMessage("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8005/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: currentSessionId,
          message: userMsgContent,
        }),
      });

      const data = await response.json();
      const botMessage: Message = { role: "assistant", content: data.answer };

      setSessions(prev => prev.map(s => {
        if (s.id === currentSessionId) {
          return { ...s, messages: [...s.messages, botMessage] };
        }
        return s;
      }));
    } catch (error) {
      console.error("Error calling chat API:", error);
      setSessions(prev => prev.map(s => {
        if (s.id === currentSessionId) {
          return { ...s, messages: [...s.messages, { role: "error", content: "Failed to connect to the assistant. Is the FastAPI server running?" }] };
        }
        return s;
      }));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#212121] text-white">
      {/* Sidebar */}
      <aside className="w-[260px] bg-[#171717] flex flex-col h-full border-r border-[#2f2f2f]">
        <div className="p-3 flex items-center justify-between">
          <button
            onClick={createNewChat}
            className="flex items-center gap-2 p-2 hover:bg-[#212121] rounded-lg transition-colors w-full text-left">
            <div className="p-1 bg-[#212121] rounded-full border border-[#3c3c3c]">
              <Plus className="w-4 h-4" />
            </div>
            <span className="text-sm font-medium">New chat</span>
          </button>
          <button className="p-2 hover:bg-[#212121] rounded-lg text-[#b4b4b4]">
            <History className="w-4 h-4" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 space-y-1">


          <div className="mt-8 mb-2 px-3 text-[11px] font-semibold text-[#8e8e8e] uppercase tracking-wider">Your chats</div>
          <div className="space-y-1">
            {sessions.map((s) => (
              <ChatItem
                key={s.id}
                label={s.title}
                active={s.id === currentSessionId}
                onClick={() => {
                  setCurrentSessionId(s.id);
                  setMessage("");
                }}
              />
            ))}
          </div>
        </nav>

        {/* User Profile */}
        <div className="p-3 border-t border-[#2f2f2f]">
          <button className="flex items-center gap-3 p-2 hover:bg-[#212121] rounded-lg w-full transition-colors group">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold text-white uppercase">
              G
            </div>
            <div className="flex-1 text-left">
              <div className="text-sm font-medium">Guest</div>
              <div className="text-xs text-[#8e8e8e]">Free</div>
            </div>
            <MoreHorizontal className="w-4 h-4 text-[#8e8e8e] group-hover:text-white" />
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        {/* Header */}
        <header className="absolute top-0 w-full p-4 flex justify-between items-center z-10">
          <button className="flex items-center gap-1 px-3 py-1.5 hover:bg-[#2f2f2f] rounded-lg transition-colors">
            <span className="font-semibold text-lg flex items-center gap-2">
              Richmond Policy Assistant
            </span>
            <ChevronDown className="w-4 h-4 text-[#8e8e8e]" />
          </button>
          <div className="flex items-center gap-4">
            <button className="p-2 hover:bg-[#2f2f2f] rounded-full text-[#b4b4b4]">
              <UserCircle className="w-5 h-5" />
            </button>
            <button className="p-2 hover:bg-[#2f2f2f] rounded-full text-[#b4b4b4]">
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* Chat Content */}
        <div className="flex-1 overflow-y-auto flex flex-col items-center p-4">
          {chatHistory.length === 0 ? (
            <div className="flex flex-col items-center max-w-2xl text-center mt-[15vh]">
              <h1 className="text-4xl font-semibold mb-8">How can I help you with University policies?</h1>
              <div className="grid grid-cols-2 gap-3 w-full max-w-xl">
                <SuggestionCard title="Richmond Drug Policy" desc="Ask about university rules" onClick={() => setMessage("What is the Richmond drug policy?")} />
                <SuggestionCard title="Academic Integrity" desc="Ask about student conduct" onClick={() => setMessage("Explain the academic integrity policy.")} />
                <SuggestionCard title="Inclement Weather" desc="Ask about school closures" onClick={() => setMessage("What happens during inclement weather?")} />
                <SuggestionCard title="Catering Minimums" desc="Ask about event planning" onClick={() => setMessage("What are the catering minimums?")} />
              </div>
            </div>
          ) : (
            <div className="w-full max-w-3xl flex flex-col gap-6 pt-20 pb-32">
              {chatHistory.map((msg, i) => (
                <div key={i} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-full border border-[#3c3c3c] flex items-center justify-center shrink-0">
                      <Sparkles className="w-5 h-5 text-[#10a37f]" />
                    </div>
                  )}
                  <div className={`p-3 rounded-2xl max-w-[85%] ${msg.role === 'user' ? 'bg-[#2f2f2f] text-white px-5' : 'text-[#ececec]'
                    }`}>
                    {msg.role === 'assistant' ? (
                      <div className="prose prose-invert max-w-none">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            ol: ({ node, ...props }) => <ol className="list-decimal pl-6 my-2 space-y-1" {...props} />,
                            ul: ({ node, ...props }) => <ul className="list-disc pl-6 my-2 space-y-1" {...props} />,
                            li: ({ node, ...props }) => <li className="pl-1" {...props} />,
                            p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />
                          }}
                        >
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    ) : msg.content}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex gap-4 animate-pulse">
                  <div className="w-8 h-8 rounded-full border border-[#3c3c3c] flex items-center justify-center shrink-0">
                    <Sparkles className="w-5 h-5 text-[#10a37f]/50" />
                  </div>
                  <div className="h-4 w-24 bg-[#2f2f2f] rounded mt-3"></div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="absolute bottom-0 w-full p-4 flex justify-center bg-gradient-to-t from-[#212121] via-[#212121] to-transparent">
          <div className="w-full max-w-3xl flex flex-col gap-2">
            <div className="relative flex items-center bg-[#2f2f2f] rounded-[26px] p-2 pr-3 shadow-xl border border-transparent focus-within:border-[#424242] transition-all">
              <button className="p-2 ml-1 text-[#b4b4b4] hover:text-white transition-colors">
                <Plus className="w-5 h-5" />
              </button>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask anything"
                rows={1}
                className="flex-1 bg-transparent border-none focus:ring-0 text-white p-2 resize-none max-h-40 outline-none placeholder-[#8e8e8e]"
              />
              <div className="flex items-center gap-1">
                <button className="p-2 text-[#b4b4b4] hover:text-white transition-colors">
                  <Mic className="w-5 h-5" />
                </button>
                <button
                  onClick={handleSend}
                  disabled={!message.trim() || isLoading}
                  className={`p-1.5 rounded-full transition-all ${message.trim() && !isLoading ? 'bg-white text-black' : 'bg-[#171717] text-[#424242]'
                    }`}>
                  <ArrowUp className="w-5 h-5 font-bold" />
                </button>
              </div>
            </div>

          </div>
        </div>
      </main>
    </div>
  );
}

function SidebarItem({ icon, label }: { icon?: React.ReactNode, label: string }) {
  return (
    <button className="flex items-center gap-3 w-full p-2.5 hover:bg-[#212121] rounded-lg transition-colors text-sm text-[#ececec]">
      {icon ? icon : <LayoutGrid className="w-4 h-4 text-transparent" />}
      <span className="flex-1 text-left">{label}</span>
      <MoreHorizontal className="w-4 h-4 opacity-0 group-hover:opacity-100" />
    </button>
  );
}

function ChatItem({ label, active = false, onClick }: { label: string, active?: boolean, onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`w-full p-2.5 rounded-lg transition-colors text-sm text-left truncate relative group ${active ? 'bg-[#212121]' : 'hover:bg-[#212121]'
        }`}>
      <span className={active ? 'text-white' : 'text-[#ececec]'}>{label}</span>
      <div className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 bg-gradient-to-l from-[#212121] to-transparent pl-4">
        <MoreHorizontal className="w-4 h-4 text-[#8e8e8e]" />
      </div>
    </button>
  );
}

function SuggestionCard({ title, desc, onClick }: { title: string, desc: string, onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="p-4 border border-[#3c3c3c] rounded-2xl text-left hover:bg-[#2f2f2f] transition-colors group">
      <div className="text-sm font-medium mb-1">{title}</div>
      <div className="text-xs text-[#8e8e8e] group-hover:text-[#b4b4b4]">{desc}</div>
    </button>
  );
}
