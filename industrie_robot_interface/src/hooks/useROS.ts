import { useCallback, useEffect, useRef, useState } from 'react';
import * as ROSLIB from 'roslib';

const ROSBRIDGE_URL = `ws://${window.location.hostname}:9090`;
const RECONNECT_DELAY_MS = 3000;

export interface StatusMessage {
  id: number;
  text: string;
  timestamp: Date;
}

let messageIdCounter = 0;

/**
 * Hook React pour gérer la connexion WebSocket à rosbridge_server.
 *
 * - Se connecte automatiquement à ws://localhost:9090
 * - Gère la reconnexion automatique
 * - Subscribe au topic /mission_status
 */
export function useROS() {
  const [connected, setConnected] = useState(false);
  const [statusMessages, setStatusMessages] = useState<StatusMessage[]>([]);
  const rosRef = useRef<ROSLIB.Ros | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const addStatusMessage = useCallback((text: string) => {
    const msg: StatusMessage = {
      id: ++messageIdCounter,
      text,
      timestamp: new Date(),
    };
    setStatusMessages((prev) => [...prev.slice(-99), msg]);
  }, []);

  const connect = useCallback(() => {
    // Nettoyer l'ancienne connexion
    if (rosRef.current) {
      try {
        rosRef.current.close();
      } catch {
        // ignore
      }
    }

    const ros = new ROSLIB.Ros({});

    ros.on('connection', () => {
      setConnected(true);
      addStatusMessage('[OK] Connecté à rosbridge_server');

      // Subscribe au topic /mission_status
      const statusTopic = new ROSLIB.Topic({
        ros,
        name: '/mission_status',
        messageType: 'std_msgs/msg/String',
      });

      statusTopic.subscribe((message: any) => {
        addStatusMessage(message?.data || '');
      });
    });

    ros.on('error', () => {
      setConnected(false);
    });

    ros.on('close', () => {
      setConnected(false);
      addStatusMessage('[ERREUR] Connexion perdue — reconnexion...');

      // Reconnexion automatique
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      reconnectTimerRef.current = setTimeout(() => {
        connect();
      }, RECONNECT_DELAY_MS);
    });

    try {
      ros.connect(ROSBRIDGE_URL);
    } catch {
      // La reconnexion sera gérée par l'event 'close'
    }

    rosRef.current = ros;
  }, [addStatusMessage]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      if (rosRef.current) {
        try {
          rosRef.current.close();
        } catch {
          // ignore
        }
      }
    };
  }, [connect]);

  const clearMessages = useCallback(() => {
    setStatusMessages([]);
  }, []);

  return {
    ros: rosRef.current,
    connected,
    statusMessages,
    addStatusMessage,
    clearMessages,
  };
}
