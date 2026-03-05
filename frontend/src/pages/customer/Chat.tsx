import { useEffect, useRef, useState } from 'react';
import { Send, Sparkles, User, Bot } from 'lucide-react';
import { useChatStore } from '../../stores/chatStore';
import PageHeader from '../../components/PageHeader';
import Spinner from '../../components/Spinner';

export default function Chat() {
  const {
    messages,
    suggestions,
    loading,
    error,
    fetchSuggestions,
    sendMessage,
  } = useChatStore();
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (text?: string) => {
    const msg = text ?? input.trim();
    if (!msg || loading) return;
    setInput('');
    sendMessage(msg);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 130px)' }}>
      <PageHeader
        title="Data Assistant"
        subtitle="Ask questions about the CDM, schema mappings, and uploaded data"
      />

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto card p-4 mb-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="mb-4 rounded-xl bg-brand-blue/5 p-4">
              <Sparkles size={28} className="text-brand-blue" />
            </div>
            <h3 className="text-base font-semibold text-gray-800">
              Periscope Data Assistant
            </h3>
            <p className="mt-1 text-sm text-gray-500 max-w-md">
              I can help you understand the Common Data Model, review schema mappings, and answer
              questions about uploaded customer data.
            </p>

            {suggestions.length > 0 && (
              <div className="mt-6 flex flex-wrap justify-center gap-2 max-w-lg">
                {suggestions.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(s)}
                    className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-medium text-gray-700 shadow-sm hover:bg-gray-50 hover:border-brand-blue/30 transition-all text-left"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {msg.role === 'assistant' && (
              <div className="flex-shrink-0 w-7 h-7 rounded-lg bg-brand-blue/10 flex items-center justify-center">
                <Bot size={14} className="text-brand-blue" />
              </div>
            )}
            <div
              className={`max-w-[70%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-brand-blue text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>
              <div
                className={`mt-1.5 text-[10px] ${
                  msg.role === 'user' ? 'text-white/50' : 'text-gray-400'
                }`}
              >
                {msg.timestamp.toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </div>
            </div>
            {msg.role === 'user' && (
              <div className="flex-shrink-0 w-7 h-7 rounded-lg bg-brand-navy flex items-center justify-center">
                <User size={14} className="text-white" />
              </div>
            )}
          </div>
        ))}

        {loading && <Spinner text="Thinking..." />}
        {error && (
          <div className="text-sm text-error bg-red-50 rounded-lg px-4 py-2">
            {error}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="card p-3 flex gap-3">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about schema mappings, CDM fields, or upload data..."
          rows={1}
          className="input-field resize-none flex-1"
        />
        <button
          onClick={() => handleSend()}
          disabled={!input.trim() || loading}
          className="btn-primary px-4"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
