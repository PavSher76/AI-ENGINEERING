import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import Chat from './pages/Chat/Chat';
import Consultation from './pages/Consultation/Consultation';
import Archive from './pages/Archive/Archive';
import Calculations from './pages/Calculations/Calculations';
import Validation from './pages/Validation/Validation';
import Documents from './pages/Documents/Documents';
import Analytics from './pages/Analytics/Analytics';
import Integration from './pages/Integration/Integration';
import OutgoingControl from './pages/OutgoingControl/OutgoingControl';
import QRValidation from './pages/QRValidation/QRValidation';
import Settings from './pages/Settings/Settings';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/consultation" element={<Consultation />} />
            <Route path="/archive" element={<Archive />} />
            <Route path="/calculations" element={<Calculations />} />
            <Route path="/validation" element={<Validation />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/integration" element={<Integration />} />
            <Route path="/outgoing-control" element={<OutgoingControl />} />
            <Route path="/qr-validation" element={<QRValidation />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
      </div>
    </Router>
  );
}

export default App;