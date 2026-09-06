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

// TODO: بدّليها لعنوان الباك اند الفعلي لما يجهز (من .env مثلاً)
const API_BASE_URL = 'http://localhost:8000';

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
 * بترمي ApiError عند أي فشل (شبكة، أو رد بصيغة {error_code, message, details}).
 */
export async function apiRequest(path, options = {}) {
  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
      ...options,
    });
  } catch (networkErr) {
    // فشل الاتصال نفسه (السيرفر واقف، مافي إنترنت...) — قبل ما نوصل حتى لرد الباك
    throw new ApiError(
      'network_error',
      'تعذّر الاتصال بالسيرفر، تأكدي من الإنترنت وحاولي مرة تانية',
      null
    );
  }

  let body = null;
  try {
    body = await response.json();
  } catch {
    // الرد مش JSON أصلاً (نادراً ما يصير، بس منحميها)
  }

  if (!response.ok) {
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

export { ApiError };