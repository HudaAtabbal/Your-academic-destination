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
 * عالقة بالمتصفح لمدة غير محدودة. بعد مرور EXPIRY_MS من أول مرة بلش فيها
 * التسجيل (createdAt)، بتعتبر البيانات منتهية وبتنمسح تلقائياً أول ما حدا
 * يحاول يقراها — بغض النظر قديش صار فيها تحديثات بينات فترة.
 *
 * ملاحظة مهمة: الانتهاء محسوب من createdAt (أول تحديث) مش من updatedAt
 * (آخر تحديث). هيك لو الطالب رجع يفتح الفورم بعد يوم أو يومين وعدّل حقل،
 * الـ 24 ساعة ما بترجع تتصفّر من جديد — بتضل تحسب من أول مرة بلش فيها فعلياً.
 *
 * الاستخدام:
 *   import { updateRegistrationData, getRegistrationData, clearRegistrationData } from '.../RegistrationStorage';
 *   updateRegistrationData({ fullName: '...' }); // بكل تغيير بالفورم (مش بس عند الضغط على "تابع")
 *   const data = getRegistrationData(); // لتحميل البيانات المحفوظة عند فتح/إعادة فتح أي خطوة
 *   clearRegistrationData(); // بعد نجاح الإرسال الفعلي للباك، حتى ما تضل بيانات قديمة لو رجع الطالب يسجّل من جديد
 */

const STORAGE_KEY = 'registrationData';

// مدة الصلاحية: 24 ساعة، محسوبة من أول تحديث (createdAt). عدّلها حسب اللي بتحتاجه (بالميلي ثانية)
const EXPIRY_MS = 24 * 60 * 60 * 1000;

export function getRegistrationData() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};

    const parsed = JSON.parse(raw);

    // ما في وقت إنشاء محفوظ (بيانات قديمة من نسخة سابقة ما كانت فيها هاي الميزة) — نعتبرها منتهية احتياطاً
    if (!parsed.createdAt) {
      clearRegistrationData();
      return {};
    }

    const isExpired = Date.now() - parsed.createdAt > EXPIRY_MS;
    if (isExpired) {
      clearRegistrationData();
      return {};
    }

    // منرجع البيانات بدون حقول createdAt/updatedAt حتى ما تختلط مع بيانات الفورم الفعلية
    const { createdAt, updatedAt, ...data } = parsed;
    return data;
  } catch {
    return {};
  }
}

export function updateRegistrationData(fields) {
  // بنقرأ القيمة الخام مباشرة (مش عبر getRegistrationData) حتى نحافظ على
  // createdAt الأصلي بدل ما ينمسح أو يتصفّر بسبب منطق getRegistrationData
  let existingCreatedAt = null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      // منستخدم createdAt الموجود فقط إذا البيانات لسا صالحة (نفس شرط الانتهاء)
      if (parsed.createdAt && Date.now() - parsed.createdAt <= EXPIRY_MS) {
        existingCreatedAt = parsed.createdAt;
      }
    }
  } catch {
    existingCreatedAt = null;
  }

  const current = getRegistrationData(); // هاد بينضف تلقائياً إذا كانت البيانات منتهية
  const now = Date.now();
  const updated = {
    ...current,
    ...fields,
    createdAt: existingCreatedAt ?? now, // ما بيتصفّر إلا إذا كانت هاي أول مرة أو البيانات القديمة انتهت
    updatedAt: now,
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));

  const { createdAt, updatedAt, ...dataOnly } = updated;
  return dataOnly;
}

export function clearRegistrationData() {
  localStorage.removeItem(STORAGE_KEY);
}