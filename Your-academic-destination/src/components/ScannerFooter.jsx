import React from 'react';

const ScannerFooter = ({ count, countLabel, isConnected = true }) => {
  return (
    <footer className="scanner-footer">
      <span>{count} {countLabel}</span>
      <span className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
        {isConnected ? 'متصل' : 'غير متصل'}
      </span>
    </footer>
  );
};

export default ScannerFooter;