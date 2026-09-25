import { Link } from 'react-router-dom';
import DayFilter from './DayFilter';

const DASH = '—';

function pct(part, total) {
  if (!total) return 0;
  return Math.round((part / total) * 100);
}

export default function SummaryCards({ stats, gameScans, day, onDayChange }) {
  const { registered_online_count, registered_no_show_count, walkin_pending_count, walkin_completed_count, total_consultations } =
    stats || {};

  const attended = registered_online_count != null && registered_no_show_count != null ? Math.max(0, registered_online_count - registered_no_show_count) : null;
  const regTotal = registered_online_count;
  const attendedPct = attended != null && regTotal != null ? pct(attended, regTotal) : null;
  const noShowPct = attendedPct != null && regTotal != null ? pct(regTotal - attended, regTotal) : null;

  const walkTotal = walkin_completed_count != null && walkin_pending_count != null ? walkin_completed_count + walkin_pending_count : null;
  const walkPct = walkTotal ? pct(walkin_completed_count, walkTotal) : (walkin_completed_count == null ? null : 0);
  const walkPendingPct = walkPct != null && walkTotal ? 100 - walkPct : null;

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
    </div>
  );
}