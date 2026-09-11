/**
 * api.js — Wrapper مركزي لأي طلب للباك اند.
 *
 * ليش موجود هالملف؟
 * الباك اند بيرجّع الأخطاء بصيغة موحّدة دايماً:
 *   { error_code: "...", message: "رسالة بالعربي جاهزة للعرض", details: {...} }
 *
 * بدل ما كل صفحة تتعامل مع try/catch وتفكيك الـ response لحالها،
 * كل طلبات المشروع لازم تمر من هون. هيك:
 *   - أي خطأ من الباك بيوصل الصفحة كـ Error عادي، وبتقدري تعرضي err.message
 *     مباشرة بالواجهة (هو أصلاً عربي وجاهز، مش محتاج ترجمة أو تعديل).
 *   - error_code و details موجودين على الـ Error نفسه (err.errorCode, err.details)
 *     بحال احتجتي منطق خاص حسب نوع الخطأ (مثلاً تمييز خطأ فاليديشن عن خطأ صلاحيات).
 */

// العنوان الأساسي للباك اند — من متغير بيئة VITE_API_URL (ملف .env).
// لو ما اتعرف، بنسقط على localhost للـ تطوير المحلي.
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// أقصى مدة انتظار لأي طلب قبل ما ننهيه تلقائياً (بالميلي ثانية).
// بدونها، لو السيرفر أو الـ tunnel وقع، الطلب بيضل معلّق للأبد والواجهة
// بتضل عالقة بحالة "جاري التحميل" بلا أي رسالة للمستخدم.
const REQUEST_TIMEOUT_MS = 30000;

// مفتاح تخزين توكن تسجيل دخول فريق العمل (JWT) — نفس القيمة يلي بيرجّعها /auth/login
//
// مخزّن بـ sessionStorage (مش localStorage) عمداً:
//   - localStorage: بيرضل حتى بعد قفل التاب → لو فيه XSS، بيسرق جلسة تصمد 8 ساعات.
//   - sessionStorage: بيضل عند التحديث (F5) لكن بينمسح تلقائياً عند قفل التاب
//     → نافذة السرقة تصير مشروطة بتاب مفتوح، وأي تسريب بيختفي بقفل النافذة.
//   - بديل أأمن أصلاً (httpOnly cookie) بيحتاج تغيير على الباك يعتمد على cookies —
//     قرار مؤجّل، هاد حل وسط بمقدار تغيير صفر على الباك.
const AUTH_TOKEN_KEY = 'authToken';

export const getAuthToken = () => sessionStorage.getItem(AUTH_TOKEN_KEY);
export const setAuthToken = (token) => sessionStorage.setItem(AUTH_TOKEN_KEY, token);
export const clearAuthToken = () => sessionStorage.removeItem(AUTH_TOKEN_KEY);

class ApiError extends Error {
  constructor(errorCode, message, details) {
    super(message);
    this.name = 'ApiError';
    this.errorCode = errorCode;
    this.details = details;
  }
}

/**
 * apiRequest(path, options)
 * - path: مسار الـ endpoint، مثلاً '/students/register'
 * - options: نفس خيارات fetch العادية (method, body, headers...)
 *
 * بترجع الـ JSON body مباشرة عند النجاح.
 * بترمي ApiError عند أي فشل (شبكة، تايم أوت، أو رد بصيغة {error_code, message, details}).
 *
 * لو في توكن مخزّن (بعد تسجيل دخول فريق عمل)، بينضاف تلقائياً كـ
 * "Authorization: Bearer <token>" — ما محتاجة ترفقيه يدوياً بكل استدعاء.
 */
export async function apiRequest(path, options = {}) {
  let response;
  const token = getAuthToken();

  // AbortController: لو الطلب طوّل أكتر من REQUEST_TIMEOUT_MS، منلغيه تلقائياً
  // بدل ما يعلّق للأبد (مثلاً لو ngrok tunnel وقع بمنتصف الطلب)
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  // ننزع الـ headers و signal من options حتى ما يعبّوا عن القيم الجاهزة تحت
  // (كان ...options آخر سطر يمسح headers و signal صمتاً). أي خصائص تانية
  // (method, body, credentials...) بتنتقل كما هي.
  const { signal: callerSignal, headers: callerHeaders, ...restOptions } = options;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...restOptions,
      headers: {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true', // يمنع صفحة التحذير الوسيطة تبع ngrok المجاني
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(callerHeaders || {}),
      },
      signal: callerSignal || controller.signal,
    });
  } catch (networkErr) {
    if (networkErr.name === 'AbortError') {
      throw new ApiError(
        'timeout',
        'استغرق الاتصال بالسيرفر وقتاً أطول من المتوقع، تأكدي من الإنترنت وحاولي مرة تانية',
        null
      );
    }

    // فشل الاتصال نفسه (السيرفر واقف، مافي إنترنت...) — قبل ما نوصل حتى لرد الباك
    throw new ApiError(
      'network_error',
      'تعذّر الاتصال بالسيرفر، تأكدي من الإنترنت وحاولي مرة تانية',
      null
    );
  } finally {
    clearTimeout(timeoutId);
  }

  let body = null;
  try {
    body = await response.json();
  } catch {
    // الرد مش JSON أصلاً (نادراً ما يصير، بس منحميها)
  }

  if (!response.ok) {
    // التوكن غلط/منتهي — منمسحه تلقائياً حتى ما تضل الصفحة تحاول فيه من جديد بلا فايدة
    if (response.status === 401) {
      clearAuthToken();
    }

    throw new ApiError(
      body?.error_code || 'unknown_error',
      body?.message || 'صار خطأ غير متوقع، حاولي مرة تانية',
      body?.details || null
    );
  }

  return body;
}

// اختصارات جاهزة للاستخدام الشائع
export const apiGet = (path) => apiRequest(path, { method: 'GET' });
export const apiPost = (path, data) =>
  apiRequest(path, { method: 'POST', body: JSON.stringify(data) });
export const apiPut = (path, data) =>
  apiRequest(path, { method: 'PUT', body: JSON.stringify(data) });
export const apiPatch = (path, data) =>
  apiRequest(path, { method: 'PATCH', body: JSON.stringify(data) });

export { ApiError };