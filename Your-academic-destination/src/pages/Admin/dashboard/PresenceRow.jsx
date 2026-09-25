import { EVENT_DAYS } from '../../../api/eventDays';

const DASH = '—';

function pct(part, total) {
  if (!total) return 0;
  return Math.round((part / total) * 100);
}

function hms(min) {
  if (min == null || Number.isNaN(min)) return null;
  const h = Math.floor(min / 60);
  const m = Math.round(min % 60);
  if (h === 0) return `${m}د`;
  if (m === 0) return `${h}س`;
  return `${h}س ${m}د`;
}

function hmColon(min) {
  if (min == null || Number.isNaN(min)) return null;
  const h = Math.floor(min / 60);
  const m = Math.round(min % 60);
  return `${h}:${String(m).padStart(2, '0')}`;
}

const DAY_ORDER = ['wed', 'thu', 'sat'];

export default function PresenceRow({ presence }) {
  const perDay = presence?.per_day || [];
  const byDay = Object.fromEntries(perDay.map((d) => [d.day, d]));
  const maxDay = Math.max(0, ...perDay.map((d) => d.avg_minutes || 0));

  const freq = presence?.frequency;
  const freqTotal = freq?.total;
  const freqItems = [
    { key: 'one_day', label: 'يوم واحد', count: freq?.one_day },
    { key: 'two_days', label: 'يومين', count: freq?.two_days },
    { key: 'all_days', label: 'كل الأيام الثلاثة', count: freq?.all_days },
  ];

  return (
    <div className="gd-dash-grid2">
      <div className="gd-dash-card">
        <div className="gd-dash-card-hd">
          <h3>متوسط مدة التواجد</h3>
          <span className="gd-dash-tot gd-dash-tot--muted">تقدير: من أول لآخر نشاط للطالب باليوم</span>
        </div>
        <div className="gd-dash-dur">
          <div>
            <div className="gd-dash-dur__big">
              {presence?.avg_minutes_all == null ? DASH : hmColon(presence.avg_minutes_all)} <small>ساعة</small>
            </div>
            <div className="gd-dash-cap">متوسط كل الأيام</div>
          </div>
          <div className="gd-dash-dur__days">
            {DAY_ORDER.map((dkey) => {
              const d = byDay[dkey];
              const hasData = d && d.students_counted > 0 && d.avg_minutes > 0;
              const width = hasData && maxDay ? Math.round((d.avg_minutes / maxDay) * 100) : 0;
              return (
                <div key={dkey} className="gd-dash-day">
                  <span className="gd-dash-day__name">{EVENT_DAYS.find((e) => e.key === dkey)?.label}</span>
                  <div className="gd-dash-day__track">
                    <i style={{ width: `${width}%` }} />
                  </div>
                  <em className="gd-dash-day__val">{hasData ? hms(d.avg_minutes) : DASH}</em>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="gd-dash-card">
        <div className="gd-dash-card-hd">
          <h3>تكرار الحضور</h3>
          <span className="gd-dash-tot gd-dash-tot--muted">{freqTotal == null ? DASH : `${freqTotal} طالب`}</span>
        </div>
        <div className="gd-dash-freq">
          {freqItems.map((f) => (
            <div key={f.key} className={`gd-dash-freq__item${f.key === 'all_days' ? ' gd-dash-freq__item--top' : ''}`}>
              <div className="gd-dash-freq__l">{f.label}</div>
              <div className="gd-dash-freq__n">{f.count == null ? DASH : f.count}</div>
              <div className="gd-dash-freq__p">{f.count == null ? '' : `${pct(f.count, freqTotal || 0)}٪`}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}