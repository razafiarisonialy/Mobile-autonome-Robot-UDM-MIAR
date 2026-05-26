import React from 'react';
import { STATIONS } from '../data/missions';
import type { Mission } from '../data/missions';
import type { MissionState } from '../hooks/useMission';

interface MissionCardProps {
  mission: Mission;
  isActive: boolean;
  currentState: MissionState;
  onExecute: (id: string) => void;
  disabled: boolean;
}

export const MissionCard: React.FC<MissionCardProps> = ({
  mission,
  isActive,
  currentState,
  onExecute,
  disabled,
}) => {
  const getButtonText = () => {
    if (!isActive) return 'Lancer la mission';
    switch (currentState) {
      case 'validating':
        return 'Validation...';
      case 'running':
        return 'En cours...';
      case 'success':
        return '✓ Terminé';
      case 'error':
        return '✗ Échec';
      default:
        return 'Lancer la mission';
    }
  };

  const getStatusClass = () => {
    if (!isActive) return '';
    return `card-${currentState}`;
  };

  return (
    <div className={`mission-card ${getStatusClass()}`} style={{ '--accent-color': mission.color } as React.CSSProperties}>
      <div className="card-header">
        <span className="mission-icon">{mission.icon}</span>
        <h3 className="mission-name">{mission.name}</h3>
      </div>
      
      <p className="mission-description">{mission.description}</p>
      
      <div className="stations-flow">
        <h4 className="flow-title">Itinéraire</h4>
        <div className="stations-list">
          {mission.stations.map((stationId, index) => {
            const station = STATIONS[stationId];
            return (
              <React.Fragment key={`${stationId}-${index}`}>
                <div className="station-badge" title={station?.description || stationId}>
                  {station?.label || stationId}
                </div>
                {index < mission.stations.length - 1 && (
                  <span className="flow-arrow">→</span>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
      
      <button
        type="button"
        className={`btn-execute ${isActive ? 'active' : ''}`}
        onClick={() => onExecute(mission.id)}
        disabled={disabled && !isActive}
      >
        {isActive && currentState === 'running' && (
          <span className="spinner"></span>
        )}
        {getButtonText()}
      </button>
    </div>
  );
};
