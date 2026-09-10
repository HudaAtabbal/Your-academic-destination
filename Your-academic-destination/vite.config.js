export default {
  server: {
    host: true,
    allowedHosts: ['.ngrok-free.app', '.ngrok-free.dev'],
    hmr: {
      protocol: 'wss',
      host: 'maturing-platter-sloping.ngrok-free.dev', // لازم تبدّليها كل مرة يتغيّر رابط ngrok
      clientPort: 443,
    },
  },
}