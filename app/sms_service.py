"""
إرسال رسائل SMS (رمز OTP) عبر خدمة سيرياتيل Bulk Messaging (SendTemplateSMS).
راجع BMS_API_EXTERNAL.pdf للتوثيق الرسمي الكامل.

⚠️ ملاحظات مهمة:
- شهادة SSL تبع سيرياتيل self-signed — لازم verify=False صراحة، وإلا
  الطلب بيفشل بخطأ SSL قبل ما يوصل حتى.
- القالب المعتمد محتاج قيمة وحدة بس بـ param_list (تأكّد بالتجربة اليدوية) —
  هي رمز التحقق نفسه.
- الرقم لازم يكون بالصيغة الدولية 963xxxxxxxxx، مش 09xxxxxxxxx يلي الفرونت
  بيجمعه من الطالب — التحويل بيصير هون تلقائياً.
"""

import os

import requests
import urllib3
from requests.exceptions import RequestException

# بما إنه شهادة سيرياتيل self-signed عمداً (verify=False)، بدون هاد السطر
# رح تنطبع تحذيرات InsecureRequestWarning بكل استدعاء — مزعجة وغير مفيدة
# بما إنه verify=False قرار مقصود، مش نسيان
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_BASE_URL = "https://bms.syriatel.sy/API/SendTemplateSMS.aspx"

_USERNAME = os.getenv("SYRIATEL_USERNAME")
_PASSWORD = os.getenv("SYRIATEL_PASSWORD")
_SENDER = os.getenv("SYRIATEL_SENDER")
_TEMPLATE_CODE = os.getenv("SYRIATEL_TEMPLATE_CODE")

# رسائل الخطأ الموثّقة رسمياً من سيرياتيل (BMS_API_EXTERNAL.pdf) — بنتحقق
# منها بنص الرد لأنه الـ API بيرجع 200 OK دايماً حتى بحالة الفشل، والفرق
# الوحيد هو نص الرسالة نفسها
_KNOWN_ERROR_MESSAGES = (
    "Missing required parameters",
    "User name or password is incorrect",
    "User isn't active",
    "You don't have permission to use API",
    "User can't perform this action",
    "Invalid optional parameters",
    "Sorry, Internal Error",
)


class SmsSendError(Exception):
    """بترمى لما سيرياتيل نفسها ترجع رسالة خطأ (مش مشكلة اتصال)."""


def _to_international_format(phone: str) -> str:
    """يحوّل 0991234567 (صيغة محلية) لـ 963991234567 (صيغة دولية مطلوبة من سيرياتيل)."""
    digits = phone.strip()
    if digits.startswith("963"):
        return digits
    if digits.startswith("0"):
        return "963" + digits[1:]
    return "963" + digits


def send_otp_sms(phone: str, otp_code: str) -> None:
    """
    بتبعت رمز الـ OTP عبر SMS للرقم المُعطى. بترمي SmsSendError لو سيرياتيل
    ردّت برسالة خطأ معروفة، أو RequestException لو فشل الاتصال نفسه
    (السيرفر واقف، انقطاع شبكة، إلخ) — الطبقة يلي فوق (registration_service)
    هي المسؤولة تقرر شو تسوي بكل حالة.
    """
    if not all([_USERNAME, _PASSWORD, _SENDER, _TEMPLATE_CODE]):
        raise RuntimeError(
            "بيانات حساب سيرياتيل (SYRIATEL_*) مش معرّفة بالـ .env — "
            "راجعي .env.example"
        )

    params = {
        "user_name": _USERNAME,
        "password": _PASSWORD,
        "template_code": _TEMPLATE_CODE,
        "param_list": otp_code,
        "sender": _SENDER,
        "to": _to_international_format(phone),
    }

    # verify=False لازم — شهادة سيرياتيل self-signed (موثّق بآخر صفحة بالـ PDF)
    response = requests.get(_BASE_URL, params=params, verify=False, timeout=15)
    response.raise_for_status()  # بيرمي RequestException لو الرد نفسه HTTP error (500/404 إلخ)

    body_text = response.text.strip()

    for error_message in _KNOWN_ERROR_MESSAGES:
        if error_message in body_text:
            raise SmsSendError(body_text)