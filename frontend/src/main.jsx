import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error('[ErrorBoundary] Uncaught render error:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#03030a', color: '#06b6d4', fontFamily: 'sans-serif', flexDirection: 'column', gap: '1rem' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>⚡ Grid Connection Lost</h2>
          <p style={{ color: '#94a3b8' }}>An unexpected error occurred. Please refresh the page.</p>
          <button onClick={() => window.location.reload()} style={{ padding: '0.5rem 1.5rem', background: '#06b6d4', color: '#000', borderRadius: '0.5rem', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}>
            Refresh
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);
