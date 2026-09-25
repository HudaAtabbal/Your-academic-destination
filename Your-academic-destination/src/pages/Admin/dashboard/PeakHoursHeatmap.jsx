import { EVENT_DAYS } from '../../../api/eventDays';

const HEAT_COUNT = 5;

function heatIndex(value, max) {
  if (!max) return 0;
  const idx = Math.floor((value / max) * HEAT_COUNT);
  return Math.min(HEAT_COUNT - 1, Math.max(0, idx));
}

const DAY_ORDER = ['wed', 'thu', 'sat'];

export default function PeakHoursHeatmap({ peakHours }) {
  const hours = peakHours?.hours || [];
  const days = peakHours?.days || [];
  const peak = peakHours?.peak || null;
  const maxCount = Math.max(0, ...days.flatMap((d) => d.counts || []));

  const dayLabel = (key) => EVENT_DAYS.find((e) => e.key === key)?.label || key;

  const byDay = Object.fromEntries(days.map((d) => [d.day, d]));
  const rows = DAY_ORDER.filter((k) => byDay[k]);

  return (
    <div className="gd-dash-card">
      <div className="gd-dash-card-hd">
        <h3>ساعات الذروة</h3>
        {peak ? (
          <span className="gd-dash-peak-hint">
            الذروة: {dayLabel(peak.day)} {peak.hour}:00 – {peak.hour + 1}:00
          </span>
        ) : null}
      </div>

      {!rows.length ? (
        <div className="gd-dash-empty">ما في بيانات عن ساعات الذروة للآن</div>
      ) : (
        <>
          <div className="gd-dash-heat-wrap">
            <div
              className="gd-dash-heat"
              style={{ '--gd-heat-cols': hours.length }}
            >
              <span className="gd-dash-heat__h" />
              {hours.map((h) => (
                <span key={h} className="gd-dash-heat__h">
                  {h}:00
                </span>
              ))}
              {rows.map((dkey) => {
                const day = byDay[dkey];
                return (
                  <div key={dkey} className="gd-dash-heat__row" style={{ display: 'contents' }}>
                    <span className="gd-dash-heat__dl">{dayLabel(dkey)}</span>
                    {hours.map((h, hi) => {
                      const value = (day.counts || [])[hi] ?? 0;
                      const idx = heatIndex(value, maxCount);
                      const isPeak = peak && peak.day === dkey && peak.hour === h;
                      return (
                        <span
                          key={h}
                          className={`gd-dash-heat__c${isPeak ? ' is-peak' : ''}`}
                          style={{
                            backgroundColor: `var(--gd-heat-${idx})`,
                            color: idx >= 3 ? '#fff' : '#0d3a34',
                          }}
                        >
                          {value}
                        </span>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          </div>
          <div className="gd-dash-heatlg">
            أقل
            {Array.from({ length: HEAT_COUNT }, (_, i) => (
              <i key={i} style={{ backgroundColor: `var(--gd-heat-${i})` }} aria-hidden="true" />
            ))}
            أكثر · عدد المسحات بكل ساعة
          </div>
        </>
      )}
    </div>
  );
}