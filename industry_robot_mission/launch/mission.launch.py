#!/usr/bin/env python3
"""Fichier de lancement du nœud mission_manager."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Génère la description de lancement pour le nœud mission_manager."""
    pkg_dir = get_package_share_directory('industry_robot_mission')

    # --- Arguments de lancement ---
    arg_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description="Synchronisation avec l'horloge Gazebo (true) ou robot réel (false)",
    )

    arg_stations_file = DeclareLaunchArgument(
        'stations_file',
        default_value=os.path.join(pkg_dir, 'config', 'stations.yaml'),
        description='Chemin absolu vers le fichier de configuration des stations',
    )

    arg_missions_file = DeclareLaunchArgument(
        'missions_file',
        default_value=os.path.join(pkg_dir, 'config', 'missions.yaml'),
        description='Chemin absolu vers le fichier de configuration des missions',
    )

    # --- Nœud mission_manager ---
    noeud_mission_manager = Node(
        package='industry_robot_mission',
        executable='mission_manager.py',
        name='mission_manager',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'stations_file': LaunchConfiguration('stations_file'),
            'missions_file': LaunchConfiguration('missions_file'),
        }],
    )

    return LaunchDescription([
        arg_use_sim_time,
        arg_stations_file,
        arg_missions_file,
        noeud_mission_manager,
    ])
