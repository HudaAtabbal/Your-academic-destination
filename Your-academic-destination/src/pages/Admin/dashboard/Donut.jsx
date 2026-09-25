export default function Donut({ title, headerTotal, filter, series, empty }) {
  const total = series.reduce((acc, s) => acc + s.count, 0);

  const parts = series.map((s) => ({
    ...s,
    pct: total ? Math.round((s.count / total) * 100) : 0,
  }));

  const arcs = parts.reduce((list, s) => {
    const prev = list.length ? list[list.length - 1] : null;
    list.push({ ...s, offset: prev ? prev.offset - prev.pct : 0 });
    return list;
  }, []);

  return (
    <div className="gd-dash-card">
      <div className="gd-dash-card-hd">
        <h3>{title}</h3>
        {(headerTotal != null || filter) && (
          <div className="gd-dash-card-hd__side">
            {headerTotal != null && <span className="gd-dash-tot">{headerTotal}</span>}
            {filter}
          </div>
        )}
      </div>

      {!total ? (
        <div className="gd-dash-empty">{empty}</div>
      ) : (
        <div className="gd-dash-donut">
          <div className="gd-dash-donut__circle">
            <svg viewBox="0 0 42 42" className="gd-dash-donut__svg" aria-hidden="true">
              <circle cx="21" cy="21" r="15.9" fill="none" stroke="currentColor" strokeWidth="6" className="gd-dash-donut__track" />
              {arcs.map((s) => (
                <circle
                  key={s.key}
                  cx="21"
                  cy="21"
                  r="15.9"
                  fill="none"
                  stroke={s.color}
                  strokeWidth="6"
                  strokeLinecap="round"
                  strokeDasharray={`${s.pct} ${100 - s.pct}`}
                  strokeDashoffset={s.offset}
                />
              ))}
            </svg>
            <b className="gd-dash-donut__val">{total}</b>
          </div>
          <div className="gd-dash-donut__lg">
            {parts.map((s) => (
              <span key={s.key} className="gd-dash-donut__lg-item">
                <i style={{ backgroundColor: s.color }} aria-hidden="true" />
                {s.label}
                <em>
                  {s.pct}٪ ({s.count})
                </em>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}