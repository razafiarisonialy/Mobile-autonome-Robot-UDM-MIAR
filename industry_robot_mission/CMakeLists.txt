cmake_minimum_required(VERSION 3.8)
project(industry_robot_mission)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Dépendances de construction
find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(nav2_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(action_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)

# Génération des interfaces personnalisées (service + action)
rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/StartMission.srv"
  "action/ExecuteMission.action"
  DEPENDENCIES builtin_interfaces std_msgs geometry_msgs action_msgs
)

ament_export_dependencies(rosidl_default_runtime)

# Installation des scripts Python exécutables
install(PROGRAMS
  scripts/mission_manager.py
  scripts/send_mission.py
  scripts/calibrate_stations.py
  DESTINATION lib/${PROJECT_NAME}
)

# Installation des répertoires de ressources partagées
# Sans slash final sur config/launch : CMake installe le dossier lui-même,
# créant share/industry_robot_mission/config/ et share/industry_robot_mission/launch/
install(DIRECTORY
  config
  launch
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
