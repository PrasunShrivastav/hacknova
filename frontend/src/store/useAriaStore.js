import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// In production (Vercel), VITE_API_URL points to the Render backend
// In local dev, falls back to '/api' (proxied by Vite to localhost:8000)
const API_BASE = import.meta.env.VITE_API_URL || '/api';

// Local storage utilities
const STORAGE_KEY = 'aria-session-history';

const saveSessionToHistory = (sessionData) => {
  try {
    const existingHistory = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    const newSession = {
      id: sessionData.sessionId,
      question: sessionData.question,
      timestamp: new Date().toISOString(),
      papers: sessionData.papers,
      summary: sessionData.summary,
      contradictions: sessionData.contradictions,
      gaps: sessionData.gaps,
      roadmap: sessionData.roadmap,
      status: sessionData.status,
      progress: sessionData.progress
    };
    
    // Remove any existing session with same ID
    const filteredHistory = existingHistory.filter(s => s.id !== sessionData.sessionId);
    // Add new session at the beginning
    const updatedHistory = [newSession, ...filteredHistory].slice(0, 50); // Keep last 50 sessions
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedHistory));
  } catch (error) {
    console.error('Failed to save session to history:', error);
  }
};

const getSessionHistory = () => {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
  } catch (error) {
    console.error('Failed to load session history:', error);
    return [];
  }
};

const deleteSessionFromHistory = (sessionId) => {
  try {
    const existingHistory = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    const updatedHistory = existingHistory.filter(s => s.id !== sessionId);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedHistory));
  } catch (error) {
    console.error('Failed to delete session from history:', error);
  }
};

const clearSessionHistory = () => {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error('Failed to clear session history:', error);
  }
};

