// مجموعة أزرار صغيرة (Segmented control) — نفس ستايل فلتر الأيام، بس
// بتاخد خياراتها من المتصل بدل ما تكون مثبّتة على أيام الفعالية.
export default function SegmentedControl({ options, value, onChange, ariaLabel, variant = 'light' }) {
  return (
    <div
      className={`gd-dash-seg${variant === 'dark' ? ' gd-dash-seg--dark' : ''}`}
      role="group"
      aria-label={ariaLabel}
    >
      {options.map((o) => (
        <button
          key={o.key}
          type="button"
          className={o.key === value ? 'gd-dash-seg__btn is-on' : 'gd-dash-seg__btn'}
          aria-pressed={o.key === value}
          onClick={() => onChange(o.key)}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
