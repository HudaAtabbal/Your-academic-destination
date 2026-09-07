import React, { useEffect, useRef, useState } from 'react';
import { Html5Qrcode } from 'html5-qrcode';

/**
 * صندوق المسح — كاميرا حقيقية عبر html5-qrcode.
 * بمجرد ما تلتقط رمز QR، بتستدعي onScan(decodedText) تلقائياً.
 * فيها فترة "تبريد" قصيرة بعد كل مسح ناجح حتى ما تكرر نفس الرمز بالغلط
 * (لأنو الكاميرا بتضل شغالة وبتشوف نفس الملصق كذا مرة بالثانية).
 */
const ScanBox = ({ caption = 'وجّه الكاميرا نحو رمز QR تبع الطالب', onScan }) => {
  const scannerRef = useRef(null);
  const lastScanRef = useRef({ text: '', time: 0 });
  const containerIdRef = useRef(`qr-reader-${Math.random().toString(36).slice(2)}`);
  const isStartingRef = useRef(false); // حماية من React StrictMode يلي بيشغّل الـ effect مرتين بالتطوير
  const [cameraError, setCameraError] = useState('');

  useEffect(() => {
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
            const now = Date.now();
            if (decodedText === lastScanRef.current.text && now - lastScanRef.current.time < 3000) {
              return;
            }
            lastScanRef.current = { text: decodedText, time: now };
            onScan(decodedText);
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
  }, [onScan]);

  return (
    <div className="scan-box-wrapper">
      <div id={containerIdRef.current} className="scan-box-camera" />
      {cameraError ? (
        <p className="scan-camera-error">{cameraError}</p>
      ) : (
        <p className="scan-caption">{caption}</p>
      )}
    </div>
  );
};

export default ScanBox;