import { useROS } from './hooks/useROS';
import { useMission } from './hooks/useMission';
import { MISSIONS } from './data/missions';
import { Header } from './components/Header';
import { MissionCard } from './components/MissionCard';
import { StatusPanel } from './components/StatusPanel';
import './App.css';

function App() {
  const { ros, connected, statusMessages, addStatusMessage, clearMessages } = useROS();
  const { state, currentMission, executeMission } = useMission(ros, connected, addStatusMessage);

  return (
    <div className="app-container">
      <Header connected={connected} />

      <main className="dashboard-grid">
        <section className="missions-section">
          <div>
            <h2 className="section-title">Missions Logistiques</h2>
            <p className="section-subtitle">
              Sélectionnez une mission pour orchestrer le robot autonome AMR Husky A300
            </p>
          </div>

          <div className="cards-grid">
            {MISSIONS.map((mission) => {
              const isActive = currentMission === mission.id;
              return (
                <MissionCard
                  key={mission.id}
                  mission={mission}
                  isActive={isActive}
                  currentState={state}
                  onExecute={executeMission}
                  disabled={!connected || (currentMission !== null && !isActive)}
                />
              );
            })}
          </div>
        </section>

        <section className="terminal-section">
          <StatusPanel messages={statusMessages} onClear={clearMessages} />
        </section>
      </main>

      <footer className="app-footer">
        <p>
          Département IAR — Projet Robotique Mobile Autonome UDM. Communication via{' '}
          <code>rosbridge_websocket</code>.
        </p>
      </footer>
    </div>
  );
}

export default App;
