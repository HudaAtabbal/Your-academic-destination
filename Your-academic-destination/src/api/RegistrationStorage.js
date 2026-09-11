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
 * ليش فيها انتهاء صلاحية؟
 * حتى ما تضل بيانات قديمة (مثلاً طالب بلش تسجيل بس ما كمّل، ورجع بعد أسابيع)
 * عالقة بالمتصفح لمدة غير محدودة. بعد مرور EXPIRY_MS من آخر تحديث، بتعتبر
 * البيانات منتهية وبتنمسح تلقائياً أول ما حدا يحاول يقراها.
 *
 * الاستخدام:
 *   import { updateRegistrationData, getRegistrationData, clearRegistrationData } from '.../RegistrationStorage';
 *   updateRegistrationData({ fullName: '...' }); // بكل تغيير بالفورم (مش بس عند الضغط على "تابع")
 *   const data = getRegistrationData(); // لتحميل البيانات المحفوظة عند فتح/إعادة فتح أي خطوة
 *   clearRegistrationData(); // بعد نجاح الإرسال الفعلي للباك، حتى ما تضل بيانات قديمة لو رجع الطالب يسجّل من جديد
 */

const STORAGE_KEY = 'registrationData';

// مدة الصلاحية: 24 ساعة. عدّلها حسب اللي بتحتاجه (بالميلي ثانية)
const EXPIRY_MS = 24 * 60 * 60 * 1000;

export function getRegistrationData() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};

    const parsed = JSON.parse(raw);

    // ما في وقت محفوظ (بيانات قديمة من نسخة سابقة ما كانت فيها هاي الميزة) — نعتبرها منتهية احتياطاً
    if (!parsed.updatedAt) {
      clearRegistrationData();
      return {};
    }

    const isExpired = Date.now() - parsed.updatedAt > EXPIRY_MS;
    if (isExpired) {
      clearRegistrationData();
      return {};
    }

    // منرجع البيانات بدون حقل updatedAt حتى ما يختلط مع بيانات الفورم الفعلية
    const { updatedAt, ...data } = parsed;
    return data;
  } catch {
    return {};
  }
}

export function updateRegistrationData(fields) {
  const current = getRegistrationData();
  const updated = { ...current, ...fields, updatedAt: Date.now() };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));

  const { updatedAt, ...dataOnly } = updated;
  return dataOnly;
}

export function clearRegistrationData() {
  localStorage.removeItem(STORAGE_KEY);
}