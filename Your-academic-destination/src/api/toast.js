/**
 * toast.js — نظام رسائل منبثقة (toast) بسيط، بدون الحاجة لـ React Context.
 *
 * الفكرة: أي component بأي مكان بالمشروع فيه يستدعي showToast(message)
 * وهي بتظهر تلقائياً كرسالة منبثقة فوق الشاشة لثواني معدودة وبعدين تختفي
 * لحالها — بدل ما تتراكم كنص ثابت بالصفحة.
 *
 * الاستخدام:
 *   import { showToast } from '../../api/toast';
 *   showToast('الرسالة هون', 'error'); // أو 'success'
 *
 * لازم <ToastContainer /> تكون موجودة مرة وحدة بس بـ App.jsx (خارج <Routes>)
 * حتى الرسائل تظهر فوق أي صفحة بالمشروع.
 */

let listeners = [];
let idCounter = 0;

export function showToast(message, type = 'error', duration = 4000) {
  const id = idCounter++;
  const toast = { id, message, type };

  listeners.forEach((fn) => fn((prev) => [...prev, toast]));

  setTimeout(() => {
    listeners.forEach((fn) => fn((prev) => prev.filter((t) => t.id !== id)));
  }, duration);
}

export function subscribeToasts(fn) {
  listeners.push(fn);
  return () => {
    listeners = listeners.filter((l) => l !== fn);
  };
}