"""
navigation2.launch.py — Utilise directement turtlebot3_navigation2

Prérequis :
  sudo apt install ros-jazzy-turtlebot3-navigation2

Utilisation :
  ros2 launch industry_robot_navigation navigation2.launch.py
  ros2 launch industry_robot_navigation navigation2.launch.py map:=$HOME/map.yaml
  ros2 launch industry_robot_navigation navigation2.launch.py slam:=true
  ros2 launch industry_robot_navigation navigation2.launch.py use_sim_time:=false map:=$HOME/map.yaml
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression


def generate_launch_description():
    desc_pkg = get_package_share_directory('industry_robot_description')
    nav_pkg  = get_package_share_directory('industry_robot_navigation')
    sim_pkg  = get_package_share_directory('industry_robot_sim')

    default_map    = os.path.join(desc_pkg, 'maps', 'warehouse.yaml')
    default_params = os.path.join(nav_pkg,  'config', 'nav2_params.yaml')

    map_yaml     = LaunchConfiguration('map')
    slam         = LaunchConfiguration('slam')
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_sim      = LaunchConfiguration('use_sim')

    declare_map = DeclareLaunchArgument(
        'map',
        default_value=default_map,
        description='Carte YAML du projet (défaut: warehouse.yaml) — ex: map:=$HOME/map.yaml'
    )
    declare_slam = DeclareLaunchArgument(
        'slam',
        default_value='false',
        description='Mode SLAM (true) ou localisation sur carte existante (false)'
    )
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Horloge simulée Gazebo (true) ou robot réel (false)'
    )
    declare_use_sim = DeclareLaunchArgument(
        'use_sim',
        default_value='true',
        description='Lancer Gazebo automatiquement (seulement si use_sim_time:=true)'
    )

    # ── Gazebo (uniquement si use_sim_time:=true ET use_sim:=true) ──
    # PythonExpression : ROS2 évalue en Python — "true"/"false" ne sont PAS des
    # booléens Python. On utilise une comparaison de chaînes explicite.
    launch_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(sim_pkg, 'launch', 'sim.launch.py')
        ),
        condition=IfCondition(
            PythonExpression(['"', use_sim_time, '" == "true" and "', use_sim, '" == "true"'])
        )
    )

    # turtlebot3_navigation2 utilise PythonExpression([slam, ' and ', ...])
    # → eval('false and True') → NameError. Il faut 'False'/'True' (Python).
    # On normalise : 'true'/'True'/'1' → 'True', tout le reste → 'False'.
    slam_py = PythonExpression(
        ['"True" if "', slam, '" in ["true", "True", "1"] else "False"']
    )

    # ── TurtleBot3 navigation2 (lève une erreur claire si non installé) ──
    try:
        tb3_nav_pkg = get_package_share_directory('turtlebot3_navigation2')
        tb3_navigation = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(tb3_nav_pkg, 'launch', 'navigation2.launch.py')
            ),
            launch_arguments={
                'map':             map_yaml,
                'slam':            slam_py,
                'use_sim_time':    use_sim_time,
                'params_file':     default_params,
                'use_composition': 'False',
            }.items()
        )
    except Exception:
        raise RuntimeError(
            '\n\n[navigation2.launch.py] Le package turtlebot3_navigation2 est introuvable.\n'
            'Installez-le avec :\n'
            '  sudo apt install ros-jazzy-turtlebot3-navigation2\n'
        )

    # turtlebot3_navigation2 lit os.environ['TURTLEBOT3_MODEL'] directement.
    # La valeur n'a aucun effet sur notre robot (nos params surchargent tout)
    # mais la variable doit exister pour que le package ne plante pas.
    set_tb3_model = SetEnvironmentVariable('TURTLEBOT3_MODEL', 'burger')

    return LaunchDescription([
        set_tb3_model,
        declare_map,
        declare_slam,
        declare_use_sim_time,
        declare_use_sim,
        launch_gazebo,
        tb3_navigation,
    ])
