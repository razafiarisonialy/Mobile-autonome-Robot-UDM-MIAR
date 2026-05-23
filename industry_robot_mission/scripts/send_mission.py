#!/usr/bin/env python3
"""Outil CLI pour déclencher ou lister les missions logistiques AMR."""

import argparse
import os
import sys

import rclpy
import yaml
from rclpy.node import Node

from industry_robot_mission.srv import StartMission


class ClientMission(Node):
    """Nœud ROS 2 client du service mission_manager/start_mission."""

    def __init__(self):
        """Initialise le client de service."""
        super().__init__('send_mission_cli')
        self._client = self.create_client(StartMission, '/mission_manager/start_mission')

    def envoyer_mission(self, nom_mission: str) -> bool:
        """
        Envoie une requête de démarrage de mission et affiche le résultat.

        Retourne True si la mission est acceptée, False sinon.
        """
        self.get_logger().info(
            f'Connexion au service /mission_manager/start_mission (timeout 5s)...'
        )
        if not self._client.wait_for_service(timeout_sec=5.0):
            print(
                '\nErreur : service /mission_manager/start_mission inaccessible.\n'
                'Vérifiez que mission_manager est lancé :\n'
                '  ros2 launch industry_robot_mission mission.launch.py',
                file=sys.stderr,
            )
            return False

        requete = StartMission.Request()
        requete.mission_name = nom_mission

        future = self._client.call_async(requete)
        rclpy.spin_until_future_complete(self, future, timeout_sec=10.0)

        if future.result() is None:
            print(
                '\nErreur : pas de réponse du service (timeout 10s).',
                file=sys.stderr,
            )
            return False

        reponse = future.result()

        if reponse.accepted:
            print(f'\nMission "{nom_mission}" acceptée.')
            print(f'Message : {reponse.message}')
            print(f'\nStations à visiter ({len(reponse.stations_liste)}) :')
            for i, station in enumerate(reponse.stations_liste, start=1):
                print(f'  {i:2d}. {station}')
            print()
        else:
            print(f'\nMission refusée : {reponse.message}', file=sys.stderr)
            return False

        return True


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
        print('  ros2 run industry_robot_mission send_mission --name <nom_mission>')

    except Exception as e:
        print(
            f'\nImpossible de lire le fichier missions.yaml : {e}\n'
            'Utilisez --name <nom_mission> pour déclencher une mission.',
            file=sys.stderr,
        )


def main():
    """Point d'entrée CLI — liste les missions ou déclenche celle demandée."""
    parser = argparse.ArgumentParser(
        description='Outil CLI de déclenchement des missions logistiques AMR.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'Exemples :\n'
            '  ros2 run industry_robot_mission send_mission\n'
            '  ros2 run industry_robot_mission send_mission --name approvisionnement\n'
            '  ros2 run industry_robot_mission send_mission --name retour_base\n'
        ),
    )
    parser.add_argument(
        '--name',
        type=str,
        default=None,
        metavar='NOM_MISSION',
        help='Nom de la mission à déclencher',
    )
    args = parser.parse_args()

    if args.name is None:
        lister_missions_disponibles()
        return

    rclpy.init()
    noeud = ClientMission()

    try:
        succes = noeud.envoyer_mission(args.name)
        sys.exit(0 if succes else 1)
    except KeyboardInterrupt:
        pass
    finally:
        noeud.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
