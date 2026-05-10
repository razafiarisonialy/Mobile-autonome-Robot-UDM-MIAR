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

    use_sim = LaunchConfiguration('use_sim')
    
    # 1. Argument to toggle simulation
    declare_use_sim = DeclareLaunchArgument('use_sim', default_value='true')

    # Paths
    params_file = os.path.join(nav_pkg, 'config', 'nav2_params.yaml')
    # Note: Make sure you save a 'nav.rviz' in your nav package!
    rviz_config = os.path.join(nav_pkg, 'rviz', 'nav.rviz') 

    # 2. Include the Sim launch (Gazebo + Robot State + Laser Filter)
    # This fulfills your requirement to not duplicate sim logic
    launch_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(sim_pkg, 'launch', 'sim.launch.py')
        ),
        launch_arguments={'use_sim': use_sim}.items(),
        condition=IfCondition(use_sim)
    )

    # 3. Nav2 Nodes
    # We use a helper list to keep the Lifecycle Manager clean
    nav_nodes = ['map_server', 'amcl', 'planner_server', 'controller_server', 'behavior_server', 'bt_navigator']
    
    # Map Server (Points to your description package as requested)
    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        parameters=[params_file, {'yaml_filename': os.path.join(desc_pkg, 'maps', 'map.yaml')}]
    )

    amcl = Node(package='nav2_amcl', executable='amcl', parameters=[params_file])
    planner = Node(package='nav2_planner', executable='planner_server', parameters=[params_file])
    controller = Node(package='nav2_controller', executable='controller_server', parameters=[params_file])
    behavior_server = Node(package='nav2_behaviors', executable='behavior_server', parameters=[params_file])
    bt_nav = Node(package='nav2_bt_navigator', executable='bt_navigator', parameters=[params_file])

    # 4. Lifecycle Manager
    lifecycle_mgr = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        parameters=[{'autostart': True, 'node_names': nav_nodes}]
    )

    # 5. Navigation RViz
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        declare_use_sim,
        launch_sim,
        map_server,
        amcl,
        planner,
        controller,
        behavior_server,
        bt_nav,
        lifecycle_mgr,
        rviz
    ])