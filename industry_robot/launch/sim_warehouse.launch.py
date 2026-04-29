# ================================================================
# sim_warehouse.launch.py — Simulation dans l'environnement entrepôt
# Identique à sim.launch.py mais charge le monde warehouse.sdf
# au lieu du monde vide. Permet de tester la navigation avec
# obstacles (étagères, palettes de cartons, murs, piliers).
# ================================================================

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    # Chemins vers les ressources du package
    pkg_share = get_package_share_directory('industry_robot')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    xacro_file    = os.path.join(pkg_share, 'urdf', 'warehouse_bot.urdf.xacro')
    bridge_config = os.path.join(pkg_share, 'config', 'bridge.yaml')
    rviz_config   = os.path.join(pkg_share, 'rviz', 'view_robot.rviz')
    world_file    = os.path.join(pkg_share, 'worlds', 'warehouse.sdf')

    # --- Conversion Xacro → URDF ---
    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str
    )

    # ============================================================
    # 1. GAZEBO HARMONIC — Lancer avec le monde entrepôt
    # ============================================================
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {world_file}'}.items()
    )

    # ============================================================
    # 2. ROBOT STATE PUBLISHER
    # ============================================================
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True
        }]
    )

    # ============================================================
    # 3. SPAWNER — Position initiale dans l'entrepôt
    #    Placé à x=2, y=2 pour éviter les obstacles au démarrage
    # ============================================================
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'warehouse_bot',
            '-x', '2.0',
            '-y', '2.0',
            '-z', '0.0',
        ],
        output='screen'
    )

    # ============================================================
    # 4. BRIDGE ROS_GZ
    # ============================================================
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': bridge_config,
            'use_sim_time': True
        }],
        output='screen'
    )

    # ============================================================
    # 5. RVIZ2
    # ============================================================
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        spawn_entity,
        bridge,
        rviz,
    ])
