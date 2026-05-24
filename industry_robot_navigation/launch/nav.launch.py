"""
nav.launch.py — Navigation Autonome Nav2 (sans docking_server)

Lance chaque nœud Nav2 individuellement et configure les lifecycle managers
avec une liste explicite de nœuds — sans dépendre de bringup_launch.py dont
la liste hardcodée inclut docking_server (qui avorte le bringup si non configuré).

Architecture :
  1. Simulation Gazebo  (sim.launch.py)
  2. Map Server + AMCL  → lifecycle_manager_localization
  3. Nœuds Nav2         → lifecycle_manager_navigation
  4. RViz2

Utilisation :
  ros2 launch industry_robot_navigation nav.launch.py
  ros2 launch industry_robot_navigation nav.launch.py use_sim:=false map:=/chemin/carte.yaml
"""

import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    nav_pkg  = get_package_share_directory('industry_robot_navigation')
    desc_pkg = get_package_share_directory('industry_robot_description')
    sim_pkg  = get_package_share_directory('industry_robot_sim')

    # ── Chemins fixes ────────────────────────────────────────────────────────
    params_file    = os.path.join(nav_pkg,  'config', 'nav2_params.yaml')
    default_map    = os.path.join(desc_pkg, 'maps',   'warehouse.yaml')
    rviz_config    = os.path.join(nav_pkg,  'rviz',   'nav.rviz')
    nogoZone_map   = os.path.join(desc_pkg, 'maps',   'keepOut.yaml')

    # ── Arguments ────────────────────────────────────────────────────────────
    use_sim  = LaunchConfiguration('use_sim')
    use_rviz = LaunchConfiguration('use_rviz')
    map_yaml = LaunchConfiguration('map')

    declare_use_sim = DeclareLaunchArgument(
        'use_sim', default_value='true',
        description='Horloge Gazebo (true) ou robot réel (false)')

    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz', default_value='true',
        description='Lancer RViz2')

    declare_map = DeclareLaunchArgument(
        'map', default_value=default_map,
        description='Chemin vers le fichier YAML de la carte')

    # ── Nœuds du lifecycle_manager_localization ───────────────────────────────
    # filter_mask_server et costmap_filter_info_server DOIVENT être activés
    # AVANT les costmaps (controller_server, planner_server) pour que le
    # KeepoutFilter reçoive le mask au moment de son initialisation.
    localization_nodes = [
        'map_server',
        'amcl',
        'filter_mask_server',
        'costmap_filter_info_server',
    ]

    # ── Nœuds du lifecycle_manager_navigation ────────────────────────────────
    # docking_server volontairement EXCLU : non utilisé dans ce projet.
    # Son absence dans nav2_bringup/bringup_launch.py causait un abort fatal.
    navigation_nodes = [
        'controller_server',
        'smoother_server',
        'planner_server',
        'behavior_server',
        'bt_navigator',
        'waypoint_follower',
        'velocity_smoother',
        'collision_monitor',
        'route_server',
    ]

    # ── 1. Simulation Gazebo ─────────────────────────────────────────────────
    launch_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(sim_pkg, 'launch', 'sim.launch.py')),
        condition=IfCondition(use_sim)
    )

    # ── 2a. Map Server ───────────────────────────────────────────────────────
    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[params_file, {'yaml_filename': map_yaml, 'use_sim_time': use_sim}]
    )

    # ── 2b. AMCL ─────────────────────────────────────────────────────────────
    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim}]
    )

    

    filter_mask_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='filter_mask_server',
        output='screen',
        parameters=[
            params_file,          # Load the default configurations first
            {'yaml_filename': nogoZone_map}  # Override with the dynamic path!
        ]
    )

    costmap_filter_info_server_node = Node(
        package='nav2_map_server',
        executable='costmap_filter_info_server',
        name='costmap_filter_info_server', # <-- Match this name as well
        output='screen',
        parameters=[params_file]
    )

    # ── 2c. Lifecycle Manager — Localisation ─────────────────────────────────
    lifecycle_manager_loc = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[{'use_sim_time': use_sim,
                     'autostart': True,
                     'node_names': localization_nodes}]
    )

    # ── 3a. Controller Server ─────────────────────────────────────────────────
    controller_server = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim}]
    )

    # ── 3b. Smoother Server ───────────────────────────────────────────────────
    smoother_server = Node(
        package='nav2_smoother',
        executable='smoother_server',
        name='smoother_server',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim}]
    )

    # ── 3c. Planner Server ────────────────────────────────────────────────────
    planner_server = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim}]
    )

    # ── 3d. Behavior Server ───────────────────────────────────────────────────
    behavior_server = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim}]
    )

    # ── 3e. BT Navigator ─────────────────────────────────────────────────────
    bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim}]
    )

    # ── 3f. Waypoint Follower ─────────────────────────────────────────────────
    waypoint_follower = Node(
        package='nav2_waypoint_follower',
        executable='waypoint_follower',
        name='waypoint_follower',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim}]
    )

    # ── 3g. Velocity Smoother ─────────────────────────────────────────────────
    velocity_smoother = Node(
        package='nav2_velocity_smoother',
        executable='velocity_smoother',
        name='velocity_smoother',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim}]
    )

    # ── 3h. Collision Monitor ─────────────────────────────────────────────────
    collision_monitor = Node(
        package='nav2_collision_monitor',
        executable='collision_monitor',
        name='collision_monitor',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim}]
    )

    # ── 3i. Route Server ─────────────────────────────────────────────────────
    route_server = Node(
        package='nav2_route',
        executable='route_server',
        name='route_server',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim}]
    )

    # ── 3j. Lifecycle Manager — Navigation ───────────────────────────────────
    lifecycle_manager_nav = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[{'use_sim_time': use_sim,
                     'autostart': True,
                     'node_names': navigation_nodes}]
    )

    # ── 4. RViz2 ─────────────────────────────────────────────────────────────
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2_nav',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim}],
        condition=IfCondition(use_rviz)
    )

    return LaunchDescription([
        declare_use_sim,
        declare_use_rviz,
        declare_map,
        # Gazebo
        launch_sim,
        # Localisation
        map_server,
        amcl,
        filter_mask_server_node,
        costmap_filter_info_server_node,
        lifecycle_manager_loc,
        # Navigation
        controller_server,
        smoother_server,
        planner_server,
        behavior_server,
        bt_navigator,
        waypoint_follower,
        velocity_smoother,
        collision_monitor,
        route_server,
        lifecycle_manager_nav,
        # Visualisation
        rviz,
    ])
