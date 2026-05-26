import React, { useEffect, useRef } from 'react';
import type { StatusMessage } from '../hooks/useROS';

interface StatusPanelProps {
  messages: StatusMessage[];
  onClear: () => void;
}

export const StatusPanel: React.FC<StatusPanelProps> = ({ messages, onClear }) => {
  const terminalEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const getMessageClass = (text: string) => {
    if (text.includes('✅') || text.includes('MISSION_TERMINEE') || text.includes('✓')) {
      return 'log-success';
    }
    if (text.includes('❌') || text.includes('🔴') || text.includes('MISSION_ECHEC') || text.includes('✗')) {
      return 'log-error';
    }
    if (text.includes('⏳') || text.includes('REPRISE') || text.includes('EN_ROUTE') || text.includes('⏳')) {
      return 'log-info';
    }
    return 'log-default';
  };

  return (
    <div className="status-panel">
      <div className="panel-header">
        <h3 className="panel-title">📡 Terminal de Suivi des Missions</h3>
        <button type="button" className="btn-clear" onClick={onClear}>
          Effacer les logs
        </button>
      </div>
      <div className="terminal-body">
        {messages.length === 0 ? (
          <div className="terminal-empty">Aucune activité enregistrée. En attente de connexion...</div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`terminal-line ${getMessageClass(msg.text)}`}>
              <span className="log-time">
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </span>
              <span className="log-text">{msg.text}</span>
            </div>
          ))
        )}
        <div ref={terminalEndRef} />
      </div>
    </div>
  );
};
