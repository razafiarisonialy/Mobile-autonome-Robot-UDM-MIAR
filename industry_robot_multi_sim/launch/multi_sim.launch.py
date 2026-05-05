import os
import sys
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    pkg_description = get_package_share_directory('industry_robot_description')
    pkg_sim         = get_package_share_directory('industry_robot_sim')
    pkg_multi_sim   = get_package_share_directory('industry_robot_multi_sim')
    pkg_ros_gz_sim  = get_package_share_directory('ros_gz_sim')

    xacro_file          = os.path.join(pkg_description, 'urdf', 'warehouse_bot.urdf.xacro')
    world_file          = os.path.join(pkg_description, 'worlds', 'warehouse.sdf')
    laser_filter_config = os.path.join(pkg_description, 'config', 'laser_filter.yaml')
    rviz_config         = os.path.join(pkg_multi_sim, 'rviz', 'multi_sim.rviz')
    
    world_name = 'warehouse_world'

    # Lancement de Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {world_file}'}.items()
    )

    nodes = [gazebo]

    # Bridge horloge (global, unique)
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='clock_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )
    nodes.append(clock_bridge)

    # Définition des 4 robots
    robots = [
        {'name': 'robot1', 'x': '1.0', 'y': '3.0'},
        {'name': 'robot2', 'x': '1.0', 'y': '0.0'},
        {'name': 'robot3', 'x': '1.0', 'y': '-3.0'},
        {'name': 'robot4', 'x': '-2.0', 'y': '0.0'},
    ]

    for robot in robots:
        name = robot['name']

        # Commande pour générer l'URDF avec le paramètre namespace
        robot_desc = ParameterValue(
            Command(['xacro ', xacro_file, ' namespace:=', name]),
            value_type=str
        )

        # Groupe pour chaque robot
        robot_group = GroupAction([
            # State Publisher
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
                }],
                remappings=[
                    ('/tf', '/tf'),
                    ('/tf_static', '/tf_static'),
                ]
            ),
            # Joint State Publisher
            Node(
                package='joint_state_publisher',
                executable='joint_state_publisher',
                name=f'{name}_joint_state_publisher',
                namespace=name,
                parameters=[{
                    'robot_description': robot_desc,
                    'use_sim_time': True,
                    'source_list': [f'/{name}/joint_states_gz'],
                }],
                output='screen'
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
            ),
            # Static TF publisher: world -> {name}/odom
            Node(
                package='tf2_ros',
                executable='static_transform_publisher',
                name=f'{name}_static_tf',
                arguments=[
                    robot['x'], robot['y'], '0',
                    '0', '0', '0',
                    'world', f'{name}/odom'
                ],
                output='screen'
            )
        ])
        nodes.append(robot_group)

        # Bridge par robot (toujours via arguments ici, ou on pourrait utiliser un bridge_multi.yaml)
        # Si on veut utiliser bridge_multi.yaml, il faudrait qu'il contienne tous les robots.
        # Pour l'instant on garde les arguments pour la flexibilité du loop.
        robot_bridge = Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name=f'{name}_bridge',
            arguments=[
                f'/model/{name}/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
                f'/model/{name}/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
                f'/model/{name}/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
                f'/world/{world_name}/model/{name}/joint_state@sensor_msgs/msg/JointState[gz.msgs.Model',
                f'/{name}/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
                f'/model/{name}/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            ],
            remappings=[
                (f'/model/{name}/cmd_vel', f'/{name}/cmd_vel'),
                (f'/model/{name}/odometry', f'/{name}/odom'),
                (f'/model/{name}/tf', '/tf'),
                (f'/world/{world_name}/model/{name}/joint_state', f'/{name}/joint_states_gz'),
                (f'/model/{name}/imu', f'/{name}/imu'),
            ],
            parameters=[{'use_sim_time': True}],
            output='screen'
        )
        nodes.append(robot_bridge)

        # Filtre Laser
        laser_filter = Node(
            package='laser_filters',
            executable='scan_to_scan_filter_chain',
            name=f'{name}_laser_filter',
            parameters=[
                laser_filter_config,
                {
                    'use_sim_time': True,
                    'filter1.params.box_frame': f'{name}/base_link',
                }
            ],
            remappings=[
                ('scan', f'/{name}/scan'),
                ('scan_filtered', f'/{name}/scan_filtered'),
            ],
            output='screen'
        )
        nodes.append(laser_filter)

    # RViz
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )
    nodes.append(rviz)

    return LaunchDescription(nodes)
