import { useCallback, useState } from 'react';
import * as ROSLIB from 'roslib';

export type MissionState = 'idle' | 'validating' | 'running' | 'success' | 'error';

interface MissionStatus {
  state: MissionState;
  currentMission: string | null;
  message: string | null;
}

interface StartMissionResponse {
  accepted: boolean;
  message: string;
  stations_liste: string[];
}

interface ExecuteMissionFeedback {
  station_courante: string;
  station_index: number;
  station_total: number;
  statut: string;
  progression: number;
}

interface ExecuteMissionResult {
  success: boolean;
  message: string;
  stations_visitees: number;
}

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
        addStatusMessage('[ERREUR] Non connecté à ROS 2 — impossible de lancer la mission.');
        return;
      }

      setStatus({ state: 'validating', currentMission: missionName, message: null });
      addStatusMessage(`[...] Validation de la mission "${missionName}"...`);

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
        (serviceResponse: unknown) => {
          const response = serviceResponse as StartMissionResponse;

          if (!response.accepted) {
            setStatus({
              state: 'error',
              currentMission: missionName,
              message: response.message,
            });
            addStatusMessage(`[ERREUR] Mission refusée : ${response.message}`);
            return;
          }

          addStatusMessage(
            `[OK] Mission "${missionName}" validée — ${response.stations_liste.length} station(s)`,
          );

          setStatus({ state: 'running', currentMission: missionName, message: null });
          addStatusMessage(`[INFO] Démarrage de la navigation pour "${missionName}"...`);

          const executeMissionAction = new ROSLIB.Action<
            { mission_name: string },
            ExecuteMissionFeedback,
            ExecuteMissionResult
          >({
            ros,
            name: '/mission_manager/execute_mission',
            actionType: 'industry_robot_mission/ExecuteMission',
          });

          executeMissionAction.sendGoal(
            {
              mission_name: missionName,
            },
            (result) => {
              if (result.success) {
                setStatus({
                  state: 'success',
                  currentMission: missionName,
                  message: result.message,
                });
                addStatusMessage(`[OK] ${result.message}`);
              } else {
                setStatus({
                  state: 'error',
                  currentMission: missionName,
                  message: result.message,
                });
                addStatusMessage(`[ERREUR] ${result.message}`);
              }

              setTimeout(() => {
                setStatus((prev) =>
                  prev.currentMission === missionName
                    ? { state: 'idle', currentMission: null, message: null }
                    : prev,
                );
              }, 5000);
            },
            (feedback) => {
              const pct = Math.round(feedback.progression * 100);
              addStatusMessage(
                `[INFO] [${feedback.statut}] ${feedback.station_courante} (${feedback.station_index + 1}/${feedback.station_total}) — ${pct}%`,
              );
            },
            (error) => {
              setStatus({
                state: 'error',
                currentMission: missionName,
                message: `Action inaccessible : ${error}`,
              });
              addStatusMessage(`[ERREUR] Erreur action : ${error}`);

              setTimeout(() => {
                setStatus({ state: 'idle', currentMission: null, message: null });
              }, 5000);
            },
          );
        },
        (error: unknown) => {
          setStatus({
            state: 'error',
            currentMission: missionName,
            message: `Service inaccessible : ${error}`,
          });
          addStatusMessage(`[ERREUR] Erreur service : ${error}`);

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
