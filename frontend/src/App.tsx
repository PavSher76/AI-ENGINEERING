import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout.tsx';
import Dashboard from './pages/Dashboard/Dashboard.tsx';
import Chat from './pages/Chat/Chat.tsx';
import Consultation from './pages/Consultation/Consultation.tsx';
import Archive from './pages/Archive/Archive.tsx';
import Calculations from './pages/Calculations/Calculations.tsx';
import Validation from './pages/Validation/Validation.tsx';
import Documents from './pages/Documents/Documents.tsx';
import Analytics from './pages/Analytics/Analytics.tsx';
import Integration from './pages/Integration/Integration.tsx';
import OutgoingControl from './pages/OutgoingControl/OutgoingControl.tsx';
import QRValidation from './pages/QRValidation/QRValidation.tsx';
import Settings from './pages/Settings/Settings.tsx';
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