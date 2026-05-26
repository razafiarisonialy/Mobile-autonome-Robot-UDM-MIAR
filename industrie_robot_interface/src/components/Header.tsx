import React from 'react';

interface HeaderProps {
  connected: boolean;
}

export const Header: React.FC<HeaderProps> = ({ connected }) => {
  return (
    <header className="app-header">
      <div className="header-logo-title">
        <div className="udm-badge">UDM</div>
        <h1 className="header-title">AMR Mission Control</h1>
      </div>
      <div className="connection-status">
        <span className={`status-dot ${connected ? 'connected' : 'disconnected'}`}></span>
        <span className="status-text">
          {connected ? 'ROS 2 Connecté' : 'ROS 2 Déconnecté'}
        </span>
      </div>
    </header>
  );
};
