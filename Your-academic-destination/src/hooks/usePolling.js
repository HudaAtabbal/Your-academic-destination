import { useEffect, useRef } from 'react';

/**
 * يشرّع دالة جلب بفواصل زمنية: يجلب فوراً ثم كل intervalMs.
 * يتوقف تلقائياً عندما تكون الصفحة مخفية، ويجلب فوراً عند العودة للظهور.
 * عند تغيير deps يجلب فوراً من جديد. لا يتطلب أي تنظيف يدوي.
 */
export default function usePolling(fetchFn, intervalMs, deps = []) {
  const fetchRef = useRef(fetchFn);
  fetchRef.current = fetchFn;

  useEffect(() => {
    let timer = null;

    const run = () => {
      fetchRef.current();
    };

    const startTimer = () => {
      if (timer) clearInterval(timer);
      timer = setInterval(run.bind(null), intervalMs);
    };

    const onVisibility = () => {
      if (document.visibilityState === 'hidden') {
        if (timer) {
          clearInterval(timer);
          timer = null;
        }
      } else {
        run();
        startTimer();
      }
    };

    run();
    startTimer();
    document.addEventListener('visibilitychange', onVisibility);

    return () => {
      if (timer) clearInterval(timer);
      document.removeEventListener('visibilitychange', onVisibility);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs, ...deps]);
}