import { Link } from 'react-router-dom';

const DASH = '—';

const TABS = [
  { key: 'lectures', label: 'أكثر حضور محاضرات' },
  { key: 'tours', label: 'أكثر جولات كليات' },
  { key: 'presence', label: 'أطول تواجد بالجامعة' },
];

const UNIT = {
  lectures: 'محاضرة',
  tours: 'جولة',
  presence: 'تواجد',
  union_all: 'الأركان الثلاثة',
};

function fmtPresence(val) {
  const n = Number(val);
  if (Number.isNaN(n) || !Number.isFinite(n)) return DASH;
  const h = Math.floor(n / 60);
  const m = Math.round(n % 60);
  if (h === 0) return `${m}د`;
  if (m === 0) return `${h}س`;
  return `${h}س ${m}د`;
}

function fmtDays(d) {
  const n = Number(d);
  if (!Number.isFinite(n) || n <= 0) return null;
  if (n === 1) return 'يوم واحد';
  if (n === 2) return 'يومين';
  return `${n} أيام`;
}

export default function TopStudents({ metric, onMetricChange, data, unionTotal }) {
  const items = data?.items?.length ? data.items : [];

  return (
    <div className="gd-dash-card">
      <div className="gd-dash-card-hd">
        <h3>الطلاب المتميزون</h3>
        <Link className="gd-dash-more" to={`/dashboard-top-students?metric=${metric}`}>
          عرض القائمة الكاملة
        </Link>
      </div>

      <div className="gd-dash-tabs" role="tablist" aria-label="المعيار">
        {[...TABS, { key: 'union_all', label: `زاروا كل أركان الاتحاد (${unionTotal == null ? DASH : unionTotal})` }].map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={metric === t.key}
            className={metric === t.key ? 'gd-dash-tabs__btn is-on' : 'gd-dash-tabs__btn'}
            onClick={() => onMetricChange(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {!items.length ? (
        <div className="gd-dash-empty">ما في بيانات عن الطلاب المتميزين للآن</div>
      ) : (
        <div className="gd-dash-lead">
          {items.map((s) => (
            <div className="gd-dash-lead__item" key={s.unique_code || s.rank || s.full_name}>
              <span className="gd-dash-lead__rk">#{s.rank}</span>
              <span className="gd-dash-lead__nm">{s.full_name || DASH}</span>
              <span className="gd-dash-lead__cd">{s.unique_code || DASH}</span>
              <span className="gd-dash-lead__val">
                {s.value == null
                  ? DASH
                  : metric === 'union_all'
                    ? 'الأركان الثلاثة'
                    : metric === 'presence'
                      ? `${fmtPresence(s.value)}${s.days != null && fmtDays(s.days) ? ` · على ${fmtDays(s.days)}` : ''}`
                      : s.value}
                {s.value != null && (metric === 'lectures' || metric === 'tours') && (
                  <small>
                    {' '}
                    {UNIT[metric] || 'مرة'}
                  </small>
                )}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}