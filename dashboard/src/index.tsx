import React from 'react';
import ReactDOM from 'react-dom/client';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <div style={{ padding: '2rem', fontFamily: 'sans-serif', color: '#f8fafc', backgroundColor: '#0f172a', minHeight: '100vh' }}>
      <h1>FinGraph — Real-Time Fraud Syndicate Analytics</h1>
      <p>Analyst Dashboard initialized.</p>
    </div>
  </React.StrictMode>
);
