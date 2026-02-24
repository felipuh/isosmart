const getModuleFromPath = (pathname = '/') => {
  if (pathname.startsWith('/planning')) return 'planning';
  if (pathname.startsWith('/operations')) return 'operations';
  if (pathname.startsWith('/performance')) return 'performance';
  if (pathname.startsWith('/improvement')) return 'improvement';
  if (pathname.startsWith('/resources')) return 'resources';
  if (pathname.startsWith('/leadership')) return 'leadership';
  if (pathname.startsWith('/settings')) return 'settings';
  if (pathname.startsWith('/context')) return 'context';
  if (pathname.startsWith('/stakeholders')) return 'stakeholders';
  if (pathname.startsWith('/scope')) return 'scope';
  if (pathname.startsWith('/processes')) return 'processes';
  return 'general';
};

const streamAssistantResponse = async ({ question, route, conversation, onChunk, onDone, signal }) => {
  const token = localStorage.getItem('access_token');

  const response = await fetch('/api/integration/assistant/stream/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      question,
      route,
      module: getModuleFromPath(route),
      conversation,
    }),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`assistant_stream_error_${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split('\n\n');
    buffer = events.pop() || '';

    for (const rawEvent of events) {
      const lines = rawEvent.split('\n');
      const eventLine = lines.find((line) => line.startsWith('event:'));
      const dataLine = lines.find((line) => line.startsWith('data:'));
      if (!dataLine) continue;

      const eventName = eventLine ? eventLine.replace('event:', '').trim() : 'message';
      const payloadRaw = dataLine.replace('data:', '').trim();

      let payload;
      try {
        payload = JSON.parse(payloadRaw);
      } catch {
        continue;
      }

      if (eventName === 'chunk' && payload.text) {
        onChunk?.(payload.text);
      }
      if (eventName === 'done') {
        onDone?.(payload);
      }
    }
  }
};

export default {
  streamAssistantResponse,
  getModuleFromPath,
};
