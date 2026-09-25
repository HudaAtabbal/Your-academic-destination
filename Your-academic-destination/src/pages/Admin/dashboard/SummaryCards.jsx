import { Link } from 'react-router-dom';
import DayFilter from './DayFilter';

const DASH = '—';

function pct(part, total) {
  if (!total) return 0;
  return Math.round((part / total) * 100);
}

// مدّة بالثواني ← "3:20" (دقائق:ثواني). أقل من دقيقة بتعرض بالثواني بس.
function mmss(seconds) {
  if (seconds == null) return DASH;
  const total = Math.round(seconds);
  const m = Math.floor(total / 60);
  const s = total % 60;
  if (m === 0) return `${s} ثانية`;
  return `${m}:${String(s).padStart(2, '0')}`;
}

// "مرة لكل شخص" بتصريف عربي صحيح حسب العدد.
function timesPer(n) {
  if (n === 1) return 'مرة واحدة لكل شخص';
  if (n === 2) return 'مرتين لكل شخص';
  if (n <= 10) return `${n} مرات لكل شخص`;
  return `${n} مرة لكل شخص`;
}

export default function SummaryCards({
  stats,
  gameScans,
  day,
  onDayChange,
  guide,
  guideDay,
  onGuideDayChange,
}) {
  const { registered_online_count, registered_no_show_count, walkin_pending_count, walkin_completed_count, total_consultations } =
    stats || {};

  const attended = registered_online_count != null && registered_no_show_count != null ? Math.max(0, registered_online_count - registered_no_show_count) : null;
  const regTotal = registered_online_count;
  const attendedPct = attended != null && regTotal != null ? pct(attended, regTotal) : null;
  const noShowPct = attendedPct != null && regTotal != null ? pct(regTotal - attended, regTotal) : null;

  const walkTotal = walkin_completed_count != null && walkin_pending_count != null ? walkin_completed_count + walkin_pending_count : null;
  const walkPct = walkTotal ? pct(walkin_completed_count, walkTotal) : (walkin_completed_count == null ? null : 0);
  const walkPendingPct = walkPct != null && walkTotal ? 100 - walkPct : null;

  const guideVisitors = guide?.visitors_count ?? null;
  const guideVisits = guide?.visits_count ?? null;
  const guideAvg = guide?.avg_duration_seconds ?? null;
  const guidePerPerson = guideVisitors && guideVisits != null ? Math.round(guideVisits / guideVisitors) : null;

  return (
    <div className="gd-dash-groups">
      <div className="gd-dash-card">
        <h3>
          التسجيل الإلكتروني
          <Link to="/dashboard-no-shows">مسجّلون بلا حضور</Link>
        </h3>
        <div className="gd-dash-split">
          <div>
            <div className="gd-dash-split__n">{attended == null ? DASH : attended}</div>
            <div className="gd-dash-split__l">حضروا</div>
          </div>
          <div>
            <div className="gd-dash-split__n gd-dash-split__n--warn">{registered_no_show_count == null ? DASH : registered_no_show_count}</div>
            <div className="gd-dash-split__l">بلا حضور</div>
          </div>
        </div>
        <div className="gd-dash-bar">
          {attendedPct != null && <i style={{ width: `${attendedPct}%` }} />}
          {noShowPct != null && <i className="gd-dash-bar__o" style={{ width: `${noShowPct}%` }} />}
        </div>
        <div className="gd-dash-cap">{attendedPct == null ? '' : `${attendedPct}٪ من المسجّلين حضروا فعلاً`}</div>
      </div>

      <div className="gd-dash-card">
        <h3>
          سجلات Walk-in
          <Link to="/gate-incomplete">تنتظر الإكمال</Link>
        </h3>
        <div className="gd-dash-split">
          <div>
            <div className="gd-dash-split__n">{walkin_completed_count == null ? DASH : walkin_completed_count}</div>
            <div className="gd-dash-split__l">تم إكمالها</div>
          </div>
          <div>
            <div className="gd-dash-split__n gd-dash-split__n--warn">{walkin_pending_count == null ? DASH : walkin_pending_count}</div>
            <div className="gd-dash-split__l">تنتظر الإكمال</div>
          </div>
        </div>
        <div className="gd-dash-bar">
          {walkPct != null && <i style={{ width: `${walkPct}%` }} />}
          {walkPendingPct != null && <i className="gd-dash-bar__o" style={{ width: `${walkPendingPct}%` }} />}
        </div>
        <div className="gd-dash-cap">{walkPct == null ? '' : `${walkPct}٪ من السجلات مكتملة`}</div>
      </div>

      <div className="gd-dash-card gd-dash-solo">
        <h3>إجمالي الاستشارات</h3>
        <div className="gd-dash-solo__n">{total_consultations == null ? DASH : total_consultations}</div>
        <div className="gd-dash-cap">استشارة وحدة لكل طالب</div>
      </div>

      <div className="gd-dash-card gd-dash-solo">
        <h3>مسحات ركن الترفيه</h3>
        <div className="gd-dash-solo__chips">
          <DayFilter value={day} onChange={onDayChange} />
        </div>
        <div className="gd-dash-solo__n gd-dash-solo__n--sm">{gameScans == null ? DASH : gameScans}</div>
        <div className="gd-dash-cap">مسح واحد لكل طالب طوال الفعالية</div>
      </div>

      <div className="gd-dash-card gd-dash-solo gd-dash-guide">
        <h3>الدليل الأكاديمي</h3>
        <div className="gd-dash-solo__chips">
          <DayFilter value={guideDay} onChange={onGuideDayChange} />
        </div>
        <div className="gd-dash-guide__lbl">متوسط البقاء</div>
        <div className="gd-dash-solo__n gd-dash-solo__n--sm">{mmss(guideAvg)}</div>
        <div className="gd-dash-guide__rule" />
        <div className="gd-dash-guide__split">
          <div>
            <div className="gd-dash-guide__n">{guideVisitors == null ? DASH : guideVisitors}</div>
            <div className="gd-dash-guide__l">شخص</div>
          </div>
          <div>
            <div className="gd-dash-guide__n">{guideVisits == null ? DASH : guideVisits}</div>
            <div className="gd-dash-guide__l">مرة</div>
          </div>
        </div>
        <div className="gd-dash-cap">{guidePerPerson == null ? '' : `≈ ${timesPer(guidePerPerson)}`}</div>
      </div>
    </div>
  );
}