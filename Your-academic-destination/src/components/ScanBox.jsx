import React, { useEffect, useRef, useState } from 'react';
import { Html5Qrcode } from 'html5-qrcode';

/**
 * صندوق المسح — كاميرا حقيقية عبر html5-qrcode.
 * بمجرد ما تلتقط رمز QR، بتستدعي onScan(decodedText) تلقائياً.
 *
 * حمايتين ضد التكرار:
 *  1. isProcessingRef — منع أي مسح جديد (أي رمز كان) لحد ما يخلص onScan
 *     الحالي فعلياً (يعني لحد ما يوصل رد الباك، نجاح أو فشل). هاي الحماية
 *     الأساسية، ومرتبطة بحالة الطلب الفعلية مش بمؤقت ثابت.
 *  2. lastScanRef — فترة "تبريد" 3 ثواني لنفس الرمز بالضبط، حتى ما تتكرر
 *     نفس القراءة عدة مرات بالثانية الواحدة (الكاميرا بتشوف نفس الملصق
 *     أكتر من مرة وهي شغالة).
 *
 * isBusy (state) مرتبط بـ isProcessingRef بس منعكس بصرياً — حتى الموظف
 * يشوف إشارة واضحة "في طلب قيد المعالجة" بدل ما يفكر الكاميرا ما استلمت
 * المسح ويحاول يقرب الكرت أو يهزّه بلا داعي.
 */
const ScanBox = ({ caption = 'وجّه الكاميرا نحو رمز QR تبع الطالب', onScan, paused = true, onResume }) => {
  const scannerRef = useRef(null);
  const lastScanRef = useRef({ text: '', time: 0 });
  const isProcessingRef = useRef(false); // منع أي مسح جديد أثناء معالجة مسح سابق
  const containerIdRef = useRef(`qr-reader-${Math.random().toString(36).slice(2)}`);
  const isStartingRef = useRef(false); // حماية من React StrictMode يلي بيشغّل الـ effect مرتين بالتطوير
  const [cameraError, setCameraError] = useState('');
  const [isBusy, setIsBusy] = useState(false); // نسخة مرئية من isProcessingRef

  useEffect(() => {
    // لو متوقفة يدوياً (paused=true)، ما منشغّل الكاميرا خالص — منستنى لحد ما تنرجع false
    if (paused) return;

    const containerId = containerIdRef.current;
    let isMounted = true;
    let html5QrCode;

    const start = async () => {
      if (isStartingRef.current) return;
      isStartingRef.current = true;

      try {
        html5QrCode = new Html5Qrcode(containerId);
        scannerRef.current = html5QrCode;

        await html5QrCode.start(
          { facingMode: 'environment' },
          { fps: 10, qrbox: { width: 220, height: 220 } },
          (decodedText) => {
            // في مسح شغال أصلاً (بانتظار رد الباك) — نتجاهل أي رمز جديد
            // لحد ما يخلص، بغض النظر شو الرمز الجديد كان
            if (isProcessingRef.current) return;

            const now = Date.now();
            if (decodedText === lastScanRef.current.text && now - lastScanRef.current.time < 3000) {
              return;
            }
            lastScanRef.current = { text: decodedText, time: now };

            isProcessingRef.current = true;
            if (isMounted) setIsBusy(true);

            // onScan (handleScan بالصفحات) أصلاً async وبترجع Promise —
            // منستنى نتيجتها الفعلية قبل ما نفتح الباب لمسح جديد
            Promise.resolve(onScan(decodedText)).finally(() => {
              isProcessingRef.current = false;
              if (isMounted) setIsBusy(false);
            });
          },
          () => {
            // بيستدعى كتير أثناء البحث عن رمز — طبيعي، ما منعرض شي
          }
        );
      } catch (err) {
        console.error('فشل تشغيل الكاميرا', err);
        if (isMounted) {
          setCameraError('ما قدرنا نشغّل الكاميرا — تأكدي إنك عطيتي إذن الوصول إلها بالمتصفح');
        }
      }
    };

    start();

    return () => {
      isMounted = false;
      const instance = scannerRef.current;
      if (instance) {
        // بنتأكد الكاميرا فعلاً شغالة قبل ما نحاول نوقفها،
        // وإلا بترمي استثناء غير ملتقط بيكسر الصفحة كاملة (شاشة بيضا)
        try {
          if (instance.isScanning) {
            instance
              .stop()
              .then(() => instance.clear())
              .catch(() => {})
              .finally(() => {
                isStartingRef.current = false;
              });
          } else {
            isStartingRef.current = false;
          }
        } catch {
          isStartingRef.current = false;
        }
      }
    };
  }, [onScan, paused]);

  return (
    <div className="scan-box-wrapper">
      {paused ? (
        <div className="scan-box-paused">
          <p className="scan-paused-text">الكاميرا متوقفة</p>
          <button type="button" className="scan-resume-btn" onClick={onResume}>
            ▶ تشغيل الكاميرا
          </button>
        </div>
      ) : (
        <div className="scan-box-camera-wrapper">
          <div id={containerIdRef.current} className="scan-box-camera" />
          {isBusy && (
            <div className="scan-box-busy-overlay">
              <span className="scan-box-busy-text">جاري المعالجة...</span>
            </div>
          )}
        </div>
      )}
      {cameraError ? (
        <p className="scan-camera-error">{cameraError}</p>
      ) : (
        !paused && <p className="scan-caption">{caption}</p>
      )}
    </div>
  );
};

export default ScanBox;