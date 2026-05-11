# ================================================================
# slam.launch.py — Lancement du SLAM Cartographer pour industry_robot
#
# Reproduit la mécanique du package turtlebot3_cartographer
# (cartographer_node + cartographer_occupancy_grid_node) mais en
# utilisant notre propre fichier de configuration adapté au robot
# industriel (industry_robot_2d.lua).
#
# Pré-requis : sim.launch.py de industry_robot_sim doit déjà tourner
# dans un autre terminal (Gazebo + bridge + laser_filter actifs).
#
# Topic SLAM en entrée : /scan_filtered (LiDAR filtré)
# Topic SLAM en sortie : /map (OccupancyGrid)
# ================================================================

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_slam = get_package_share_directory('industry_robot_slam')

    cartographer_config_dir = os.path.join(pkg_slam, 'config')
    configuration_basename  = 'industry_robot_2d.lua'
    rviz_config             = os.path.join(pkg_slam, 'rviz', 'slam.rviz')

    # ========== Arguments de lancement ==========
    use_sim_time       = LaunchConfiguration('use_sim_time',       default='true')
    use_rviz           = LaunchConfiguration('use_rviz',           default='true')
    scan_topic         = LaunchConfiguration('scan_topic',         default='/scan_filtered')
    resolution         = LaunchConfiguration('resolution',         default='0.05')
    publish_period_sec = LaunchConfiguration('publish_period_sec', default='1.0')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Utiliser le temps simulé (Gazebo).'
    )
    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz', default_value='true',
        description='Lancer RViz avec la config slam.rviz.'
    )
    declare_scan_topic = DeclareLaunchArgument(
        'scan_topic', default_value='/scan_filtered',
        description="Topic LiDAR consommé par Cartographer (default: /scan_filtered)."
    )
    declare_resolution = DeclareLaunchArgument(
        'resolution', default_value='0.05',
        description="Résolution de la carte d'occupation en m/cell."
    )
    declare_publish_period = DeclareLaunchArgument(
        'publish_period_sec', default_value='1.0',
        description='Période de publication de /map en secondes.'
    )

    # ========== Cartographer node (SLAM) ==========
    cartographer_node = Node(
        package='cartographer_ros',
        executable='cartographer_node',
        name='cartographer_node',
        output='screen',
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        arguments=[
            '-configuration_directory', cartographer_config_dir,
            '-configuration_basename',  configuration_basename,
        ],
        remappings=[
            ('scan', scan_topic),
            ('imu',  '/imu'),
            ('odom', '/odom'),
        ],
    )

    # ========== Occupancy grid node (carte 2D publiée sur /map) ==========
    occupancy_grid_node = Node(
        package='cartographer_ros',
        executable='cartographer_occupancy_grid_node',
        name='cartographer_occupancy_grid_node',
        output='screen',
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        arguments=[
            '-resolution',         resolution,
            '-publish_period_sec', publish_period_sec,
        ],
    )

    # ========== RViz (optionnel, désactivable avec use_rviz:=false) ==========
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        condition=IfCondition(use_rviz),
        output='screen',
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_use_rviz,
        declare_scan_topic,
        declare_resolution,
        declare_publish_period,
        cartographer_node,
        occupancy_grid_node,
        rviz_node,
    ])
