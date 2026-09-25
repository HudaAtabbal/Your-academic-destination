import { useState } from 'react';

export default function HorizontalBars({
  items,
  title,
  totalText,
  filter,
  accent = 'teal',
  empty,
  expandable = false,
  expandLabel = null,
}) {
  const [showAll, setShowAll] = useState(false);
  const max = Math.max(0, ...items.map((i) => i.count));

  const visible = showAll || !expandable ? items : items.slice(0, 8);

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
        <>
          <div className={`gd-dash-hb gd-dash-hb--${accent}`}>
            {visible.map((it, i) => (
              <div className="gd-dash-hb__r" key={`${it.label}-${i}`}>
                <span className="gd-dash-hb__t" title={it.title != null ? it.title : it.label}>
                  {it.label}
                </span>
                <div className="gd-dash-hb__track">
                  <i style={{ width: `${max ? Math.round((it.count / max) * 100) : 0}%` }} />
                </div>
                <span className="gd-dash-hb__v">{it.count}</span>
              </div>
            ))}
          </div>
          {expandable && items.length > 8 && (
            <button
              type="button"
              className="gd-dash-more"
              onClick={() => setShowAll((s) => !s)}
            >
              {showAll ? 'عرض أقل' : expandLabel ? expandLabel(items.length) : `عرض الكل (${items.length})`}
            </button>
          )}
        </>
      )}
    </div>
  );
}