import { EVENT_DAYS } from '../../../api/eventDays';
import SegmentedControl from './SegmentedControl';

export default function DayFilter({ value, onChange, variant = 'light' }) {
  return (
    <SegmentedControl
      options={EVENT_DAYS}
      value={value}
      onChange={onChange}
      variant={variant}
      ariaLabel="فلترة حسب اليوم"
    />
  );
}
