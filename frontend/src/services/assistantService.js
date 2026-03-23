const ROUTE_CONTEXTS = [
  {
    match: (pathname) => pathname === '/' || pathname === '/dashboard',
    module: 'general',
    submodule: 'executive_dashboard',
    pageLabel: 'dashboard ejecutivo',
    clauseHints: ['4', '5', '6', '7', '8', '9', '10'],
    primaryStandards: ['ISO 9001'],
  },
  {
    match: (pathname) => pathname.startsWith('/context'),
    module: 'context',
    submodule: 'context_analysis',
    pageLabel: 'analisis de contexto',
    clauseHints: ['4.1', '4.2'],
    primaryStandards: ['ISO 9001', 'ISO 14001', 'ISO 45001', 'ISO 27001'],
  },
  {
    match: (pathname) => pathname.startsWith('/stakeholders'),
    module: 'stakeholders',
    submodule: 'stakeholder_management',
    pageLabel: 'partes interesadas',
    clauseHints: ['4.2'],
    primaryStandards: ['ISO 9001', 'ISO 14001', 'ISO 45001', 'ISO 27001'],
  },
  {
    match: (pathname) => pathname.startsWith('/scope'),
    module: 'scope',
    submodule: 'scope_definition',
    pageLabel: 'alcance del sistema',
    clauseHints: ['4.3'],
    primaryStandards: ['ISO 9001', 'ISO 14001', 'ISO 45001', 'ISO 27001', 'ISO 42001'],
  },
  {
    match: (pathname) => pathname.startsWith('/processes'),
    module: 'processes',
    submodule: 'process_mapping',
    pageLabel: 'mapeo de procesos',
    clauseHints: ['4.4', '8.1'],
    primaryStandards: ['ISO 9001'],
  },
  {
    match: (pathname) => pathname.startsWith('/leadership/policies'),
    module: 'leadership',
    submodule: 'policies',
    pageLabel: 'politicas',
    clauseHints: ['5.2'],
    primaryStandards: ['ISO 9001', 'ISO 14001', 'ISO 45001', 'ISO 27001', 'ISO 42001'],
  },
  {
    match: (pathname) => pathname.startsWith('/leadership/roles') || pathname.startsWith('/leadership/assignments'),
    module: 'leadership',
    submodule: 'roles_and_responsibilities',
    pageLabel: 'roles y responsabilidades',
    clauseHints: ['5.3'],
    primaryStandards: ['ISO 9001', 'ISO 14001', 'ISO 45001', 'ISO 27001', 'ISO 42001'],
  },
  {
    match: (pathname) => pathname.startsWith('/leadership/commitments') || pathname.startsWith('/leadership/customer-focus'),
    module: 'leadership',
    submodule: 'leadership_commitment',
    pageLabel: 'compromiso de la direccion',
    clauseHints: ['5.1'],
    primaryStandards: ['ISO 9001', 'ISO 14001', 'ISO 45001', 'ISO 27001', 'ISO 42001'],
  },
  {
    match: (pathname) => pathname.startsWith('/leadership/raci'),
    module: 'leadership',
    submodule: 'raci_matrix',
    pageLabel: 'matriz raci',
    clauseHints: ['5.3'],
    primaryStandards: ['ISO 9001', 'ISO 27001'],
  },
  {
    match: (pathname) => pathname.startsWith('/planning'),
    module: 'planning',
    submodule: 'planning_controls',
    pageLabel: 'planificacion',
    clauseHints: ['6.1', '6.2', '6.3'],
    primaryStandards: ['ISO 9001', 'ISO 14001', 'ISO 45001', 'ISO 27001', 'ISO 42001'],
  },
  {
    match: (pathname) => pathname.startsWith('/resources'),
    module: 'resources',
    submodule: 'support_resources',
    pageLabel: 'recursos y soporte',
    clauseHints: ['7.1', '7.2', '7.3', '7.4', '7.5'],
    primaryStandards: ['ISO 9001', 'ISO 14001', 'ISO 45001', 'ISO 27001', 'ISO 42001'],
  },
  {
    match: (pathname) => pathname.startsWith('/operations'),
    module: 'operations',
    submodule: 'operational_control',
    pageLabel: 'operacion',
    clauseHints: ['8.1', '8.2', '8.3', '8.4', '8.5', '8.6', '8.7'],
    primaryStandards: ['ISO 9001', 'ISO 14001', 'ISO 45001', 'ISO 27001'],
  },
  {
    match: (pathname) => pathname.startsWith('/performance'),
    module: 'performance',
    submodule: 'evaluation_and_audits',
    pageLabel: 'evaluacion del desempeno',
    clauseHints: ['9.1', '9.2', '9.3'],
    primaryStandards: ['ISO 9001', 'ISO 14001', 'ISO 45001', 'ISO 27001', 'ISO 42001'],
  },
  {
    match: (pathname) => pathname.startsWith('/improvement'),
    module: 'improvement',
    submodule: 'nonconformities_and_improvement',
    pageLabel: 'mejora',
    clauseHints: ['10.1', '10.2', '10.3'],
    primaryStandards: ['ISO 9001', 'ISO 14001', 'ISO 45001', 'ISO 27001', 'ISO 42001'],
  },
  {
    match: (pathname) => pathname.startsWith('/settings'),
    module: 'settings',
    submodule: 'system_configuration',
    pageLabel: 'configuracion del sistema',
    clauseHints: [],
    primaryStandards: ['ISO 9001'],
  },
];

const getAssistantContextFromPath = (pathname = '/') => {
  const match = ROUTE_CONTEXTS.find((entry) => entry.match(pathname));
  return match || {
    module: 'general',
    submodule: 'general_guidance',
    pageLabel: 'orientacion general',
    clauseHints: [],
    primaryStandards: ['ISO 9001'],
  };
};

const getModuleFromPath = (pathname = '/') => getAssistantContextFromPath(pathname).module;

const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

const fetchAssistantState = async ({ conversationId } = {}) => {
  const params = new URLSearchParams();
  if (conversationId) {
    params.set('conversation_id', String(conversationId));
  }
  const query = params.toString();
  const url = `/api/integration/assistant/state/${query ? `?${query}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(`assistant_state_error_${response.status}`);
  }

  return response.json();
};

const streamAssistantResponse = async ({ question, route, conversation, conversationId, onChunk, onDone, signal }) => {
  const routeContext = getAssistantContextFromPath(route);

  const response = await fetch('/api/integration/assistant/stream/', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      question,
      route,
      module: routeContext.module,
      routeContext,
      conversation,
      conversationId,
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
  fetchAssistantState,
  getModuleFromPath,
  getAssistantContextFromPath,
};
