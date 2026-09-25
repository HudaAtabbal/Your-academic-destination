import { useEffect, useRef } from 'react';
import { apiPost } from '../api/api';

/**
 * usePageVisit — يسجّل كم مرة انفتحت الصفحة وكم بقي الزائر فيها.
 *
 * المدّة نفسها بتقيسها الواجهة (قديش ثانية بقيت الصفحة مفتوحة)، لكن
 * الباك اند هو يلي يخزّن entered_at ويحسب الفرق لحاله — فما في أي رقم
 * مدّة بيجي من المتصفح وبيقبل. لو حدا عبّث بالـ JS ما بيقدر يضخّم الأرقام.
 *
 * سلوك التتبّع (قواعد مقصودة):
 * 1. ما بنبلّش تسجيل الزيارة قبل 3 ثواني حضور *فعلي* — فتح وطلع فوراً
 *    ارتداد سريع، وما منفع عدّه زيارة. العدّاد بيتجمّد وقت إخفاء التبويب.
 * 2. بلّغ النهاية لما يطلع أو يتنقّل، وعند إخفاء التبويب وقبل إغلاق الصفحة
 *    (pagehide) — لأن إغلاق التبويب ما بيوصله fetch عادي.
 * 3. معرّف الزائر (visitor_id) بيتولّد مرة وحدة بمخزن المتصفح، وبهذا بعدّ
 *    الأشخاص المختلفين. ما بنستعمل الـ IP أبداً: كل طلبة الجامعة على نفس
 *    شبكة الواي-فاي، فالـ IP ما بيمثّل شخص.
 *
 * الاستدعاء: usePageVisit(active, 'academic-guide') — `active` هو التبويب
 * الظاهر حالياً (StudentTabsLayout بيفوتّره لكل صفحة).
 */

const VISITOR_ID_KEY = 'pageVisitVisitorId';
const MIN_DWELL_MS = 3000;
const DEFAULT_PAGE = 'academic-guide';

function getVisitorId() {
  try {
    let id = localStorage.getItem(VISITOR_ID_KEY);
    if (!id) {
      // crypto.randomUUID بدّه سياق آمن (HTTPS أو localhost) — على شبكة
      // الجامعة فوق HTTP بيرمي استثناء، فبنعمل بديل احتياطي.
      id =
        typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
          ? crypto.randomUUID()
          : `v-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`;
      localStorage.setItem(VISITOR_ID_KEY, id);
    }
    return id;
  } catch {
    // وضع التصفّح الخاص أو localStorage محجوب — تتبّع بلا هوية.
    return 'anonymous';
  }
}

export default function usePageVisit(active, page = DEFAULT_PAGE) {
  // حارس StrictMode: بوضع التطوير كل useEffect بيتنفّذ مرتين ورا بعض.
  // بلا هالـ guard، كل فتح للصفحة بينبلّغ مرتين.
  const startedRef = useRef(false);
  const visitIdRef = useRef(null);
  const dwellRef = useRef(0);

  useEffect(() => {
    if (!active) return undefined;

    let ticking = null;

    // أي فشل بالتتبّع بينتجاهل بالكامل — ما لازم يعلّق صفحة الطالب.
    const fire = (path, payload) => apiPost(path, payload).catch(() => {});

    const beginVisit = () => {
      if (startedRef.current) return;
      startedRef.current = true;
      apiPost('/students/page-visit/start', {
        page,
        visitor_id: getVisitorId(),
        student_code: localStorage.getItem('studentCode') || null,
      })
        .then((data) => {
          visitIdRef.current = data?.visit_id ?? null;
        })
        .catch(() => {
          // ما في رقم زيارة = ما في شي نختمه.
          startedRef.current = false;
        });
    };

    const endVisit = () => {
      if (!visitIdRef.current) return;
      fire('/students/page-visit/end', { visit_id: visitIdRef.current });
      visitIdRef.current = null;
      startedRef.current = false;
      dwellRef.current = 0;
    };

    const tick = () => {
      if (document.visibilityState !== 'visible') return;
      dwellRef.current += 1000;
      if (dwellRef.current >= MIN_DWELL_MS) beginVisit();
    };

    // إخفاء التبويب بيختم الزيارة، والرجوع بيبلّش العدّاد من الصفر — ما
    // بدنا نحسب مدة الطالب وهو ساكّر عالشاشة بتبويب مفتوح.
    const onVisibility = () => {
      if (document.visibilityState === 'hidden') {
        endVisit();
        dwellRef.current = 0;
      }
    };

    // بنبلّش بعد أول ثانية — الهدف 3 ثواني حضور فعلي، فأول تكة ما بتنتسب
    // (غيرها بدنا نعدّ ثانية كاملة قبل ما تمر).
    ticking = setInterval(tick, 1000);    document.addEventListener('visibilitychange', onVisibility);
    window.addEventListener('pagehide', endVisit);

    return () => {
      if (ticking) clearInterval(ticking);
      document.removeEventListener('visibilitychange', onVisibility);
      window.removeEventListener('pagehide', endVisit);
      endVisit();
    };
  }, [active, page]);
}
