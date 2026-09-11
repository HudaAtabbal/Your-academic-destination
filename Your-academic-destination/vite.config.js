export default {
  server: {
    host: true,
    allowedHosts: true, // يسمح بأي host (مفيد للتطوير عبر ngrok/tunnel)
    // ملاحظة: الـ HMR عبر ngrok كان مثبّت هنا بوصلة ثابتة — انحذف عمداً لأن الرابط
    // بينغيّر كل مرة. للتطوير عبر ngrok، شغّلي الـ dev server على http://localhost:5173
    // وخليني ngrok tunnel يشاور عليه — Vite بيكتشف الـ host تلقائياً من الطلب.
  },
}