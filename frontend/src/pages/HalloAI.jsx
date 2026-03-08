import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  Send, Bot, User, RefreshCw, Loader2, Plus, Trash2, MessageSquare,
  Crown, DollarSign, Settings, Megaphone, ShoppingCart, Headphones, BarChart3,
  Sparkles, ChevronRight, X
} from 'lucide-react';
import { toast } from 'sonner';

const HalloAI = () => {
  const { api, user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [selectedPersona, setSelectedPersona] = useState('analyst');
  const [personas, setPersonas] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [showSidebar, setShowSidebar] = useState(true);
  const messagesEndRef = useRef(null);

  const personaIcons = {
    ceo: Crown,
    cfo: DollarSign,
    coo: Settings,
    cmo: Megaphone,
    sales: ShoppingCart,
    customer_service: Headphones,
    analyst: BarChart3
  };

  const personaColors = {
    ceo: 'from-amber-600 to-yellow-500',
    cfo: 'from-green-600 to-emerald-500',
    coo: 'from-blue-600 to-cyan-500',
    cmo: 'from-purple-600 to-pink-500',
    sales: 'from-orange-600 to-red-500',
    customer_service: 'from-cyan-600 to-teal-500',
    analyst: 'from-pink-600 to-rose-500'
  };

  useEffect(() => {
    loadPersonas();
    loadSessions();
  }, []);

  useEffect(() => {
    loadSuggestions();
  }, [selectedPersona]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadPersonas = async () => {
    try {
      const res = await api('/api/hallo-ai/personas');
      if (res.ok) setPersonas(await res.json());
    } catch (err) { console.error(err); }
  };

  const loadSuggestions = async () => {
    try {
      const res = await api(`/api/hallo-ai/suggested-questions?persona=${selectedPersona}`);
      if (res.ok) {
        const data = await res.json();
        setSuggestions(data.suggestions || []);
      }
    } catch (err) { console.error(err); }
  };

  const loadSessions = async () => {
    try {
      const res = await api('/api/hallo-ai/sessions');
      if (res.ok) setSessions(await res.json());
    } catch (err) { console.error(err); }
  };

  const loadSessionHistory = async (sid) => {
    try {
      const res = await api(`/api/hallo-ai/sessions/${sid}/history`);
      if (res.ok) {
        const data = await res.json();
        setSessionId(sid);
        setMessages(data.messages || []);
      }
    } catch (err) { 
      toast.error('Gagal memuat riwayat chat');
    }
  };

  const startNewChat = () => {
    setMessages([]);
    setSessionId(null);
  };

  const deleteSession = async (sid, e) => {
    e.stopPropagation();
    try {
      const res = await api(`/api/hallo-ai/sessions/${sid}`, { method: 'DELETE' });
      if (res.ok) {
        toast.success('Sesi dihapus');
        loadSessions();
        if (sid === sessionId) startNewChat();
      }
    } catch (err) { toast.error('Gagal menghapus sesi'); }
  };

  const sendMessage = async (text = null) => {
    const messageText = text || input.trim();
    if (!messageText) return;

    const userMessage = { role: 'user', content: messageText };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const res = await api('/api/hallo-ai/chat', {
        method: 'POST',
        body: JSON.stringify({
          message: messageText,
          session_id: sessionId,
          persona: selectedPersona
        })
      });

      if (res.ok) {
        const data = await res.json();
        if (!sessionId) setSessionId(data.session_id);
        
        const aiMessage = { role: 'assistant', content: data.response };
        setMessages(prev => [...prev, aiMessage]);
        loadSessions();
      } else {
        toast.error('Gagal mengirim pesan');
      }
    } catch (err) {
      toast.error('Terjadi kesalahan');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const currentPersona = personas.find(p => p.id === selectedPersona) || {};
  const PersonaIcon = personaIcons[selectedPersona] || Bot;
  const personaGradient = personaColors[selectedPersona] || 'from-purple-600 to-blue-500';

  return (
    <div className="flex h-[calc(100vh-7rem)] gap-4" data-testid="hallo-ai-page">
      {/* Sidebar */}
      {showSidebar && (
        <div className="w-80 bg-[#1a1214] border border-red-900/30 rounded-xl flex flex-col">
          {/* Header */}
          <div className="p-4 border-b border-red-900/30">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-gradient-to-br from-purple-600 to-blue-600 rounded-xl">
                <Sparkles className="h-6 w-6 text-white" />
              </div>
              <div>
                <h2 className="font-bold text-lg text-amber-100">Hallo OCB AI</h2>
                <p className="text-xs text-gray-400">AI Perusahaan Terlengkap</p>
              </div>
            </div>
            
            <button 
              onClick={startNewChat}
              className="w-full px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center justify-center gap-2 hover:opacity-90 transition-opacity"
              data-testid="new-chat-btn"
            >
              <Plus className="h-4 w-4" /> Chat Baru
            </button>
          </div>

          {/* Persona Selection */}
          <div className="p-4 border-b border-red-900/30">
            <div className="text-xs text-gray-400 mb-2">Pilih AI Persona</div>
            <div className="grid grid-cols-4 gap-2">
              {personas.map(persona => {
                const Icon = personaIcons[persona.id] || Bot;
                const isActive = selectedPersona === persona.id;
                return (
                  <button
                    key={persona.id}
                    onClick={() => setSelectedPersona(persona.id)}
                    className={`p-2 rounded-lg flex flex-col items-center gap-1 transition-all ${
                      isActive 
                        ? `bg-gradient-to-br ${personaColors[persona.id]} text-white` 
                        : 'bg-red-900/10 text-gray-400 hover:bg-red-900/20'
                    }`}
                    title={persona.description}
                    data-testid={`persona-${persona.id}`}
                  >
                    <Icon className="h-4 w-4" />
                    <span className="text-[10px] truncate w-full text-center">{persona.name.replace(' AI', '')}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Chat Sessions */}
          <div className="flex-1 overflow-y-auto p-4">
            <div className="text-xs text-gray-400 mb-2">Riwayat Chat</div>
            <div className="space-y-2">
              {sessions.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-4">Belum ada riwayat</p>
              ) : (
                sessions.map(session => (
                  <div
                    key={session.session_id}
                    onClick={() => loadSessionHistory(session.session_id)}
                    className={`p-3 rounded-lg cursor-pointer transition-colors group ${
                      session.session_id === sessionId 
                        ? 'bg-red-900/30 border border-red-700/30' 
                        : 'bg-red-900/10 hover:bg-red-900/20'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <MessageSquare className="h-4 w-4 text-gray-400 flex-shrink-0" />
                        <span className="text-sm truncate">{session.last_message}</span>
                      </div>
                      <button 
                        onClick={(e) => deleteSession(session.session_id, e)}
                        className="opacity-0 group-hover:opacity-100 p-1 text-red-400 hover:bg-red-900/30 rounded"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">{session.message_count} pesan</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        {/* Chat Header */}
        <div className="p-4 border-b border-red-900/30 flex items-center gap-3">
          <button 
            onClick={() => setShowSidebar(!showSidebar)}
            className="p-2 hover:bg-red-900/20 rounded-lg lg:hidden"
          >
            <MessageSquare className="h-5 w-5" />
          </button>
          
          <div className={`p-2 bg-gradient-to-br ${personaGradient} rounded-xl`}>
            <PersonaIcon className="h-6 w-6 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-amber-100">{currentPersona.name || 'Hallo OCB AI'}</h3>
            <p className="text-xs text-gray-400">{currentPersona.description || 'AI Perusahaan'}</p>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4" data-testid="chat-messages">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center px-4">
              <div className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${personaGradient} flex items-center justify-center mb-4 shadow-lg`}>
                <PersonaIcon className="h-10 w-10 text-white" />
              </div>
              <h3 className="text-xl font-bold text-amber-100 mb-2">Hallo! Saya {currentPersona.name || 'AI'}</h3>
              <p className="text-gray-400 mb-6 max-w-md">{currentPersona.description || 'Tanyakan apa saja tentang bisnis Anda'}</p>
              
              {/* Suggested Questions */}
              <div className="w-full max-w-lg">
                <p className="text-sm text-gray-500 mb-3">Pertanyaan yang disarankan:</p>
                <div className="space-y-2">
                  {suggestions.slice(0, 4).map((question, idx) => (
                    <button
                      key={idx}
                      onClick={() => sendMessage(question)}
                      className="w-full p-3 text-left bg-red-900/10 hover:bg-red-900/20 rounded-lg text-sm text-gray-300 flex items-center gap-2 transition-colors"
                      data-testid={`suggestion-${idx}`}
                    >
                      <ChevronRight className="h-4 w-4 text-amber-500" />
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  data-testid={`message-${msg.role}-${idx}`}
                >
                  {msg.role === 'assistant' && (
                    <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${personaGradient} flex items-center justify-center flex-shrink-0`}>
                      <PersonaIcon className="h-4 w-4 text-white" />
                    </div>
                  )}
                  
                  <div
                    className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-r from-red-700 to-red-600 text-white'
                        : 'bg-[#0a0608] border border-red-900/30 text-gray-200'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                  </div>
                  
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-lg bg-amber-600 flex items-center justify-center flex-shrink-0">
                      <User className="h-4 w-4 text-white" />
                    </div>
                  )}
                </div>
              ))}
              
              {loading && (
                <div className="flex gap-3">
                  <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${personaGradient} flex items-center justify-center`}>
                    <PersonaIcon className="h-4 w-4 text-white" />
                  </div>
                  <div className="bg-[#0a0608] border border-red-900/30 rounded-2xl px-4 py-3">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 rounded-full bg-amber-400 animate-bounce" />
                      <div className="w-2 h-2 rounded-full bg-amber-400 animate-bounce" style={{ animationDelay: '0.1s' }} />
                      <div className="w-2 h-2 rounded-full bg-amber-400 animate-bounce" style={{ animationDelay: '0.2s' }} />
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-red-900/30 bg-[#0a0608]/50">
          <div className="flex gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={`Tanyakan sesuatu ke ${currentPersona.name || 'Hallo AI'}...`}
              disabled={loading}
              rows={1}
              className="flex-1 px-4 py-3 bg-[#1a1214] border border-red-900/30 rounded-xl text-gray-200 placeholder-gray-500 resize-none focus:outline-none focus:border-red-700/50"
              data-testid="chat-input"
            />
            <button
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              className="px-4 py-3 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-xl disabled:opacity-50 hover:opacity-90 transition-opacity"
              data-testid="send-btn"
            >
              {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2 text-center">
            Hallo AI terhubung dengan data real-time sistem OCB AI TITAN
          </p>
        </div>
      </div>
    </div>
  );
};

export default HalloAI;
