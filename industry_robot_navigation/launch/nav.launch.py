"""
nav.launch.py — Lancement de la Navigation Autonome Nav2

Architecture identique à TurtleBot3 Navigation :
  1. Lance la simulation Gazebo (robot + capteurs + bridge + filtre laser)
  2. Lance nav2_bringup (AMCL, Map Server, Planner, Controller, BT, Behaviors)
  3. Lance RViz2 avec la configuration de navigation

Prérequis :
  sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup

Utilisation :
  ros2 launch industry_robot_navigation nav.launch.py
  ros2 launch industry_robot_navigation nav.launch.py use_sim:=false   # Robot réel
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
    nav_pkg = get_package_share_directory('industry_robot_navigation')
    desc_pkg = get_package_share_directory('industry_robot_description')
    sim_pkg = get_package_share_directory('industry_robot_sim')
    nav2_bringup_pkg = get_package_share_directory('nav2_bringup')

    # ── Arguments configurables ──
    use_sim = LaunchConfiguration('use_sim')
    use_rviz = LaunchConfiguration('use_rviz')

    declare_use_sim = DeclareLaunchArgument(
        'use_sim', default_value='true',
        description='Utiliser l\'horloge simulée Gazebo (true pour simulation)'
    )
    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz', default_value='true',
        description='Lancer RViz2 avec la configuration navigation'
    )

    # ── Chemins vers les fichiers de configuration ──
    params_file = os.path.join(nav_pkg, 'config', 'nav2_params.yaml')
    map_yaml_file = os.path.join(desc_pkg, 'maps', 'warehouse.yaml')
    rviz_config = os.path.join(nav_pkg, 'rviz', 'nav.rviz')

    # ── 1. Simulation Gazebo (robot + capteurs + bridge + filtre laser) ──
    launch_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(sim_pkg, 'launch', 'sim.launch.py')
        ),
        condition=IfCondition(use_sim)
    )

    # ── 2. Nav2 Bringup (comme TurtleBot3) ──
    # Lance automatiquement : AMCL, Map Server, Planner Server,
    # Controller Server, BT Navigator, Behavior Server, Lifecycle Manager
    bringup_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_pkg, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'map': map_yaml_file,
            'use_sim_time': use_sim,
            'params_file': params_file,
            'autostart': 'True',
        }.items()
    )

    # ── 3. RViz2 Navigation ──
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
        launch_sim,
        bringup_cmd,
        rviz,
    ])