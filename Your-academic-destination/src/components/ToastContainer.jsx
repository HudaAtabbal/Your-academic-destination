import React, { useState, useEffect } from 'react';
import { subscribeToasts } from '../api/toast';
import '../style/Toast.css';

const ToastContainer = () => {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    const unsubscribe = subscribeToasts(setToasts);
    return unsubscribe;
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div key={t.id} className={`toast-item toast-${t.type}`}>
          {t.message}
        </div>
      ))}
    </div>
  );
};

export default ToastContainer;