module.exports = {
  apps: [{
    name: 'isosmart-frontend',
    script: 'npm',
    args: 'run dev',
    cwd: '/home/felipe/proyectos/isosmart/frontend',
    env: {
      NODE_ENV: 'development',
      PORT: 3001,
      VITE_API_URL: 'http://192.168.100.100/api'
    },
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    error_file: '/home/felipe/proyectos/isosmart/logs/ai/frontend-error.log',
    out_file: '/home/felipe/proyectos/isosmart/logs/ai/frontend-out.log',
    time: true,
  }]
}
