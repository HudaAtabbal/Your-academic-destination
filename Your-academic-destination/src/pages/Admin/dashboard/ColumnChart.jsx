export default function ColumnChart({ title, items, empty, totalText, filter }) {
  const max = Math.max(0, ...items.map((i) => i.count));

  return (
    <div className="gd-dash-card">
      <div className="gd-dash-card-hd">
        <h3>{title}</h3>
        {(totalText != null || filter) && (
          <div className="gd-dash-card-hd__side">
            {totalText != null && <span className="gd-dash-tot gd-dash-tot--strong">{totalText}</span>}
            {filter}
          </div>
        )}
      </div>

      {!items.length ? (
        <div className="gd-dash-empty">{empty}</div>
      ) : (
        <div className="gd-dash-cols">
          {items.map((it, i) => {
            const pct = max ? Math.max(2, Math.round((it.count / max) * 100)) : 0;
            const isHi = max > 0 && it.count === max;
            return (
              <div className="gd-dash-cols__col" key={`${it.label}-${i}`}>
                <b>{it.count}</b>
                <i className={`gd-dash-cols__bar${isHi ? ' is-hi' : ''}`} style={{ height: `${pct}%` }} />
                <small title={String(it.label)}>{it.label}</small>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}