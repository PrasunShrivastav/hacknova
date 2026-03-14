import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import useAriaStore from '../store/useAriaStore';

export default function ChatInterface() {
  const [input, setInput] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const chatMessages = useAriaStore((s) => s.chatMessages);
  const chatLoading = useAriaStore((s) => s.chatLoading);
  const sendChatMessage = useAriaStore((s) => s.sendChatMessage);
  const status = useAriaStore((s) => s.status);
  const messagesEndRef = useRef(null);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim() || chatLoading) return;
    sendChatMessage(input.trim());
    setInput('');
  };

  // Only show after research is complete
  if (status !== 'completed') return null;

  return (
    <>
      {/* Toggle button */}
      {!isOpen && (
        <button
          id="chat-toggle"
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 left-4  z-50 btn-glow w-14 h-14 rounded-full flex items-center justify-center text-xl shadow-lg shadow-aria-accent/20"
        >
          💬
        </button>
      )}

      {/* Chat panel */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 w-96 h-[500px] glass-card flex flex-col shadow-2xl shadow-aria-accent/10 animate-slide-up"
          style={{ border: '1px solid rgba(0, 212, 255, 0.15)' }}>
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-aria-border">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-aria-green animate-pulse" />
              <span className="text-sm font-semibold text-aria-text">Ask ARIA</span>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-aria-text-muted hover:text-aria-text transition-colors text-sm"
            >
              ✕
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
            {chatMessages.length === 0 && (
              <div className="text-center py-8">
                <span className="text-3xl block mb-2">🤖</span>
                <p className="text-xs text-aria-text-dim">
                  Ask follow-up questions about the research papers.
                </p>
                <div className="mt-3 space-y-1">
                  {[
                    'What are the key findings?',
                    'Which paper is most cited?',
                    'Summarize the methodology used',
                  ].map((q, i) => (
                    <button
                      key={i}
                      onClick={() => { sendChatMessage(q); }}
                      className="block w-full text-left text-[11px] px-3 py-1.5 rounded border border-aria-border text-aria-text-dim
                                 hover:border-aria-accent/30 hover:text-aria-accent transition-all"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {chatMessages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-lg px-3 py-2 text-xs ${msg.role === 'user'
                    ? 'bg-aria-accent/15 text-aria-text border border-aria-accent/20'
                    : 'bg-aria-surface text-aria-text-dim border border-aria-border'
                    }`}
                >
                  {msg.role === 'assistant' ? (
                    <div className="markdown-content text-xs">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            ))}

            {chatLoading && (
              <div className="flex justify-start">
                <div className="bg-aria-surface border border-aria-border rounded-lg px-3 py-2 text-xs text-aria-text-dim">
                  <span className="flex items-center gap-1">
                    <span className="animate-pulse">●</span>
                    <span className="animate-pulse" style={{ animationDelay: '0.2s' }}>●</span>
                    <span className="animate-pulse" style={{ animationDelay: '0.4s' }}>●</span>
                  </span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form onSubmit={handleSend} className="border-t border-aria-border p-3 flex gap-2">
            <input
              id="chat-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a follow-up question..."
              className="flex-1 bg-aria-bg border border-aria-border rounded-lg px-3 py-2 text-xs text-aria-text placeholder-aria-text-muted outline-none focus:border-aria-accent/50"
              disabled={chatLoading}
            />
            <button
              id="chat-send"
              type="submit"
              disabled={!input.trim() || chatLoading}
              className="btn-glow px-3 py-2 text-xs rounded-lg disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </form>
        </div>
      )}
    </>
  );
}
