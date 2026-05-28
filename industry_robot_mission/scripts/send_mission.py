#!/usr/bin/env python3
"""Outil CLI pour déclencher et suivre une mission logistique AMR."""

import argparse
import os
import sys

import rclpy
import yaml
from rclpy.action import ActionClient
from rclpy.node import Node

from industry_robot_mission.action import ExecuteMission
from industry_robot_mission.srv import StartMission

# Timeout CLI pour attendre le résultat de la navigation (secondes)
TIMEOUT_NAVIGATION_SEC = 900.0  # 15 minutes — couvre les missions les plus longues


class ClientMission(Node):
    """Nœud ROS 2 client : valide la mission via le service, puis l'exécute via l'action."""

    def __init__(self):
        """Initialise les clients service et action."""
        super().__init__('send_mission_cli')
        self._client_service = self.create_client(
            StartMission, '/mission_manager/start_mission'
        )
        self._client_action = ActionClient(
            self, ExecuteMission, '/mission_manager/execute_mission'
        )

    def valider_mission(self, nom_mission: str) -> bool:
        """
        Appelle le service start_mission pour valider et afficher la liste des stations.

        Retourne True si la mission est acceptée.
        """
        if not self._client_service.wait_for_service(timeout_sec=5.0):
            print(
                '\nErreur : service /mission_manager/start_mission inaccessible.\n'
                'Vérifiez que mission_manager est lancé :\n'
                '  ros2 launch industry_robot_mission mission.launch.py',
                file=sys.stderr,
            )
            return False

        requete = StartMission.Request()
        requete.mission_name = nom_mission

        future = self._client_service.call_async(requete)
        rclpy.spin_until_future_complete(self, future, timeout_sec=10.0)

        if future.result() is None:
            print('\nErreur : pas de réponse du service (timeout 10s).', file=sys.stderr)
            return False

        reponse = future.result()
        if not reponse.accepted:
            print(f'\nMission refusée : {reponse.message}', file=sys.stderr)
            return False

        print(f'\nMission "{nom_mission}" validée.')
        print(f'Message  : {reponse.message}')
        print(f'\nStations à visiter ({len(reponse.stations_liste)}) :')
        for i, station in enumerate(reponse.stations_liste, start=1):
            print(f'  {i:2d}. {station}')
        print()
        return True

    def executer_mission(self, nom_mission: str) -> bool:
        """
        Envoie le goal execute_mission et affiche la progression en temps réel.

        Retourne True si la mission se termine avec succès.
        """
        if not self._client_action.wait_for_server(timeout_sec=10.0):
            print(
                '\nErreur : action /mission_manager/execute_mission inaccessible.',
                file=sys.stderr,
            )
            return False

        goal = ExecuteMission.Goal()
        goal.mission_name = nom_mission

        print(f'Démarrage de la navigation pour "{nom_mission}"...\n')

        send_future = self._client_action.send_goal_async(
            goal, feedback_callback=self._cb_feedback
        )
        rclpy.spin_until_future_complete(self, send_future, timeout_sec=30.0)

        if not send_future.done() or send_future.result() is None:
            print('\nErreur : pas de réponse du serveur d\'action (timeout 30s).', file=sys.stderr)
            return False

        goal_handle = send_future.result()
        if not goal_handle.accepted:
            print('\nErreur : goal refusé par mission_manager.', file=sys.stderr)
            return False

        print('Goal accepté — navigation en cours...\n')

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(
            self, result_future, timeout_sec=TIMEOUT_NAVIGATION_SEC
        )

        if not result_future.done() or result_future.result() is None:
            print(
                f'\nErreur : pas de résultat après {TIMEOUT_NAVIGATION_SEC:.0f}s — '
                'Nav2 peut être bloqué.',
                file=sys.stderr,
            )
            return False

        result_response = result_future.result()
        resultat = result_response.result

        if resultat.success:
            print(f'\n✓ Mission terminée avec succès.')
            print(f'  Stations visitées : {resultat.stations_visitees}')
            print(f'  Message           : {resultat.message}')
        else:
            print(f'\n✗ Mission échouée.', file=sys.stderr)
            print(f'  Stations visitées : {resultat.stations_visitees}', file=sys.stderr)
            print(f'  Message           : {resultat.message}', file=sys.stderr)

        return resultat.success

    def _cb_feedback(self, feedback_msg):
        """Affiche la progression en temps réel pendant la navigation."""
        fb = feedback_msg.feedback
        pct = int(fb.progression * 100)
        # station_index = index courant (0-based), on affiche l'index suivant pour indiquer la cible
        print(
            f'  [{fb.statut:15s}] {fb.station_courante} '
            f'({fb.station_index + 1}/{fb.station_total}) — {pct}%'
        )


def lister_missions_disponibles():
    """Affiche les missions disponibles en lisant le YAML du package."""
    try:
        from ament_index_python.packages import get_package_share_directory
        pkg_dir = get_package_share_directory('industry_robot_mission')
        fichier = os.path.join(pkg_dir, 'config', 'missions.yaml')
        with open(fichier, 'r') as f:
            donnees = yaml.safe_load(f)
        missions = donnees.get('missions', {})

        print('\nMissions disponibles :')
        print('=' * 50)
        for nom, info in missions.items():
            desc = info.get('description', '')
            stations = info.get('stations', [])
            print(f'  {nom}')
            print(f'    Description : {desc}')
            print(f'    Stations    : {" → ".join(stations)}')
            print()

        print('Utilisation :')
        print('  ros2 run industry_robot_mission send_mission.py --name <nom_mission>')

    except Exception as e:
        print(
            f'\nImpossible de lire le fichier missions.yaml : {e}',
            file=sys.stderr,
        )


def main():
    """Point d'entrée CLI — liste les missions ou déclenche celle demandée."""
    parser = argparse.ArgumentParser(
        description='Outil CLI de déclenchement des missions logistiques AMR.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'Exemples :\n'
            '  ros2 run industry_robot_mission send_mission.py\n'
            '  ros2 run industry_robot_mission send_mission.py --name approvisionnement\n'
            '  ros2 run industry_robot_mission send_mission.py --name retour_base\n'
        ),
    )
    parser.add_argument(
        '--name',
        type=str,
        default=None,
        metavar='NOM_MISSION',
        help='Nom de la mission à déclencher et exécuter',
    )
    args = parser.parse_args()

    if args.name is None:
        lister_missions_disponibles()
        return

    rclpy.init()
    noeud = ClientMission()

    try:
        # Étape 1 : validation via le service (affiche les stations)
        if not noeud.valider_mission(args.name):
            sys.exit(1)

        # Étape 2 : exécution via l'action (déclenche la navigation)
        succes = noeud.executer_mission(args.name)
        sys.exit(0 if succes else 1)

    except KeyboardInterrupt:
        print('\nInterruption clavier — mission annulée.')
        sys.exit(1)
    finally:
        noeud.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
