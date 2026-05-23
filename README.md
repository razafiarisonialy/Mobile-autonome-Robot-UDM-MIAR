# Industry Robot — AMR Entrepôt de Cartonnerie

[![ROS 2](https://img.shields.io/badge/ROS%202-Jazzy%20Jalisco-blue)](https://docs.ros.org/en/jazzy/)
[![Gazebo](https://img.shields.io/badge/Gazebo-Harmonic-orange)](https://gazebosim.org/)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04%20LTS-purple)](https://ubuntu.com/)
[![Nav2](https://img.shields.io/badge/Nav2-Navigation%20Stack-brightgreen)](https://docs.nav2.org/)
[![SLAM](https://img.shields.io/badge/SLAM-Cartographer-red)](https://google-cartographer-ros.readthedocs.io/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE)

Robot Mobile Autonome (AMR) skid-steer 4 roues simulé sous Gazebo Harmonic, cartographié avec Cartographer SLAM et naviguant de façon autonome avec Nav2. Conçu pour un entrepôt de fabrication de cartons.

---

## Packages

| Package | Rôle |
|---------|------|
| `industry_robot_description` | URDF/Xacro, monde Gazebo, cartes SLAM |
| `industry_robot_sim` | Simulation mono-robot (Gazebo + bridge + LiDAR) |
| `industry_robot_multi_sim` | Simulation multi-robots (4 AMR) |
| `industry_robot_slam` | Cartographie 2D temps réel (Cartographer) |
| `industry_robot_navigation` | Navigation autonome Nav2 (AMCL + planification) |
| `industry_robot_mission` | Missions logistiques multi-stations |

---

## Robot

| Paramètre | Valeur |
|-----------|--------|
| Cinématique | Skid-steer, 4 roues motrices |
| Vitesse max | 1.0 m/s linéaire — 2.0 rad/s angulaire |
| Empreinte Nav2 | 106 × 86 cm |
| LiDAR | 360°, portée 0.12–10 m |
| Masse | ~66 kg |

---

## Installation

### 1. Prérequis

- Ubuntu 24.04 LTS
- [ROS 2 Jazzy](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)
- [Gazebo Harmonic](https://gazebosim.org/docs/harmonic/install_ubuntu/)

### 2. Dépendances

```bash
sudo apt install -y \
  ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge \
  ros-jazzy-robot-state-publisher ros-jazzy-joint-state-publisher \
  ros-jazzy-xacro ros-jazzy-rviz2 ros-jazzy-teleop-twist-keyboard \
  ros-jazzy-laser-filters ros-jazzy-turtlebot3-cartographer \
  ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-turtlebot3-navigation2
```

### 3. Cloner et compiler

```bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone https://github.com/razafiarisonialy/Mobile-autonome-Robot-UDM-MIAR.git
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

> Ajouter `source ~/ros2_ws/install/setup.bash` dans `~/.bashrc` pour ne pas le répéter.

---

## Lancement

### Simulation seule

```bash
ros2 launch industry_robot_sim sim.launch.py
```

### SLAM — Cartographier l'entrepôt

```bash
# Terminal 1
ros2 launch industry_robot_sim sim.launch.py

# Terminal 2
ros2 launch industry_robot_slam slam.launch.py

# Terminal 3 — téléopération clavier
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Sauvegarder la carte quand c'est terminé :

```bash
ros2 run nav2_map_server map_saver_cli -f \
  ~/ros2_ws/src/Mobile-autonome-Robot-UDM-MIAR/industry_robot_description/maps/warehouse
```

### Navigation autonome Nav2

```bash
ros2 launch industry_robot_navigation nav.launch.py
```

Dans RViz :
1. Attendre que tous les nœuds Nav2 soient **Active**
2. **"2D Pose Estimate"** → poser le robot sur la carte
3. **"Nav2 Goal"** → cliquer sur la destination

### Missions logistiques

```bash
# Terminal 1 — Nav2 (prérequis)
ros2 launch industry_robot_navigation nav.launch.py

# Terminal 2 — Mission manager
ros2 launch industry_robot_mission mission.launch.py

# Terminal 3 — Envoyer une mission
ros2 run industry_robot_mission send_mission.py --name approvisionnement
```

---

## Missions

### Missions disponibles

```bash
# Lister toutes les missions
ros2 run industry_robot_mission send_mission.py

# Déclencher une mission
ros2 run industry_robot_mission send_mission.py --name approvisionnement
ros2 run industry_robot_mission send_mission.py --name cycle_complet
ros2 run industry_robot_mission send_mission.py --name inspection_qualite
ros2 run industry_robot_mission send_mission.py --name retour_base
```

| Mission | Séquence |
|---------|---------|
| `approvisionnement` | base_charge → matieres_premieres → poste_decoupe → base_charge |
| `cycle_complet` | matieres_premieres → poste_decoupe → controle_qualite → expedition → base_charge |
| `inspection_qualite` | base_charge → controle_qualite → expedition → base_charge |
| `retour_base` | base_charge *(retour d'urgence automatique)* |

### Suivi en temps réel

```bash
ros2 topic echo /mission_status
```

### Comportements automatiques

| Situation | Réponse automatique |
|-----------|-------------------|
| Waypoint manqué | Réessai de la mission |
| 2 échecs consécutifs | Déclenchement de `retour_base` |
| Timeout (`nb_stations × 120s`) | Annulation Nav2 + `retour_base` |
| `FollowWaypoints` indisponible | Repli sur `NavigateThroughPoses` |

---

## Calibration des stations

Les coordonnées dans `config/stations.yaml` sont des **placeholders**. Voici comment les régler sur la vraie carte.

### Procédure

**Terminal 1** — Lancer Nav2 :
```bash
ros2 launch industry_robot_navigation nav.launch.py
```

**Terminal 2** — Lancer le calibreur :
```bash
ros2 run industry_robot_mission calibrate_stations.py
```

**Dans RViz** :
1. Sélectionner l'outil **"Nav2 Goal"** (flèche verte dans la barre d'outils)
2. **Cliquer + glisser** sur l'emplacement de la station
   - Le clic = position (x, y)
   - Le glisser = orientation du robot à l'arrivée (yaw)
3. Dans le terminal, taper le numéro de la station correspondante
4. Répéter pour les 5 stations

```
📍 Pose reçue depuis RViz :
   x   = -4.823 m
   y   =  7.956 m
   yaw =  0.0034 rad  (0.2°)

Noms de stations disponibles :
  [ ] 1. base_charge
  [ ] 2. matieres_premieres   ← taper 2
  [ ] 3. poste_decoupe
  [ ] 4. controle_qualite
  [ ] 5. expedition

Votre choix : 2
✓ Station "matieres_premieres" enregistrée.
```

**Ctrl+C** à la fin — le YAML complet s'affiche :

```yaml
stations:
  base_charge:
    x: 0.042
    y: 0.011
    yaw: 0.0012
  matieres_premieres:
    x: -4.823
    y: 7.956
    yaw: 0.0034
  ...
```

Copier ce bloc dans [industry_robot_mission/config/stations.yaml](industry_robot_mission/config/stations.yaml).

### Rebuild après modification

```bash
colcon build --packages-select industry_robot_mission
source install/setup.bash
```

> Avec `--symlink-install` (recommandé), le fichier YAML est modifiable directement sans rebuild.

---

## Topics principaux

| Topic | Type | Description |
|-------|------|-------------|
| `/cmd_vel` | `geometry_msgs/Twist` | Commande vitesse |
| `/odom` | `nav_msgs/Odometry` | Odométrie |
| `/scan_filtered` | `sensor_msgs/LaserScan` | LiDAR filtré (utilisé par Nav2) |
| `/map` | `nav_msgs/OccupancyGrid` | Carte d'occupation |
| `/mission_status` | `std_msgs/String` | Statut des missions |
| `/goal_pose` | `geometry_msgs/PoseStamped` | Objectif RViz → Nav2 |

### Diagnostic rapide

```bash
ros2 topic list                          # topics actifs
ros2 topic echo /mission_status          # statut mission
ros2 topic echo /goal_pose --once        # dernière pose RViz
ros2 run tf2_tools view_frames           # arbre TF
```

---

## Structure du projet

```
Mobile-autonome-Robot-UDM-MIAR/
├── industry_robot_description/    # URDF, monde, cartes
├── industry_robot_sim/            # Simulation mono-robot
├── industry_robot_slam/           # Cartographer SLAM
├── industry_robot_navigation/     # Stack Nav2
└── industry_robot_mission/        # Missions logistiques
    ├── config/
    │   ├── stations.yaml          # Coordonnées des stations
    │   └── missions.yaml          # Séquences de mission
    ├── scripts/
    │   ├── mission_manager.py     # Nœud principal
    │   ├── send_mission.py        # CLI de déclenchement
    │   └── calibrate_stations.py  # Outil de calibration
    ├── srv/StartMission.srv
    └── action/ExecuteMission.action
```
