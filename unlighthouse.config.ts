export default {
  puppeteerOptions: {
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
    ],
  },
  lighthouse: {
    throttlingMethod: 'simulate',
  },
  scanner: {
    concurrency: 2,
    // exclude: ['/admin/', '/api/'],
  },
}


//para ejecutar el servidor desde el terminal npx unlighthouse --site http://isosmart.local/