const useAriaStore = create((set, get) => ({
  // === State ===
  sessionId: null,
  status: 'idle', // idle | searching | running | completed | error
  statusEvents: [],
  progress: 0,
  question: '',

  // Results
  papers: [],
  summary: '',
  contradictions: '',
  gaps: null,
  graphData: null,
  roadmap: null,

  // Chat
  chatMessages: [],
  chatLoading: false,

  // Active tab
  activeTab: 'summary', // summary | contradictions | gaps | graph | papers

  // Session History
  sessionHistory: [],
  showHistory: false,

  // Error
  error: null,

  // === Actions ===

  setActiveTab: (tab) => set({ activeTab: tab }),

  startResearch: async (question, maxPapers = 30, depth = 2) => {
    set({
      question,
      status: 'searching',
      statusEvents: [],
      progress: 0,
      papers: [],
      summary: '',
      contradictions: '',
      gaps: null,
      graphData: null,
      roadmap: null,
      chatMessages: [],
      error: null,
    });

    try {
      const res = await fetch(`${API_BASE}/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, max_papers: maxPapers, depth }),
      });

      if (!res.ok) throw new Error(`Research request failed: ${res.statusText}`);

      const data = await res.json();
      const sessionId = data.session_id;

      set({ sessionId, status: 'running' });

      // Connect to SSE for status updates
      get().connectSSE(sessionId);
    } catch (err) {
      set({ status: 'error', error: err.message });
    }
  },

  connectSSE: (sessionId) => {
    const eventSource = new EventSource(`${API_BASE}/status/${sessionId}`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.event === 'done') {
          eventSource.close();
          get().fetchResults(sessionId);
          return;
        }

        if (data.event === 'error') {
          eventSource.close();
          set({ status: 'error', error: data.detail });
          return;
        }

        if (data.event === 'keepalive') return;

        set((state) => ({
          statusEvents: [...state.statusEvents, data],
          progress: data.progress >= 0 ? data.progress : state.progress,
        }));
      } catch (e) {
        console.error('SSE parse error:', e);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      // Don't mark as error if we already completed
      const currentStatus = get().status;
      if (currentStatus === 'running') {
        // Try fetching results in case stream died but pipeline completed
        get().fetchResults(sessionId);
      }
    };
  },

  fetchResults: async (sessionId) => {
    try {
      const res = await fetch(`${API_BASE}/results/${sessionId}`);
      if (!res.ok) throw new Error('Failed to fetch results');

      const data = await res.json();

      if (data.status === 'running') {
        // Pipeline still running, retry in 3s
        setTimeout(() => get().fetchResults(sessionId), 3000);
        return;
      }

      // Parse gaps — backend returns JSON string, frontend needs object
      let parsedGaps = data.gaps || null;
      if (typeof parsedGaps === 'string') {
        try { parsedGaps = JSON.parse(parsedGaps); } catch (e) { parsedGaps = null; }
      }

      set({
        status: 'completed',
        summary: data.summary || '',
        contradictions: data.contradictions || '',
        gaps: parsedGaps,
        papers: data.papers || [],
        roadmap: data.roadmap || null,
      });

      // Save session to history
      const currentState = get();
      saveSessionToHistory({
        sessionId: currentState.sessionId,
        question: currentState.question,
        papers: data.papers || [],
        summary: data.summary || '',
        contradictions: data.contradictions || '',
        gaps: parsedGaps,
        roadmap: data.roadmap || null,
        status: 'completed',
        progress: 100
      });
      
      // Update history in state
      get().loadSessionHistory();

      // Fetch graph data
      get().fetchGraph(sessionId);
    } catch (err) {
      set({ status: 'error', error: err.message });
    }
  },

  fetchGraph: async (sessionId) => {
    try {
      const res = await fetch(`${API_BASE}/graph/${sessionId}`);
      if (!res.ok) return;
      const data = await res.json();
      set({ graphData: data });
    } catch (err) {
      console.error('Failed to fetch graph:', err);
    }
  },

  sendChatMessage: async (question) => {
    const { sessionId, chatMessages } = get();
    if (!sessionId) return;

    const userMsg = { role: 'user', content: question };
    set({
      chatMessages: [...chatMessages, userMsg],
      chatLoading: true,
    });

    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, question }),
      });

      if (!res.ok) throw new Error('Query failed');

      const data = await res.json();
      const assistantMsg = { role: 'assistant', content: data.answer };

      set((state) => ({
        chatMessages: [...state.chatMessages, assistantMsg],
        chatLoading: false,
      }));
    } catch (err) {
      const errorMsg = { role: 'assistant', content: `Error: ${err.message}` };
      set((state) => ({
        chatMessages: [...state.chatMessages, errorMsg],
        chatLoading: false,
      }));
    }
  },

  // Session History Actions
  loadSessionHistory: () => {
    const history = getSessionHistory();
    set({ sessionHistory: history });
  },

  toggleHistory: () => {
    set((state) => ({ showHistory: !state.showHistory }));
  },

  restoreSession: (sessionData) => {
    set({
      sessionId: sessionData.id,
      question: sessionData.question,
      papers: sessionData.papers,
      summary: sessionData.summary,
      contradictions: sessionData.contradictions,
      gaps: sessionData.gaps,
      roadmap: sessionData.roadmap,
      status: sessionData.status || 'completed',
      progress: sessionData.progress || 100,
      chatMessages: [],
      error: null,
      showHistory: false
    });
  },

  deleteSession: (sessionId) => {
    deleteSessionFromHistory(sessionId);
    get().loadSessionHistory();
  },

  clearHistory: () => {
    clearSessionHistory();
    set({ sessionHistory: [] });
  },

  reset: () => set({
    sessionId: null,
    status: 'idle',
    statusEvents: [],
    progress: 0,
    question: '',
    papers: [],
    summary: '',
    contradictions: '',
    gaps: null,
    graphData: null,
    roadmap: null,
    chatMessages: [],
    chatLoading: false,
    activeTab: 'summary',
    error: null,
    showHistory: false
  }),
}));

export default useAriaStore;
