-- ================================================================
-- industry_robot_2d.lua — Configuration Cartographer 2D
--
-- Adaptée au robot AMR industriel du projet Mobile-autonome-Robot-UDM-MIAR.
-- Basée sur la configuration de référence TurtleBot3 (turtlebot3_lds_2d.lua),
-- mais ajustée aux caractéristiques du robot :
--
--   ┌─────────────────────────────────────┬──────────────────┬──────────────────┐
--   │ Paramètre                           │ TurtleBot3       │ Industry Robot   │
--   ├─────────────────────────────────────┼──────────────────┼──────────────────┤
--   │ Portée LiDAR                        │ 0.12 – 3.5 m     │ 0.12 – 10.0 m    │
--   │ Empreinte robot                     │ ≈ 28 × 28 cm     │ 100 × 55 cm      │
--   │ Fréquence LiDAR                     │ 5 Hz             │ 10 Hz            │
--   │ Usage IMU                           │ true             │ true             │
--   └─────────────────────────────────────┴──────────────────┴──────────────────┘
--
-- Frames TF utilisées (cohérentes avec l'URDF) :
--   - map             : repère monde fixe (publié par Cartographer)
--   - odom            : repère odométrique (publié par DiffDrive Gazebo)
--   - base_footprint  : repère racine du robot
-- ================================================================

include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder        = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,

  -- Frames TF
  map_frame       = "map",
  tracking_frame  = "base_footprint",
  published_frame = "odom",
  odom_frame      = "odom",

  -- DiffDrive Gazebo publie déjà /odom et la TF odom→base_footprint.
  -- Cartographer NE DOIT PAS republier sa propre odométrie.
  provide_odom_frame            = false,
  publish_frame_projected_to_2d = true,
  use_pose_extrapolator         = true,
  use_odometry                  = true,
  use_nav_sat                   = false,
  use_landmarks                 = false,

  -- Capteurs : 1 LiDAR 2D
  num_laser_scans             = 1,
  num_multi_echo_laser_scans  = 0,
  num_subdivisions_per_laser_scan = 1,
  num_point_clouds            = 0,

  -- Périodes de publication
  lookup_transform_timeout_sec    = 0.2,
  submap_publish_period_sec       = 0.3,
  pose_publish_period_sec         = 5e-3,
  trajectory_publish_period_sec   = 30e-3,

  -- Taux d'échantillonnage (1.0 = tous les messages)
  rangefinder_sampling_ratio        = 1.0,
  odometry_sampling_ratio           = 1.0,
  fixed_frame_pose_sampling_ratio   = 1.0,
  imu_sampling_ratio                = 1.0,
  landmarks_sampling_ratio          = 1.0,
}

-- Mode 2D uniquement
MAP_BUILDER.use_trajectory_builder_2d = true

-- ============================================================
-- Adaptation au LiDAR du robot industriel (0.12-10 m)
-- TurtleBot3 utilise 0.12-3.5 m — on étend la plage maximale.
-- missing_data_ray_length doit être < max_range pour que
-- Cartographer insère des rayons "libre" dans les zones vides.
-- ============================================================
TRAJECTORY_BUILDER_2D.min_range             = 0.20
TRAJECTORY_BUILDER_2D.max_range             = 10.0
TRAJECTORY_BUILDER_2D.missing_data_ray_length = 9.0

-- IMU désactivé : le topic /imu n'est pas reçu par Cartographer en sim time.
-- L'odométrie DiffDrive + LiDAR suffisent pour le SLAM en entrepôt.
TRAJECTORY_BUILDER_2D.use_imu_data         = false

-- Filtre voxel : 0.05 m adapté à l'entrepôt (résolution carte 0.05 m)
TRAJECTORY_BUILDER_2D.voxel_filter_size    = 0.05

-- Corrélation temps-réel : améliore la précision en présence d'odométrie bruitée
TRAJECTORY_BUILDER_2D.use_online_correlative_scan_matching                           = true
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.linear_search_window        = 0.1
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.translation_delta_cost_weight = 10.0
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.rotation_delta_cost_weight  = 0.1

-- Filtre de mouvement : n'insère une pose que si le robot a tourné de > 0.2°
-- Évite la surcharge du graphe de poses en cas de déplacement linéaire lent.
TRAJECTORY_BUILDER_2D.motion_filter.max_angle_radians = math.rad(0.2)

-- ============================================================
-- Graphe de poses (fermeture de boucle + optimisation globale)
-- Seuils relevés vs TurtleBot3 car l'entrepôt est plus grand
-- et les scans couvrent davantage de distance.
-- ============================================================
POSE_GRAPH.constraint_builder.min_score                  = 0.65
POSE_GRAPH.constraint_builder.global_localization_min_score = 0.7
POSE_GRAPH.optimization_problem.huber_scale              = 1e2
POSE_GRAPH.optimize_every_n_nodes                        = 90

return options
