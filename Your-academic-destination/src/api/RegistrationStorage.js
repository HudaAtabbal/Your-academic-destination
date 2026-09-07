/**
 * RegistrationStorage.js — "السلة" المشتركة لتجميع بيانات التسجيل
 * عبر خطوات RegisterStep1 → RegisterStep2 → RegisterStep3.
 *
 * ليش localStorage مش useState عادي؟
 * لأنو كل صفحة (Step1, Step2, Step3) هي component منفصل تماماً، وبينهن
 * تنقّل فعلي (navigate) — يعني أي useState محلي بينمسح لما تتغير الصفحة.
 * localStorage بيضل موجود حتى لو الطالب سكّر المتصفح كامل وفتحه من جديد
 * (بعكس sessionStorage يلي كان مستخدم قبل، وبيتصفّر لحاله لما يسكّر التاب فقط) —
 * هيك لو الطالب عمل ريفريش أو سكّر المتصفح بالغلط بنص التسجيل، بيرجع يلاقي كل شي زي ما تركه.
 *
 * الاستخدام:
 *   import { updateRegistrationData, getRegistrationData, clearRegistrationData } from '.../RegistrationStorage';
 *   updateRegistrationData({ fullName: '...' }); // بكل تغيير بالفورم (مش بس عند الضغط على "تابع")
 *   const data = getRegistrationData(); // لتحميل البيانات المحفوظة عند فتح/إعادة فتح أي خطوة
 *   clearRegistrationData(); // بعد نجاح الإرسال الفعلي للباك، حتى ما تضل بيانات قديمة لو رجع الطالب يسجّل من جديد
 */

const STORAGE_KEY = 'registrationData';

export function getRegistrationData() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

export function updateRegistrationData(fields) {
  const current = getRegistrationData();
  const updated = { ...current, ...fields };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  return updated;
}

export function clearRegistrationData() {
  localStorage.removeItem(STORAGE_KEY);
}