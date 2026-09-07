/**
 * registrationStorage.js — "السلة" المشتركة لتجميع بيانات التسجيل
 * عبر خطوات RegisterStep1 → RegisterStep2 → RegisterStep3.
 *
 * ليش sessionStorage مش useState عادي؟
 * لأنو كل صفحة (Step1, Step2, Step3) هي component منفصل تماماً، وبينهن
 * تنقّل فعلي (navigate) — يعني أي useState محلي بينمسح لما تتغير الصفحة.
 * sessionStorage بيضل موجود طول ما التاب مفتوح، وبيتصفّر لحاله لما يسكّر
 * (بعكس localStorage يلي مستخدم لـ unique_code، هدفه يدوم لفترة أطول).
 *
 * الاستخدام:
 *   import { updateRegistrationData, getRegistrationData, clearRegistrationData } from '.../registrationStorage';
 *   updateRegistrationData({ fullName: '...' }); // بكل خطوة، بس عند النجاح
 *   const data = getRegistrationData(); // بآخر خطوة، لتجميع كل شي قبل الإرسال
 *   clearRegistrationData(); // بعد نجاح الإرسال للباك، حتى ما تضل بيانات قديمة لو رجع الطالب يسجّل من جديد
 */

const STORAGE_KEY = 'registrationData';

export function getRegistrationData() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

export function updateRegistrationData(fields) {
  const current = getRegistrationData();
  const updated = { ...current, ...fields };
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  return updated;
}

export function clearRegistrationData() {
  sessionStorage.removeItem(STORAGE_KEY);
}