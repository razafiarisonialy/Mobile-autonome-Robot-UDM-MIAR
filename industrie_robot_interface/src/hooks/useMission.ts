import { useCallback, useState } from 'react';
import * as ROSLIB from 'roslib';

export type MissionState = 'idle' | 'validating' | 'running' | 'success' | 'error';

interface MissionStatus {
  state: MissionState;
  currentMission: string | null;
  message: string | null;
}

/**
 * Hook React pour déclencher les missions via rosbridge.
 *
 * 1. Appelle le service /mission_manager/start_mission pour valider
 * 2. Envoie le goal action /mission_manager/execute_mission pour exécuter
 */
export function useMission(
  ros: ROSLIB.Ros | null,
  connected: boolean,
  addStatusMessage: (text: string) => void,
) {
  const [status, setStatus] = useState<MissionStatus>({
    state: 'idle',
    currentMission: null,
    message: null,
  });

  const executeMission = useCallback(
    (missionName: string) => {
      if (!ros || !connected) {
        addStatusMessage('❌ Non connecté à ROS 2 — impossible de lancer la mission.');
        return;
      }

      // Étape 1 : Validation via le service
      setStatus({ state: 'validating', currentMission: missionName, message: null });
      addStatusMessage(`⏳ Validation de la mission "${missionName}"...`);

      const startService = new ROSLIB.Service({
        ros,
        name: '/mission_manager/start_mission',
        serviceType: 'industry_robot_mission/srv/StartMission',
      });

      const request = {
        mission_name: missionName,
      };

      startService.callService(
        request,
        (response: any) => {
          if (!response.accepted) {
            setStatus({
              state: 'error',
              currentMission: missionName,
              message: response.message,
            });
            addStatusMessage(`❌ Mission refusée : ${response.message}`);
            return;
          }

          addStatusMessage(
            `✅ Mission "${missionName}" validée — ${response.stations_liste.length} station(s)`,
          );

          // Étape 2 : Exécution via l'action
          setStatus({ state: 'running', currentMission: missionName, message: null });
          addStatusMessage(`🚀 Démarrage de la navigation pour "${missionName}"...`);

          const actionClient = new ROSLIB.ActionClient({
            ros,
            serverName: '/mission_manager/execute_mission',
            actionName: 'industry_robot_mission/action/ExecuteMission',
          });

          const goal = new ROSLIB.Goal({
            actionClient,
            goalMessage: {
              mission_name: missionName,
            },
          });

          goal.on('feedback', (feedback: any) => {
            const pct = Math.round(feedback.progression * 100);
            addStatusMessage(
              `📍 [${feedback.statut}] ${feedback.station_courante} (${feedback.station_index + 1}/${feedback.station_total}) — ${pct}%`,
            );
          });

          goal.on('result', (result: any) => {
            if (result.success) {
              setStatus({
                state: 'success',
                currentMission: missionName,
                message: result.message,
              });
              addStatusMessage(`✅ ${result.message}`);
            } else {
              setStatus({
                state: 'error',
                currentMission: missionName,
                message: result.message,
              });
              addStatusMessage(`❌ ${result.message}`);
            }

            // Remettre à idle après 5 secondes
            setTimeout(() => {
              setStatus((prev) =>
                prev.currentMission === missionName
                  ? { state: 'idle', currentMission: null, message: null }
                  : prev,
              );
            }, 5000);
          });

          goal.send();
        },
        (error: any) => {
          setStatus({
            state: 'error',
            currentMission: missionName,
            message: `Service inaccessible : ${error}`,
          });
          addStatusMessage(`❌ Erreur service : ${error}`);

          setTimeout(() => {
            setStatus({ state: 'idle', currentMission: null, message: null });
          }, 5000);
        },
      );
    },
    [ros, connected, addStatusMessage],
  );

  return {
    ...status,
    executeMission,
  };
}
