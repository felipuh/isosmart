import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Bot, MessageCircle, X, Send } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import assistantService from '../../services/assistantService';
import { useI18n } from '../../context/I18nContext';

const ASSISTANT_CONVERSATION_STORAGE_KEY = 'assistant_conversation_id';

const VirtualAssistantPanel = () => {
  const { t } = useI18n();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [conversationId, setConversationId] = useState(() => {
    const persisted = localStorage.getItem(ASSISTANT_CONVERSATION_STORAGE_KEY);
    return persisted ? Number(persisted) : null;
  });
  const [hydrated, setHydrated] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: t('assistantPanel.initialMessage'),
    },
  ]);

  const suggestions = useMemo(
    () => [
      t('assistantPanel.suggestions.audits'),
      t('assistantPanel.suggestions.iso27001'),
      t('assistantPanel.suggestions.risks'),
    ],
    [t]
  );

  useEffect(() => {
    if (conversationId) {
      localStorage.setItem(ASSISTANT_CONVERSATION_STORAGE_KEY, String(conversationId));
      return;
    }
    localStorage.removeItem(ASSISTANT_CONVERSATION_STORAGE_KEY);
  }, [conversationId]);

  useEffect(() => {
    if (!open || hydrated) return;

    let cancelled = false;
    assistantService
      .fetchAssistantState({ conversationId })
      .then((payload) => {
        if (cancelled) return;
        if (payload?.conversation_id) {
          setConversationId(payload.conversation_id);
        }
        if (Array.isArray(payload?.messages) && payload.messages.length) {
          setMessages(payload.messages);
        }
      })
      .catch(() => {
        // Keep the current UI history when backend hydration is unavailable.
      })
      .finally(() => {
        if (!cancelled) setHydrated(true);
      });

    return () => {
      cancelled = true;
    };
  }, [open, hydrated, conversationId]);

  const sendQuestion = (questionText) => {
    const question = questionText.trim();
    if (!question || sending) return;

    const nextMessages = [...messages, { role: 'user', content: question }, { role: 'assistant', content: '' }];
    setMessages(nextMessages);
    setInput('');
    setSending(true);

    const assistantIndex = nextMessages.length - 1;
    const appendChunk = (chunk) => {
      setMessages((prev) => {
        const updated = [...prev];
        const current = updated[assistantIndex] || { role: 'assistant', content: '' };
        updated[assistantIndex] = { ...current, content: `${current.content || ''}${chunk}` };
        return updated;
      });
    };

    const finish = (payload) => {
      if (payload?.conversation_id) {
        setConversationId(payload.conversation_id);
      }
      if (payload?.degraded || payload?.provider === 'unavailable') {
        setMessages((prev) => {
          const updated = [...prev];
          const current = updated[assistantIndex] || {};
          updated[assistantIndex] = {
            role: 'assistant',
            content: current.content || t('assistantPanel.unavailable'),
            status: 'degraded',
          };
          return updated;
        });
      }
      setSending(false);
    };

    assistantService
      .streamAssistantResponse({
        question,
        route: location.pathname,
        conversation: messages,
        conversationId,
        onChunk: appendChunk,
        onDone: finish,
      })
      .catch(() => {
        setMessages((prev) => {
          const updated = [...prev];
          updated[assistantIndex] = {
            role: 'assistant',
            content: t('assistantPanel.unavailable'),
            status: 'degraded',
          };
          return updated;
        });
      })
      .finally(() => setSending(false));
  };

  return (
    <>
      <button
        onClick={() => setOpen((prev) => !prev)}
        className="fixed bottom-6 right-6 z-50 h-12 w-12 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg flex items-center justify-center"
        aria-label={t('assistantPanel.openAriaLabel')}
      >
        {open ? <X className="w-5 h-5" /> : <MessageCircle className="w-5 h-5" />}
      </button>

      {open && (
        <div className="fixed bottom-20 right-6 z-50 w-[360px] max-w-[calc(100vw-2rem)] bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-2xl overflow-hidden">
          <div className="px-4 py-3 bg-indigo-600 text-white flex items-center gap-2">
            <Bot className="w-4 h-4" />
            <p className="font-medium text-sm">{t('assistantPanel.title')}</p>
          </div>

          <div className="p-4 h-72 overflow-y-auto space-y-3 bg-slate-50 dark:bg-slate-900">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`max-w-[90%] px-3 py-2 rounded-lg text-sm ${
                  message.role === 'assistant'
                    ? 'bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100'
                    : 'ml-auto bg-indigo-600 text-white'
                }`}
              >
                {message.status === 'degraded' && (
                  <span className="mb-1 flex items-center gap-1 text-xs font-semibold text-amber-600 dark:text-amber-300">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    {t('assistantPanel.degradedLabel')}
                  </span>
                )}
                {message.content}
              </div>
            ))}
          </div>

          <div className="px-4 pt-3 pb-2 border-t border-slate-200 dark:border-slate-700">
            <div className="flex flex-wrap gap-2 mb-3">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => sendQuestion(suggestion)}
                  className="px-2 py-1 text-xs rounded-md bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-200"
                >
                  {suggestion}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <input
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') sendQuestion(input);
                }}
                placeholder={t('assistantPanel.inputPlaceholder')}
                disabled={sending}
                className="flex-1 px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm text-slate-800 dark:text-slate-100"
              />
              <button
                onClick={() => sendQuestion(input)}
                disabled={sending}
                className="h-9 w-9 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white flex items-center justify-center"
                aria-label={t('assistantPanel.sendAriaLabel')}
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default VirtualAssistantPanel;
