#!/usr/bin/env python3
"""Nœud ROS 2 d'orchestration des missions logistiques AMR."""

import asyncio
import math
import time

import rclpy
import yaml
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import FollowWaypoints, NavigateThroughPoses
from rclpy.action import ActionClient, ActionServer
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup, ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from std_msgs.msg import String

from industry_robot_mission.action import ExecuteMission
from industry_robot_mission.srv import StartMission


class MissionManagerNode(Node):
    """
    Nœud ROS 2 d'orchestration des missions logistiques.

    Charge les stations et missions depuis les fichiers YAML,
    pilote Nav2 via FollowWaypoints (avec repli sur NavigateThroughPoses),
    et publie l'état d'avancement sur /mission_status.
    """

    def __init__(self):
        """Initialise le nœud et toutes ses interfaces ROS 2."""
        super().__init__('mission_manager')

        # --- Paramètres ---
        self.declare_parameter('use_sim_time', True)
        self.declare_parameter('stations_file', '')
        self.declare_parameter('missions_file', '')
        self.declare_parameter('nav2_startup_delay', 5.0)

        # --- Groupes de callbacks pour la concurrence ---
        self.action_group = MutuallyExclusiveCallbackGroup()
        self.service_group = ReentrantCallbackGroup()

        # --- Données de configuration ---
        self._stations: dict = {}
        self._missions: dict = {}
        self._charger_configuration()

        # --- Publisher statut de mission ---
        self._pub_statut = self.create_publisher(String, '/mission_status', 10)

        # --- Service ~/start_mission ---
        self._service_start = self.create_service(
            StartMission,
            '~/start_mission',
            self._cb_start_mission,
            callback_group=self.service_group,
        )

        # --- Serveur d'action ~/execute_mission ---
        self._action_server = ActionServer(
            self,
            ExecuteMission,
            '~/execute_mission',
            self._cb_execute_mission,
            callback_group=self.action_group,
        )

        # --- Clients Nav2 ---
        self._client_follow_waypoints = ActionClient(
            self,
            FollowWaypoints,
            'follow_waypoints',
            callback_group=self.action_group,
        )
        self._client_navigate_through_poses = ActionClient(
            self,
            NavigateThroughPoses,
            'navigate_through_poses',
            callback_group=self.action_group,
        )

        # --- Délai de démarrage Nav2 (bloquant avant le spin) ---
        delai = self.get_parameter('nav2_startup_delay').get_parameter_value().double_value
        self.get_logger().info(f'MissionManager initialisé — attente Nav2 ({delai:.0f}s)...')
        time.sleep(delai)
        self.get_logger().info('MissionManager prêt à recevoir des missions.')

    # =========================================================================
    # Chargement de la configuration YAML
    # =========================================================================

    def _charger_configuration(self):
        """Charge les fichiers YAML des stations et des missions en mémoire."""
        fichier_stations = self.get_parameter('stations_file').get_parameter_value().string_value
        fichier_missions = self.get_parameter('missions_file').get_parameter_value().string_value

        try:
            with open(fichier_stations, 'r') as f:
                donnees = yaml.safe_load(f)
                self._stations = donnees.get('stations', {})
            self.get_logger().info(
                f'{len(self._stations)} station(s) chargée(s) depuis {fichier_stations}'
            )
        except Exception as e:
            self.get_logger().error(f'Erreur chargement stations : {e}')

        try:
            with open(fichier_missions, 'r') as f:
                donnees = yaml.safe_load(f)
                self._missions = donnees.get('missions', {})
            self.get_logger().info(
                f'{len(self._missions)} mission(s) chargée(s) depuis {fichier_missions}'
            )
        except Exception as e:
            self.get_logger().error(f'Erreur chargement missions : {e}')

    # =========================================================================
    # Conversion station → PoseStamped
    # =========================================================================

    def _station_vers_pose_stamped(self, nom_station: str) -> PoseStamped:
        """Convertit une station YAML en PoseStamped dans le repère 'map'."""
        station = self._stations[nom_station]
        yaw = float(station['yaw'])

        # Calcul direct du quaternion depuis le yaw (sans tf_transformations)
        qz = math.sin(yaw / 2.0)
        qw = math.cos(yaw / 2.0)

        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = float(station['x'])
        pose.pose.position.y = float(station['y'])
        pose.pose.position.z = 0.0
        pose.pose.orientation.x = 0.0
        pose.pose.orientation.y = 0.0
        pose.pose.orientation.z = qz
        pose.pose.orientation.w = qw

        return pose

    # =========================================================================
    # Publication de statut
    # =========================================================================

    def _publier_statut(self, message: str):
        """Publie un message texte sur /mission_status et dans les logs du nœud."""
        msg = String()
        msg.data = message
        self._pub_statut.publish(msg)
        self.get_logger().info(f'[STATUT] {message}')

    # =========================================================================
    # Callback service ~/start_mission
    # =========================================================================

    def _cb_start_mission(self, requete, reponse):
        """Valide la mission demandée et retourne la liste ordonnée des stations."""
        nom = requete.mission_name

        if nom not in self._missions:
            reponse.accepted = False
            reponse.message = (
                f'Mission inconnue : "{nom}". '
                f'Missions disponibles : {list(self._missions.keys())}'
            )
            reponse.stations_liste = []
            return reponse

        stations = self._missions[nom]['stations']
        reponse.accepted = True
        reponse.message = f'Mission "{nom}" acceptée — {len(stations)} station(s).'
        reponse.stations_liste = stations

        self.get_logger().info(f'start_mission : "{nom}" validée ({len(stations)} stations).')
        return reponse

    # =========================================================================
    # Callback serveur d'action ~/execute_mission
    # =========================================================================

    async def _cb_execute_mission(self, goal_handle):
        """Orchestre l'exécution d'une mission avec reprise automatique en cas d'échec."""
        nom_mission = goal_handle.request.mission_name
        self.get_logger().info(f'Exécution demandée pour la mission : "{nom_mission}"')

        if nom_mission not in self._missions:
            self.get_logger().error(f'Mission inconnue : "{nom_mission}"')
            resultat = ExecuteMission.Result()
            resultat.success = False
            resultat.message = f'Mission inconnue : "{nom_mission}"'
            resultat.stations_visitees = 0
            goal_handle.abort()
            return resultat

        # Première tentative
        succes, stations_visitees, message = await self._executer_nav2(
            goal_handle, nom_mission, publier_feedback=True
        )

        # Deuxième tentative si la première échoue
        if not succes:
            self.get_logger().warn(
                f'Première tentative échouée pour "{nom_mission}" — reprise en cours...'
            )
            self._publier_statut(f'REPRISE — "{nom_mission}"')
            succes, stations_visitees, message = await self._executer_nav2(
                goal_handle, nom_mission, publier_feedback=True
            )

        # Retour base automatique après double échec
        if not succes:
            self.get_logger().error(
                f'Double échec pour "{nom_mission}" — déclenchement retour_base.'
            )
            self._publier_statut('MISSION_ECHEC — déclenchement automatique retour_base')
            if 'retour_base' in self._missions and nom_mission != 'retour_base':
                await self._executer_nav2(goal_handle, 'retour_base', publier_feedback=False)

        resultat = ExecuteMission.Result()
        resultat.success = succes
        resultat.message = message
        resultat.stations_visitees = stations_visitees

        if succes:
            goal_handle.succeed()
        else:
            goal_handle.abort()

        return resultat

    # =========================================================================
    # Exécution Nav2 d'une mission
    # =========================================================================

    async def _executer_nav2(
        self, goal_handle, nom_mission: str, publier_feedback: bool
    ) -> tuple:
        """
        Envoie les waypoints à Nav2 et attend le résultat.

        Retourne un tuple (succès: bool, stations_visitées: int, message: str).
        """
        mission = self._missions[nom_mission]
        noms_stations = mission['stations']

        # Construction de la liste de PoseStamped
        poses = []
        for nom in noms_stations:
            if nom not in self._stations:
                self.get_logger().warn(f'Station inconnue ignorée : "{nom}"')
                continue
            poses.append(self._station_vers_pose_stamped(nom))

        nb_stations = len(poses)
        if nb_stations == 0:
            return False, 0, 'Aucune pose valide pour cette mission.'

        timeout_sec = float(max(nb_stations * 120, 300))

        # Sélection du client Nav2 disponible
        client, type_action = await self._choisir_client_nav2()
        if client is None:
            return False, 0, 'Aucun serveur Nav2 disponible (FollowWaypoints ni NavigateThroughPoses).'

        # Construction du goal Nav2
        goal_msg = type_action.Goal()
        goal_msg.poses = poses
        if type_action == NavigateThroughPoses:
            goal_msg.behavior_tree = ''

        self._publier_statut(
            f'DÉPART "{nom_mission}" — {nb_stations} station(s) via {type_action.__name__}'
        )

        # Callback feedback local (capturé par closure)
        def cb_feedback_nav2(fb_msg):
            if publier_feedback:
                self._cb_feedback_nav2(fb_msg, goal_handle, noms_stations)

        # Envoi du goal et attente de l'acceptation (timeout 30s)
        send_future = client.send_goal_async(goal_msg, feedback_callback=cb_feedback_nav2)
        try:
            gh_nav2 = await asyncio.wait_for(
                self._attendre_future(send_future), timeout=30.0
            )
        except asyncio.TimeoutError:
            self.get_logger().error('Timeout attente acceptation du goal Nav2 (30s).')
            return False, 0, 'Timeout lors de l\'envoi du goal Nav2.'

        if not gh_nav2.accepted:
            self.get_logger().error('Goal Nav2 refusé par le serveur.')
            return False, 0, 'Goal Nav2 refusé.'

        # Attente du résultat avec timeout mission
        result_future = gh_nav2.get_result_async()
        try:
            result_response = await asyncio.wait_for(
                self._attendre_future(result_future), timeout=timeout_sec
            )
        except asyncio.TimeoutError:
            self.get_logger().error(
                f'Timeout mission atteint ({timeout_sec:.0f}s) — annulation du goal Nav2.'
            )
            await gh_nav2.cancel_goal_async()
            self._publier_statut('MISSION_ECHEC — timeout')
            return False, 0, f'Timeout mission ({timeout_sec:.0f}s) atteint.'

        # Analyse du résultat
        return self._analyser_resultat_nav2(
            result_response, type_action, nom_mission, noms_stations, nb_stations,
            goal_handle, publier_feedback
        )

    def _analyser_resultat_nav2(
        self, result_response, type_action, nom_mission: str,
        noms_stations: list, nb_stations: int, goal_handle, publier_feedback: bool
    ) -> tuple:
        """Analyse le résultat Nav2 et retourne (succès, stations_visitées, message)."""
        # FollowWaypoints : résultat via missed_waypoints
        if type_action == FollowWaypoints:
            missed = list(result_response.result.missed_waypoints)
            stations_visitees = nb_stations - len(missed)

            if missed:
                noms_manques = [
                    noms_stations[i] for i in missed if i < len(noms_stations)
                ]
                self.get_logger().warn(f'Stations manquées : {noms_manques}')
                self._publier_statut(f'ECHEC_PARTIEL — stations manquées : {noms_manques}')

                if publier_feedback:
                    fb = ExecuteMission.Feedback()
                    fb.station_courante = ''
                    fb.station_index = stations_visitees
                    fb.station_total = nb_stations
                    fb.statut = 'ECHEC_PARTIEL'
                    fb.progression = float(stations_visitees) / float(nb_stations)
                    goal_handle.publish_feedback(fb)

                return (
                    False,
                    stations_visitees,
                    f'Mission "{nom_mission}" — {stations_visitees}/{nb_stations} stations atteintes.'
                )

        # NavigateThroughPoses : résultat via error_code
        else:
            error_code = getattr(result_response.result, 'error_code', 0)
            stations_visitees = nb_stations if error_code == 0 else 0

            if error_code != 0:
                self.get_logger().error(
                    f'NavigateThroughPoses erreur code={error_code}'
                )
                self._publier_statut(f'MISSION_ECHEC — erreur Nav2 code={error_code}')
                return (
                    False,
                    0,
                    f'Mission "{nom_mission}" — erreur Nav2 (code={error_code}).'
                )

        # Succès
        self._publier_statut(
            f'MISSION_TERMINEE — "{nom_mission}" ({stations_visitees}/{nb_stations} stations)'
        )
        return (
            True,
            stations_visitees,
            f'Mission "{nom_mission}" complétée — {stations_visitees} station(s) visitée(s).'
        )

    # =========================================================================
    # Callback feedback Nav2
    # =========================================================================

    def _cb_feedback_nav2(self, fb_msg, goal_handle, noms_stations: list):
        """Traite le feedback Nav2 FollowWaypoints et propage la progression au client."""
        try:
            idx = int(fb_msg.feedback.current_waypoint)
        except AttributeError:
            return

        nb_total = len(noms_stations)
        nom_station = noms_stations[idx] if idx < nb_total else f'waypoint_{idx}'

        self._publier_statut(f'EN_ROUTE → {nom_station} ({idx + 1}/{nb_total})')

        fb = ExecuteMission.Feedback()
        fb.station_courante = nom_station
        fb.station_index = idx
        fb.station_total = nb_total
        fb.statut = 'EN_ROUTE'
        fb.progression = float(idx) / float(nb_total) if nb_total > 0 else 0.0
        goal_handle.publish_feedback(fb)

    # =========================================================================
    # Sélection du client Nav2
    # =========================================================================

    async def _choisir_client_nav2(self) -> tuple:
        """Sélectionne FollowWaypoints en priorité, avec repli sur NavigateThroughPoses."""
        self.get_logger().info('Recherche serveur Nav2 FollowWaypoints (timeout 10s)...')
        if await self._attendre_serveur(self._client_follow_waypoints, 10.0):
            self.get_logger().info('Serveur FollowWaypoints disponible.')
            return self._client_follow_waypoints, FollowWaypoints

        self.get_logger().warn(
            'FollowWaypoints indisponible — repli sur NavigateThroughPoses (timeout 10s)...'
        )
        if await self._attendre_serveur(self._client_navigate_through_poses, 10.0):
            self.get_logger().info('Serveur NavigateThroughPoses disponible.')
            return self._client_navigate_through_poses, NavigateThroughPoses

        self.get_logger().error('Aucun serveur Nav2 disponible.')
        return None, None

    async def _attendre_serveur(self, client, timeout_sec: float) -> bool:
        """Attend qu'un serveur d'action soit prêt, sans bloquer l'exécuteur."""
        debut = time.monotonic()
        while not client.server_is_ready():
            if time.monotonic() - debut > timeout_sec:
                return False
            await asyncio.sleep(0.5)
        return True

    async def _attendre_future(self, future):
        """Attend qu'une future rclpy soit résolue (polling non bloquant)."""
        while not future.done():
            await asyncio.sleep(0.05)
        return future.result()


# =============================================================================
# Point d'entrée
# =============================================================================

def main(args=None):
    """Lance le nœud MissionManager avec un exécuteur multi-thread."""
    rclpy.init(args=args)
    noeud = MissionManagerNode()

    executeur = MultiThreadedExecutor()
    executeur.add_node(noeud)

    try:
        executeur.spin()
    except KeyboardInterrupt:
        pass
    finally:
        noeud.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
