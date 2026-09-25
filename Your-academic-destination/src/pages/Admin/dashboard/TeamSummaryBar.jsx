import { Link } from 'react-router-dom';

const DASH = '—';

export default function TeamSummaryBar({ total }) {
  return (
    <section className="gd-dash-card gd-dash-team">
      <div className="gd-dash-team__info">
        <h2>حسابات فريق العمل</h2>
        <p>{total == null ? DASH : `${total} حساب`}</p>
      </div>
      <div className="gd-dash-team__btns">
        <Link to="/team-accounts" className="gd-dash-btn gd-dash-btn--ghost">
          إدارة الحسابات
        </Link>
        <Link to="/create-team-account" className="gd-dash-btn">
          + إنشاء حساب جديد
        </Link>
      </div>
    </section>
  );
}