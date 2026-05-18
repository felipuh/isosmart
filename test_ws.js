const WebSocket = require('ws');

async function testWs(url, subprotocol) {
  return new Promise((resolve) => {
    console.log(`Testing: ${url} ${subprotocol ? `with subprotocol ${subprotocol}` : '(no subprotocol)'}`);
    const options = subprotocol ? [subprotocol] : undefined;
    const ws = new WebSocket(url, options);

    ws.on('open', () => {
      console.log('RESULT: OPEN');
      ws.close();
      resolve(0);
    });

    ws.on('error', (err) => {
      console.log(`RESULT: ERROR - ${err.message}`);
      resolve(1);
    });
  });
}

async function runTests() {
  const tests = [
    { url: 'ws://127.0.0.1:5173/?token=test', subprotocol: undefined },
    { url: 'ws://127.0.0.1:5173/?token=test', subprotocol: 'vite-hmr' },
    { url: 'ws://isosmart.smart3ai.local/?token=test', subprotocol: 'vite-hmr' }
  ];

  let exitCode = 0;
  for (const test of tests) {
    const result = await testWs(test.url, test.subprotocol);
    if (result !== 0) exitCode = 1;
    console.log('---');
  }
  process.exit(exitCode);
}

runTests();
