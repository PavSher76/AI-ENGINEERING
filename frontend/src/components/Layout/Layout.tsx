import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import Header from './Header.tsx';
import Sidebar from './Sidebar.tsx';
import './Layout.css';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <div className="layout">
      <Header onMenuClick={toggleSidebar} />
      <div className="layout-content">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} currentPath={location.pathname} />
        <main className={`main-content ${sidebarOpen ? 'sidebar-open' : ''}`}>
          <div className="content-wrapper">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;