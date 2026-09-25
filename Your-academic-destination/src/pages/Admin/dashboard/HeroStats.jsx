import { Link } from 'react-router-dom';
import DayFilter from './DayFilter';

const DASH = '—';

export default function HeroStats({ studentsInsideToday, studentsInsideCount, stats, day, onDayChange }) {
  return (
    <section className="gd-dash-hero">
      <div className="gd-dash-hero__now">
        <div className="gd-dash-hero__lbl">
          <i className="gd-dash-hero__live" aria-hidden="true" />
          داخل الحرم اليوم
        </div>
        <div className="gd-dash-hero__big">{studentsInsideToday == null ? DASH : studentsInsideToday}</div>
        <div className="gd-dash-hero__sub">
          عدد الطلاب اللي دخلوا من البوابة <b>اليوم</b> فقط
        </div>
      </div>

      <div className="gd-dash-trio">
        <Link className="gd-dash-trio__item" to="/gate-registered">
          <span className="gd-dash-trio__l">مسجّلون إلكترونياً</span>
          <span className="gd-dash-trio__n">{stats?.registered_online_count == null ? DASH : stats.registered_online_count}</span>
          <span className="gd-dash-trio__go">عرض القائمة</span>
        </Link>

        <Link to="/dashboard-students-inside" className="gd-dash-trio__item is-anchor">
          <span className="gd-dash-trio__l">إجمالي الطلاب داخل الجامعة</span>
          <span className="gd-dash-trio__chips" onClick={(e) => e.stopPropagation()}>
            <DayFilter variant="dark" value={day} onChange={onDayChange} />
          </span>
          <span className="gd-dash-trio__n">{studentsInsideCount == null ? DASH : studentsInsideCount}</span>
          <span className="gd-dash-trio__go">عرض القائمة</span>
        </Link>

        <Link className="gd-dash-trio__item" to="/dashboard-survey-completions">
          <span className="gd-dash-trio__l">أكملوا الاستبيان</span>
          <span className="gd-dash-trio__n">{stats?.survey_completed_count == null ? DASH : stats.survey_completed_count}</span>
          <span className="gd-dash-trio__go">عرض القائمة</span>
        </Link>
      </div>
    </section>
  );
}