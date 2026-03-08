import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Send, Bot, User } from 'lucide-react';
import api from '../services/api';
import { toast } from 'sonner';

export default function AIChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [agentMode, setAgentMode] = useState('customer_service');
  const [language, setLanguage] = useState('en');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await api.post('/ai/chat', {
        conversation_id: conversationId,
        message: input,
        agent_mode: agentMode,
        channel: 'webchat',
        language: language
      });

      if (!conversationId) {
        setConversationId(response.data.conversation_id);
      }

      const aiMessage = { role: 'assistant', content: response.data.response };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      toast.error('Failed to send message');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const startNewConversation = () => {
    setMessages([]);
    setConversationId(null);
  };

  return (
    <div className="space-y-6" data-testid="ai-chat-page">
      <div>
        <h1 className="text-4xl font-bold tracking-tight mb-2">AI Chat Assistant</h1>
        <p className="text-muted-foreground">Interact with your intelligent business assistant</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Settings Sidebar */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Chat Settings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Agent Mode</label>
              <Select value={agentMode} onValueChange={setAgentMode}>
                <SelectTrigger data-testid="agent-mode-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="customer_service">Customer Service</SelectItem>
                  <SelectItem value="sales">Sales Agent</SelectItem>
                  <SelectItem value="marketing">Marketing</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Language</label>
              <Select value={language} onValueChange={setLanguage}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="id">Bahasa Indonesia</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button 
              variant="outline" 
              className="w-full" 
              onClick={startNewConversation}
              data-testid="new-conversation-button"
            >
              New Conversation
            </Button>
          </CardContent>
        </Card>

        {/* Chat Interface */}
        <Card className="lg:col-span-3 flex flex-col h-[600px]">
          <CardHeader className="border-b">
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-primary" />
              AI Assistant
              <span className="text-sm font-normal text-muted-foreground ml-2 capitalize">
                ({agentMode.replace('_', ' ')} Mode)
              </span>
            </CardTitle>
          </CardHeader>
          
          <CardContent className="flex-1 overflow-y-auto p-6 space-y-4" data-testid="chat-messages">
            {messages.length === 0 ? (
              <div className="h-full flex items-center justify-center text-center">
                <div>
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center mx-auto mb-4">
                    <Bot className="h-8 w-8 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">Start a Conversation</h3>
                  <p className="text-muted-foreground">
                    Ask me anything about your business, products, or customers
                  </p>
                </div>
              </div>
            ) : (
              messages.map((msg, index) => (
                <div
                  key={index}
                  className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  data-testid={`chat-message-${msg.role}`}
                >
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center flex-shrink-0">
                      <Bot className="h-4 w-4 text-white" />
                    </div>
                  )}
                  
                  <div
                    className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                      msg.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}
                  >
                    <p className="text-sm leading-relaxed">{msg.content}</p>
                  </div>
                  
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center flex-shrink-0">
                      <User className="h-4 w-4 text-white" />
                    </div>
                  )}
                </div>
              ))
            )}
            {loading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-white" />
                </div>
                <div className="bg-muted rounded-2xl px-4 py-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 rounded-full bg-primary animate-bounce" />
                    <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </CardContent>

          <div className="border-t p-4">
            <form onSubmit={sendMessage} className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message..."
                disabled={loading}
                className="flex-1"
                data-testid="chat-input"
              />
              <Button type="submit" disabled={loading || !input.trim()} data-testid="send-message-button">
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </div>
        </Card>
      </div>
    </div>
  );
}