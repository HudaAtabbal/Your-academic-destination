import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

// خريطة كل تاب على المسار المطابق له
const TAB_ROUTES = {
  card: '/my-card',
  guide: '/academic-guide',
  map: '/map',       // TODO: بدّليه إذا المسار الفعلي مختلف
  survey: '/survey', // TODO: بدّليه إذا المسار الفعلي مختلف
};

const BottomNav = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    {
      id: 'card',
      label: 'بطاقاتي',
      icon: (
        <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="4" width="18" height="16" rx="3" />
        </svg>
      ),
    },
    {
      id: 'guide',
      label: 'الدليل',
      icon: (
        <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="4" y="4" width="16" height="16" rx="2" />
          <line x1="8" y1="8" x2="16" y2="8" />
          <line x1="8" y1="12" x2="16" y2="12" />
          <line x1="8" y1="16" x2="12" y2="16" />
        </svg>
      ),
    },
    {
      id: 'map',
      label: 'الخريطة',
      icon: (
        <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polygon points="12 2 2 7 12 12 22 7 12 2" />
          <polyline points="2 17 12 22 22 17" />
          <polyline points="2 12 12 17 22 12" />
        </svg>
      ),
    },
    {
      id: 'survey',
      label: 'الاستبيان',
      icon: (
        <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
        </svg>
      ),
    },
  ];

  // بنحدد التاب النشط اعتماداً على المسار الحالي بالـ URL، مش state محلي
  const activeTab = Object.keys(TAB_ROUTES).find(
    (id) => TAB_ROUTES[id] === location.pathname
  );

  const handleNavClick = (id) => {
    const route = TAB_ROUTES[id];
    if (route) {
      navigate(route);
    }
  };

  return (
    <nav className="bottom-nav">
      {navItems.map((item) => (
        <button
          key={item.id}
          className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
          onClick={() => handleNavClick(item.id)}
        >
          {item.icon}
          <span>{item.label}</span>
        </button>
      ))}
    </nav>
  );
};

export default BottomNav;