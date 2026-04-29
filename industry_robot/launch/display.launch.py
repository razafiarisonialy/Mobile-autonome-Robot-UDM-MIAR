# ================================================================
# display.launch.py — Visualisation URDF dans RViz (sans Gazebo)
# Démarre : robot_state_publisher + joint_state_publisher_gui + RViz2
# Utile pour vérifier le modèle 3D et l'arbre TF avant simulation.
# ================================================================

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    # Chemins vers les ressources du package
    pkg_share = get_package_share_directory('industry_robot')
    xacro_file  = os.path.join(pkg_share, 'urdf', 'warehouse_bot.urdf.xacro')
    rviz_config = os.path.join(pkg_share, 'rviz', 'view_robot.rviz')

    # --- Conversion Xacro → URDF ---
    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str
    )

    # ============================================================
    # 1. ROBOT STATE PUBLISHER — Publie /robot_description et les TFs
    # ============================================================
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description}]
    )

    # ============================================================
    # 2. JOINT STATE PUBLISHER GUI — Sliders pour bouger les joints
    #    Permet de tester manuellement la rotation des roues.
    # ============================================================
    joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        output='screen'
    )

    # ============================================================
    # 3. RVIZ2 — Visualisation du modèle 3D
    # ============================================================
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        output='screen'
    )

    return LaunchDescription([
        robot_state_publisher,
        joint_state_publisher_gui,
        rviz,
    ])
