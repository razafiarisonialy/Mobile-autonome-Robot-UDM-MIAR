#!/usr/bin/env python3
"""
Outil de calibration des coordonnées de stations.

Utilisation :
  1. Lancer Nav2 : ros2 launch industry_robot_navigation nav.launch.py
  2. Lancer ce script : ros2 run industry_robot_mission calibrate_stations.py
  3. Dans RViz, utiliser l'outil "Nav2 Goal" (flèche verte)
     → Clic + glisser pour définir position ET orientation
  4. Entrer le nom de la station dans le terminal
  5. Les coordonnées YAML s'affichent à copier dans stations.yaml
"""

import math
import sys

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node


AIDE = """
╔══════════════════════════════════════════════════════════════╗
║         CALIBRATION DES STATIONS — industry_robot_mission    ║
╠══════════════════════════════════════════════════════════════╣
║  1. Dans RViz, sélectionner l'outil "Nav2 Goal" (flèche ▶)  ║
║  2. Cliquer + GLISSER sur la carte pour poser la station     ║
║     (le glisser définit l'orientation du robot à l'arrivée) ║
║  3. Entrer le nom de la station dans ce terminal             ║
║  4. Répéter pour chaque station                              ║
║                                                              ║
║  Ctrl+C pour terminer et afficher le YAML complet            ║
╚══════════════════════════════════════════════════════════════╝
"""


class CapteurPoses(Node):
    """Nœud ROS 2 qui écoute /goal_pose et convertit en format YAML stations."""

    def __init__(self):
        """Initialise le subscriber sur /goal_pose."""
        super().__init__('calibrate_stations')
        self._stations_calibrees: dict = {}
        self._derniere_pose: PoseStamped | None = None

        self._sub = self.create_subscription(
            PoseStamped,
            '/goal_pose',
            self._cb_goal_pose,
            10,
        )
        print(AIDE)
        print('En attente d\'un clic "Nav2 Goal" dans RViz...\n')

    def _cb_goal_pose(self, msg: PoseStamped):
        """Reçoit une pose depuis RViz et demande le nom de la station."""
        x = msg.pose.position.x
        y = msg.pose.position.y
        yaw = self._quaternion_vers_yaw(
            msg.pose.orientation.z,
            msg.pose.orientation.w,
        )

        print(f'\n📍 Pose reçue depuis RViz :')
        print(f'   x   = {x:.3f} m')
        print(f'   y   = {y:.3f} m')
        print(f'   yaw = {yaw:.4f} rad  ({math.degrees(yaw):.1f}°)')
        print()

        nom = self._demander_nom_station(x, y, yaw)
        if nom:
            self._stations_calibrees[nom] = {
                'x': round(x, 3),
                'y': round(y, 3),
                'yaw': round(yaw, 4),
            }
            print(f'\n✓ Station "{nom}" enregistrée.')
            print(f'  Total calibré : {len(self._stations_calibrees)} station(s)\n')
            print('En attente du prochain clic "Nav2 Goal" dans RViz...\n')

    def _demander_nom_station(self, x: float, y: float, yaw: float) -> str:
        """Invite l'utilisateur à nommer la station."""
        noms_connus = [
            'base_charge',
            'matieres_premieres',
            'poste_decoupe',
            'controle_qualite',
            'expedition',
        ]
        print('Noms de stations disponibles :')
        for i, nom in enumerate(noms_connus, start=1):
            statut = '✓' if nom in self._stations_calibrees else ' '
            print(f'  [{statut}] {i}. {nom}')
        print(f'       c. Nom personnalisé')
        print(f'       s. Ignorer cette pose\n')

        try:
            choix = input('Votre choix (numéro, "c" ou "s") : ').strip()
        except (EOFError, KeyboardInterrupt):
            return ''

        if choix == 's':
            print('Pose ignorée.')
            return ''
        elif choix == 'c':
            try:
                nom = input('Nom de la station : ').strip()
            except (EOFError, KeyboardInterrupt):
                return ''
            return nom if nom else ''
        elif choix.isdigit() and 1 <= int(choix) <= len(noms_connus):
            return noms_connus[int(choix) - 1]
        else:
            print('Choix invalide — pose ignorée.')
            return ''

    @staticmethod
    def _quaternion_vers_yaw(qz: float, qw: float) -> float:
        """Calcule le yaw depuis les composantes z et w du quaternion (qx=qy=0)."""
        return 2.0 * math.atan2(qz, qw)

    def afficher_yaml_final(self):
        """Affiche le contenu YAML complet des stations calibrées."""
        if not self._stations_calibrees:
            print('\nAucune station calibrée.')
            return

        print('\n' + '=' * 60)
        print('RÉSULTAT — Copier dans config/stations.yaml :')
        print('=' * 60)
        print()
        print('stations:')

        descriptions = {
            'base_charge': 'Base de recharge — point de départ et de retour',
            'matieres_premieres': 'Zone de réception des bobines de papier',
            'poste_decoupe': 'Machines de découpe et rainurage',
            'controle_qualite': "Station d'inspection des cartons finis",
            'expedition': "Quai d'expédition",
        }

        for nom, coords in self._stations_calibrees.items():
            desc = descriptions.get(nom, f'Station {nom}')
            print(f'  {nom}:')
            print(f'    x: {coords["x"]}')
            print(f'    y: {coords["y"]}')
            print(f'    yaw: {coords["yaw"]}')
            print(f'    description: "{desc}"')
            print()

        print('=' * 60)

        # Stations non calibrées
        tous = ['base_charge', 'matieres_premieres', 'poste_decoupe',
                'controle_qualite', 'expedition']
        manquantes = [n for n in tous if n not in self._stations_calibrees]
        if manquantes:
            print(f'\n⚠ Stations non calibrées (placeholders conservés) :')
            for n in manquantes:
                print(f'  - {n}')


def main(args=None):
    """Point d'entrée du script de calibration."""
    rclpy.init(args=args)
    noeud = CapteurPoses()

    try:
        rclpy.spin(noeud)
    except KeyboardInterrupt:
        pass
    finally:
        noeud.afficher_yaml_final()
        noeud.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
