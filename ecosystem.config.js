module.exports = {
  apps: [
    {
      name: 'clothing-bot',
      script: 'main.py',
      interpreter: 'python3',
      watch: false,
      autorestart: true,
      restart_delay: 3000,
      max_restarts: 10,
      env: {
        PYTHONUNBUFFERED: '1',
      },
    },
  ],
};
