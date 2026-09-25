import { EVENT_DAYS } from '../../../api/eventDays';

export default function DayFilter({ value, onChange, variant = 'light' }) {
  return (
    <div
      className={`gd-dash-dayfilter${variant === 'dark' ? ' gd-dash-dayfilter--dark' : ''}`}
      role="group"
      aria-label="فلترة حسب اليوم"
    >
      {EVENT_DAYS.map((d) => (
        <button
          key={d.key}
          type="button"
          className={d.key === value ? 'gd-dash-dayfilter__btn is-on' : 'gd-dash-dayfilter__btn'}
          aria-pressed={d.key === value}
          onClick={() => onChange(d.key)}
        >
          {d.label}
        </button>
      ))}
    </div>
  );
}