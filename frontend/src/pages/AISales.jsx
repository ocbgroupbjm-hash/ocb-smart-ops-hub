import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  Send, Bot, User, ShoppingCart, Plus, Trash2, 
  CreditCard, Package, Loader2, MessageSquare, RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';

const AISales = () => {
  const { api } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [cart, setCart] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewChat, setShowNewChat] = useState(false);
  const [newCustomer, setNewCustomer] = useState({ name: '', phone: '' });
  const messagesEndRef = useRef(null);

  const loadConversations = async () => {
    try {
      const res = await api('/api/ai-sales/conversations?limit=20');
      if (res.ok) {
        const data = await res.json();
        setConversations(data.conversations || []);
      }
    } catch (err) {
      console.error('Failed to load conversations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const startNewConversation = async () => {
    if (!newCustomer.name) {
      toast.error('Nama pelanggan wajib diisi');
      return;
    }

    try {
      const res = await api('/api/ai-sales/conversation/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_name: newCustomer.name,
          customer_phone: newCustomer.phone,
          channel: 'internal_chat'
        })
      });

      if (res.ok) {
        const data = await res.json();
        setActiveConversation(data.conversation_id);
        setMessages(data.messages || []);
        setCart([]);
        setShowNewChat(false);
        setNewCustomer({ name: '', phone: '' });
        loadConversations();
        toast.success('Percakapan baru dimulai');
      }
    } catch (err) {
      toast.error('Gagal memulai percakapan');
    }
  };

  const selectConversation = async (convId) => {
    try {
      const res = await api(`/api/ai-sales/conversation/${convId}`);
      if (res.ok) {
        const data = await res.json();
        setActiveConversation(convId);
        setMessages(data.messages || []);
        setCart(data.cart_items || []);
      }
    } catch (err) {
      toast.error('Gagal memuat percakapan');
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || !activeConversation || sending) return;

    const message = inputMessage.trim();
    setInputMessage('');
    setSending(true);

    // Optimistic update
    setMessages(prev => [...prev, {
      id: Date.now(),
      role: 'customer',
      content: message,
      timestamp: new Date().toISOString()
    }]);

    try {
      const res = await api(`/api/ai-sales/conversation/${activeConversation}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: message })
      });

      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev.slice(0, -1), data.customer_message, data.ai_response]);
        setCart(data.cart_items || []);
      }
    } catch (err) {
      toast.error('Gagal mengirim pesan');
    } finally {
      setSending(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0
    }).format(value || 0);
  };

  const totalCart = cart.reduce((sum, item) => sum + (item.subtotal || 0), 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0a0608]">
        <Loader2 className="h-8 w-8 text-amber-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-[#0a0608]">
      {/* Sidebar - Conversations List */}
      <div className="w-80 border-r border-red-900/30 flex flex-col">
        <div className="p-4 border-b border-red-900/30">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-amber-100 flex items-center gap-2">
              <Bot className="h-5 w-5" />
              AI Sales
            </h2>
            <button
              onClick={() => setShowNewChat(true)}
              className="p-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700"
              title="Chat Baru"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>

          {showNewChat && (
            <div className="bg-[#1a1214] rounded-lg p-3 space-y-2">
              <input
                type="text"
                placeholder="Nama Pelanggan"
                value={newCustomer.name}
                onChange={(e) => setNewCustomer({ ...newCustomer, name: e.target.value })}
                className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-sm"
              />
              <input
                type="text"
                placeholder="No. HP (opsional)"
                value={newCustomer.phone}
                onChange={(e) => setNewCustomer({ ...newCustomer, phone: e.target.value })}
                className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-sm"
              />
              <div className="flex gap-2">
                <button
                  onClick={startNewConversation}
                  className="flex-1 px-3 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700"
                >
                  Mulai
                </button>
                <button
                  onClick={() => setShowNewChat(false)}
                  className="px-3 py-2 bg-gray-600 text-white rounded-lg text-sm hover:bg-gray-700"
                >
                  Batal
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => selectConversation(conv.id)}
              className={`p-4 border-b border-red-900/20 cursor-pointer hover:bg-red-900/10 ${
                activeConversation === conv.id ? 'bg-red-900/20' : ''
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-amber-100">
                  {conv.customer_name || 'Customer'}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  conv.status === 'active' ? 'bg-green-600/20 text-green-400' :
                  conv.status === 'waiting_payment' ? 'bg-amber-600/20 text-amber-400' :
                  'bg-gray-600/20 text-gray-400'
                }`}>
                  {conv.status}
                </span>
              </div>
              <p className="text-sm text-gray-400 truncate">
                {conv.messages?.[conv.messages.length - 1]?.content?.substring(0, 50) || 'No messages'}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {conv.channel} • {new Date(conv.last_message_at).toLocaleString('id-ID')}
              </p>
            </div>
          ))}

          {conversations.length === 0 && (
            <div className="p-4 text-center text-gray-400">
              <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>Belum ada percakapan</p>
              <p className="text-sm">Klik + untuk memulai</p>
            </div>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {activeConversation ? (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg, idx) => (
                <div
                  key={msg.id || idx}
                  className={`flex ${msg.role === 'customer' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[70%] rounded-lg p-3 ${
                    msg.role === 'customer' 
                      ? 'bg-amber-600 text-white' 
                      : 'bg-[#1a1214] border border-red-900/30 text-white'
                  }`}>
                    <div className="flex items-center gap-2 mb-1">
                      {msg.role === 'ai' && <Bot className="h-4 w-4 text-amber-500" />}
                      {msg.role === 'customer' && <User className="h-4 w-4" />}
                      <span className="text-xs opacity-70">
                        {msg.role === 'ai' ? 'AI Sales' : 'Customer'}
                      </span>
                    </div>
                    <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
                    <p className="text-xs opacity-50 mt-1">
                      {new Date(msg.timestamp).toLocaleTimeString('id-ID')}
                    </p>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Cart Summary */}
            {cart.length > 0 && (
              <div className="border-t border-red-900/30 bg-[#1a1214] p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-amber-100 flex items-center gap-2">
                    <ShoppingCart className="h-4 w-4" />
                    Keranjang ({cart.length})
                  </span>
                  <span className="text-lg font-bold text-green-400">
                    {formatCurrency(totalCart)}
                  </span>
                </div>
                <div className="space-y-1">
                  {cart.map((item, idx) => (
                    <div key={idx} className="flex justify-between text-sm text-gray-400">
                      <span>{item.product_name} x {item.qty}</span>
                      <span>{formatCurrency(item.subtotal)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Input */}
            <form onSubmit={sendMessage} className="p-4 border-t border-red-900/30">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Ketik pesan... (coba: KATALOG, BELI, CHECKOUT)"
                  className="flex-1 px-4 py-3 bg-[#1a1214] border border-red-900/30 rounded-lg focus:outline-none focus:border-amber-600"
                  disabled={sending}
                />
                <button
                  type="submit"
                  disabled={sending || !inputMessage.trim()}
                  className="px-4 py-3 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {sending ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
                </button>
              </div>
              <div className="flex gap-2 mt-2">
                {['KATALOG', 'PROMO', 'KERANJANG', 'CHECKOUT'].map((cmd) => (
                  <button
                    key={cmd}
                    type="button"
                    onClick={() => setInputMessage(cmd)}
                    className="px-3 py-1 bg-[#1a1214] border border-red-900/30 rounded-full text-xs text-gray-400 hover:border-amber-600 hover:text-amber-400"
                  >
                    {cmd}
                  </button>
                ))}
              </div>
            </form>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center text-gray-400">
              <Bot className="h-16 w-16 mx-auto mb-4 opacity-30" />
              <p className="text-lg">AI Sales Assistant</p>
              <p className="text-sm">Pilih percakapan atau mulai yang baru</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AISales;
