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
    pkg_share = get_package_share_directory('industry_robot')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    xacro_file = os.path.join(pkg_share, 'urdf', 'warehouse_bot.urdf.xacro')
    world_file = os.path.join(pkg_share, 'worlds', 'warehouse.sdf')

    # Génération du monde s'il n'existe pas
    if not os.path.isfile(world_file):
        scripts_dir = os.path.join(pkg_share, 'scripts', 'world')
        sys.path.insert(0, scripts_dir)
        from generate_warehouse import generate_warehouse_sdf
        os.makedirs(os.path.join(pkg_share, 'worlds'), exist_ok=True)
        generate_warehouse_sdf(4, 3, 4, world_file)

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

    # Définition des 4 robots (nom et position initiale)
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
                }],
                remappings=[
                    ('/tf', '/tf'),
                    ('/tf_static', '/tf_static'),
                ]
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
                    robot['x'], robot['y'], '0',  # x y z
                    '0', '0', '0',                # roll pitch yaw
                    'world', f'{name}/odom'
                ],
                output='screen'
            )
        ])
        nodes.append(robot_group)

        # Bridge par robot
        # remappings ROS:
        #   /model/<name>/cmd_vel  →  /<name>/cmd_vel
        #   /model/<name>/odometry →  /<name>/odom
        #   /model/<name>/tf       →  /<name>/tf
        #   /model/<name>/joint_states → /<name>/joint_states

        robot_bridge = Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name=f'{name}_bridge',
            arguments=[
                # DiffDrive topics (Gazebo /model/<name>/...)
                f'/model/{name}/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
                f'/model/{name}/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
                f'/model/{name}/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
                # JointState (Gazebo Harmonic publie joint_state au singulier)
                f'/model/{name}/joint_state@sensor_msgs/msg/JointState[gz.msgs.Model',
                # Capteurs (déjà sous /<name>/...)
                f'/{name}/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
                f'/{name}/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            ],
            remappings=[
                (f'/model/{name}/cmd_vel', f'/{name}/cmd_vel'),
                (f'/model/{name}/odometry', f'/{name}/odom'),
                (f'/model/{name}/tf', '/tf'),
                (f'/model/{name}/joint_state', f'/{name}/joint_states'),
            ],
            parameters=[{'use_sim_time': True}],
            output='screen'
        )
        nodes.append(robot_bridge)

    # RViz
    rviz_config = os.path.join(pkg_share, 'rviz', 'multi_sim.rviz')
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )
    nodes.append(rviz)

    return LaunchDescription(nodes)
