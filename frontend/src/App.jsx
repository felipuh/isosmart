import React from 'react';
import Header from './components/Layout/Header';
import ExecutiveDashboard from './components/Dashboard/ExecutiveDashboard';

function App() {
  return (
    <div className="min-h-screen">
      <Header />
      <ExecutiveDashboard />
    </div>
  );
}

export default App;
