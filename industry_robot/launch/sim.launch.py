import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
import sys


def generate_launch_description():
    # Chemins vers les ressources du package
    pkg_share = get_package_share_directory('industry_robot')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    xacro_file   = os.path.join(pkg_share, 'urdf', 'warehouse_bot.urdf.xacro')
    bridge_config        = os.path.join(pkg_share, 'config', 'bridge.yaml')
    laser_filter_config  = os.path.join(pkg_share, 'config', 'laser_filter.yaml')
    rviz_config          = os.path.join(pkg_share, 'rviz', 'view_robot.rviz')
    world_file = os.path.join(pkg_share, 'worlds', 'warehouse.sdf')

    # Generation du monde SDF
    if not os.path.isfile(world_file):
        scripts_dir = os.path.join(pkg_share, 'scripts', 'world')
        sys.path.insert(0, scripts_dir)
        from generate_warehouse import generate_warehouse_sdf
 
        os.makedirs(os.path.join(pkg_share, 'worlds'), exist_ok=True)
        generate_warehouse_sdf(
            num_rows=4,
            shelves_per_row=3,
            pallet_count=4,
            output_file=world_file,
        )
    else:
        print(f"[sim.launch.py] Monde existant trouvé : {world_file}")
        print("  → Pour régénérer, supprimer ce fichier et relancer.")

    # Conversion Xacro → URDF
    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str
    )

    # GAZEBO HARMONIC — Lancer le simulateur avec un monde vide
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {world_file}'}.items()
    )

    # ROBOT STATE PUBLISHER — Publie les TFs du robot
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True
        }]
    )

    # JOINT STATE PUBLISHER — Fournit les joint_states aux roues (continuous joints)
    # source_list: utilise les vraies valeurs Gazebo si le bridge fonctionne,
    # sinon publie des positions nulles (roues visibles dans RViz).
    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
            'source_list': ['joint_states_gz'],
        }],
        output='screen'
    )

    # SPAWNER — Faire apparaître le robot dans Gazebo
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'warehouse_bot',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.0',
        ],
        output='screen'
    )

    # BRIDGE ROS_GZ — Pont de communication Gazebo ↔ ROS 2
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': bridge_config,
            'use_sim_time': True
        }],
        output='screen'
    )

    # FILTRE LASER — supprime les points dans une boîte autour du robot
    # Entrée : /scan  →  Sortie : /scan_filtered
    laser_filter = Node(
        package='laser_filters',
        executable='scan_to_scan_filter_chain',
        name='laser_filter',
        parameters=[
            laser_filter_config,
            {'use_sim_time': True}
        ],
        remappings=[
            ('scan', '/scan'),
            ('scan_filtered', '/scan_filtered'),
        ],
        output='screen'
    )

    # RVIZ2 — Visualisation du robot et des données capteurs
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
        joint_state_publisher,
        spawn_entity,
        bridge,
        laser_filter,
        rviz,
    ])
