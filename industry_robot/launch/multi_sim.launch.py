import os
import sys
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, GroupAction, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    pkg_share = get_package_share_directory('industry_robot')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    xacro_file = os.path.join(pkg_share, 'urdf', 'warehouse_bot.urdf.xacro')
    world_file = os.path.join(pkg_share, 'worlds', 'warehouse.sdf')
    
    # 1. Génération du monde s'il n'existe pas
    if not os.path.isfile(world_file):
        scripts_dir = os.path.join(pkg_share, 'scripts', 'world')
        sys.path.insert(0, scripts_dir)
        from generate_warehouse import generate_warehouse_sdf
        os.makedirs(os.path.join(pkg_share, 'worlds'), exist_ok=True)
        generate_warehouse_sdf(4, 3, 4, world_file)

    # 2. Lancement de Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {world_file}'}.items()
    )

    # Bridge global (Horloge)
    bridge_args = ['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock']
    
    nodes = [gazebo]

    # Définition des 4 robots (nom et position initiale)
    robots = [
        {'name': 'robot1', 'x': '1.0', 'y': '1.0'},
        {'name': 'robot2', 'x': '1.0', 'y': '-1.0'},
        {'name': 'robot3', 'x': '-1.0', 'y': '1.0'},
        {'name': 'robot4', 'x': '-1.0', 'y': '-1.0'},
    ]

    for robot in robots:
        name = robot['name']
        
        # Commande pour générer l'URDF avec le paramètre robot_name
        robot_desc = ParameterValue(
            Command(['xacro ', xacro_file, ' robot_name:=', name]),
            value_type=str
        )

        # Groupe pour chaque robot (permet de compartimenter si besoin)
        robot_group = GroupAction([
            # State Publisher avec frame_prefix
            Node(
                package='robot_state_publisher',
                executable='robot_state_publisher',
                name=f'{name}_state_publisher',
                namespace=name,
                output='screen',
                parameters=[{
                    'robot_description': robot_desc,
                    'use_sim_time': True,
                    'frame_prefix': f'{name}/'
                }]
            ),
            # Spawner
            Node(
                package='ros_gz_sim',
                executable='create',
                name=f'{name}_spawner',
                arguments=[
                    '-topic', f'/{name}/robot_description',
                    '-name', name,
                    '-x', robot['x'],
                    '-y', robot['y'],
                    '-z', '0.2',
                ],
                output='screen'
            )
        ])
        nodes.append(robot_group)

        # Ajout des topics de ce robot au bridge
        bridge_args.extend([
            f'/{name}/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            f'/{name}/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            f'/{name}/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            f'/{name}/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            f'/{name}/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            f'/{name}/imu@sensor_msgs/msg/Imu[gz.msgs.IMU'
        ])

    # 3. Le noeud Bridge avec tous les arguments
    global_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='global_ros_gz_bridge',
        arguments=bridge_args,
        parameters=[{'use_sim_time': True}],
        output='screen'
    )
    nodes.append(global_bridge)

    # 4. (Optionnel) Un seul RViz pour tous les robots, on utilise la config de base.
    # Note: Dans RViz, la frame par défaut devra être configurée sur "world" ou "robot1/odom"
    rviz_config = os.path.join(pkg_share, 'rviz', 'view_robot.rviz')
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )
    nodes.append(rviz)

    return LaunchDescription(nodes)
