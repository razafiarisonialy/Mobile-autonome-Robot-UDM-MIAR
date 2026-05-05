# 🤖 Industry Robot — Robot Mobile Autonome d'Entrepôt

[![ROS 2](https://img.shields.io/badge/ROS%202-Jazzy%20Jalisco-blue)](https://docs.ros.org/en/jazzy/)
[![Gazebo](https://img.shields.io/badge/Gazebo-Harmonic-orange)](https://gazebosim.org/)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04%20LTS-purple)](https://ubuntu.com/)
[![SLAM](https://img.shields.io/badge/SLAM-Cartographer-red)](https://google-cartographer-ros.readthedocs.io/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE)

Workspace ROS 2 complet pour la simulation et la cartographie d'un **robot mobile autonome (AMR)** destiné à un entrepôt de fabrication de cartons. Le robot est modélisé en Xacro modulaire, simulé sous Gazebo Harmonic, et cartographie son environnement via **Cartographer SLAM**.

### Packages du workspace

| Package | Description |
|---------|-------------|
| `industry_robot_description` | **Source centrale** — URDF/Xacro, configs, monde Gazebo (`worlds/`), cartes SLAM (`maps/`) |
| `industry_robot_sim` | Simulation mono-robot (Gazebo + bridge + filtrage LiDAR) |
| `industry_robot_multi_sim` | Simulation multi-robots (flotte de 4 AMR) |
| `industry_robot_slam` | SLAM 2D Cartographer (cartographie temps réel) |

> **Design inspiré** du TurtleBot3 Waffle et du robot industriel [Effidence EffiBOT](https://effidence.com/).

---

## 📐 Caractéristiques du Robot

| Élément | Dimensions | Détail |
|---------|-----------|--------|
| Châssis | 100 × 55 × 30 cm | Boîte rectangulaire, gris clair |
| Plateau cargo | 120 × 70 × 5 cm | Surélevé sur 4 piliers, blanc |
| 4 Roues motrices | Ø 25 cm, largeur 8 cm | Configuration Skid-steer (μ=0.9) |
| LiDAR 2D | Ø 4 cm × 4 cm | 360°, portée 0.12–10 m, sur le mât |
| IMU | 3 × 3 × 1 cm | Centre du châssis |
| Masse totale | ~62 kg | Budget réaliste pour AMR industriel |

**Cinématique** : Skid-steer (4 roues motrices)

**Vitesses max** : 1.0 m/s linéaire, 2.0 rad/s angulaire

### Éléments visuels (inspirés Effidence EffiBOT)
- 🔴 Bouton d'arrêt d'urgence (E-Stop) sur le mât
- 💡 2 phares LED jaunes à l'avant
- 🟢 Voyant LED de status
- 🛡️ Pare-chocs avant de protection
- 🔩 Rails latéraux garde-corps sur le plateau

---

## 🔧 Prérequis

- **OS** : Ubuntu 24.04 LTS (64-bit)
- **ROS 2** : Jazzy Jalisco
- **Simulateur** : Gazebo Harmonic (gz-sim 8)
- **Espace disque** : ~5 Go libres
- **Connexion internet** (pour l'installation initiale)

---

## 📦 Installation

### 1. Installer ROS 2 Jazzy

Suivre la [documentation officielle ROS 2 Jazzy](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html).

### 2. Installer Gazebo Harmonic

Suivre la procédure officielle : **[Install Gazebo Harmonic on Ubuntu](https://gazebosim.org/docs/harmonic/install_ubuntu/)**


### 3. Installer les dépendances ROS-Gazebo

```bash
sudo apt install -y \
  ros-jazzy-ros-gz-sim \
  ros-jazzy-ros-gz-bridge \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-joint-state-publisher \
  ros-jazzy-joint-state-publisher-gui \
  ros-jazzy-xacro \
  ros-jazzy-teleop-twist-keyboard \
  ros-jazzy-rviz2 \
  ros-jazzy-laser-filters \
  ros-jazzy-turtlebot3-cartographer \
  ros-jazzy-nav2-map-server
```

### 4. Cloner et compiler le projet

```bash
# Créer le workspace (si pas déjà fait)
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src

# Cloner le dépôt
git clone https://github.com/razafiarisonialy/Mobile-autonome-Robot-UDM-MIAR.git

# Compiler tous les packages
cd ~/ros2_ws
colcon build --symlink-install

# Sourcer l'environnement
source install/setup.bash
```

> 💡 **Astuce** : Ajoutez `source ~/ros2_ws/install/setup.bash` à votre `~/.bashrc` pour ne pas le refaire à chaque terminal.


---

## 🚀 Lancement

### Option 1 — Simulation Mono-Robot
Lance le robot dans un entrepôt avec ses capteurs et RViz.

```bash
ros2 launch industry_robot_sim sim.launch.py
```

### Option 2 — Simulation Multi-Robots (Flotte de 4 AMR)
Génère 4 robots avec isolation par namespaces (`/robot1` à `/robot4`).

```bash
ros2 launch industry_robot_multi_sim multi_sim.launch.py
```

### Option 3 — SLAM Cartographer (cartographie autonome)
Lance le SLAM en temps réel **en complément** de la simulation mono-robot.

**Terminal 1** — Simulation (si pas déjà lancée) :
```bash
ros2 launch industry_robot_sim sim.launch.py
```

**Terminal 2** — SLAM :
```bash
ros2 launch industry_robot_slam slam.launch.py
```

**Terminal 3** — Téléopération clavier :
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

**Sauvegarder la carte** une fois l'exploration terminée :
```bash
ros2 run nav2_map_server map_saver_cli -f ~/ros2_ws/src/Mobile-autonome-Robot-UDM-MIAR/industry_robot_description/maps/warehouse
```

---

## 🎮 Piloter le Robot

Dans un **nouveau terminal** (n'oubliez pas de sourcer) :

```bash
source ~/ros2_ws/install/setup.bash

# Si vous utilisez Option 1 (1 seul robot) :
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# Si vous utilisez Option 3 (Multi-robots, ex: contrôler robot1) :
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/robot1/cmd_vel
```

---

## 📊 Topics ROS 2 disponibles

| Topic | Type | Direction | Description |
|-------|------|-----------|-------------|
| `/cmd_vel` | `geometry_msgs/Twist` | ROS → GZ | Commande de vitesse |
| `/odom` | `nav_msgs/Odometry` | GZ → ROS | Odométrie du robot |
| `/scan` | `sensor_msgs/LaserScan` | GZ → ROS | Données LiDAR 360° (brutes) |
| `/scan_filtered` | `sensor_msgs/LaserScan` | ROS | Données LiDAR après filtrage (obstacles externes uniquement) |
| `/imu` | `sensor_msgs/Imu` | GZ → ROS | Accélérations et rotations |
| `/joint_states` | `sensor_msgs/JointState` | GZ → ROS | Position des roues (via `joint_state_publisher`) |
| `/tf` | `tf2_msgs/TFMessage` | GZ → ROS | Transformations TF |
| `/clock` | `rosgraph_msgs/Clock` | GZ → ROS | Horloge simulée |
| `/map` | `nav_msgs/OccupancyGrid` | SLAM → ROS | Carte d'occupation construite par Cartographer |

### Commandes utiles de diagnostic

```bash
# Lister tous les topics actifs
ros2 topic list

# Voir l'odométrie en temps réel
ros2 topic echo /odom

# Voir les données LiDAR brutes
ros2 topic echo /scan --once

# Voir les données LiDAR filtrées
ros2 topic echo /scan_filtered --once

# Visualiser l'arbre TF complet
ros2 run tf2_tools view_frames
```

---

## 🏭 Monde Gazebo — Usine de Cartons

Le fichier `industry_robot_description/worlds/warehouse.sdf` modélise une usine de fabrication de cartons (~40 m × 28 m) chargé par `sim.launch.py` et `multi_sim.launch.py`.

| Zone | Rayonnages | Couleur sol |
|------|-----------|-------------|
| Matières premières (ouest) | `aws_robomaker_warehouse_ShelfD_01` | Bleu |
| Semi-finis (centre) | `ctrazziwp/shelf` — fond plein, LiDAR-safe | Jaune |
| Produits finis (est) | `aws_robomaker_warehouse_ShelfF_01` | Vert |

Autres éléments : chariot élévateur (`OpenRobotics/Forklift`), palettes, colonnes structurelles (12), balises sol, flèches de circulation, zones de docking.

---

## 🗺️ SLAM — Cartographie de l'entrepôt

Le package `industry_robot_slam` implémente la **cartographie 2D en temps réel** via [Cartographer](https://google-cartographer-ros.readthedocs.io/), en s'inspirant de l'architecture `turtlebot3_cartographer` tout en l'adaptant au robot industriel.

### Architecture SLAM

```
/scan_filtered  ──►  cartographer_node  ──►  /map (OccupancyGrid)
/imu            ──►  (SLAM en temps réel)    /submap_list
/odom           ──►                          TF: map → odom
```

### Paramètres clés adaptés au robot industriel

| Paramètre | TurtleBot3 | Industry Robot | Raison |
|-----------|-----------|----------------|--------|
| `max_range` LiDAR | 3.5 m | **10.0 m** | LiDAR portée étendue |
| `missing_data_ray_length` | 3.0 m | **9.0 m** | Proportionnel à max_range |
| `voxel_filter_size` | 0.05 m | **0.05 m** | Résolution carte identique |
| `optimize_every_n_nodes` | 90 | **90** | Entrepôt = longues lignes droites |
| `min_score` fermeture boucle | 0.55 | **0.65** | Plus sélectif pour éviter faux positifs |

### Arguments du launch SLAM

| Argument | Défaut | Description |
|----------|--------|-------------|
| `use_sim_time` | `true` | Horloge Gazebo |
| `scan_topic` | `/scan_filtered` | Source LiDAR pour Cartographer |
| `resolution` | `0.05` | Résolution carte en m/cell |
| `publish_period_sec` | `1.0` | Période de publication de `/map` |
| `use_rviz` | `true` | Ouvrir RViz avec la config SLAM |

```bash
# Exemple : utiliser le scan brut à la place du scan filtré (débogage)
ros2 launch industry_robot_slam slam.launch.py scan_topic:=/scan

# Exemple : désactiver RViz (mode headless)
ros2 launch industry_robot_slam slam.launch.py use_rviz:=false
```

---

## 🔍 Filtrage LiDAR (anti self-detection)

Le robot détecte nativement ses propres surfaces dans le scan LiDAR brut (plateau cargo notamment). Deux couches de filtrage complémentaires sont en place :

| Couche | Mécanisme | Fichier concerné |
|--------|-----------|-----------------|
| **Filtre intrinsèque (URDF)** | `<collision>` retiré du `cargo_platform_link` → lien transparent au raycasting Gazebo | `urdf/robot_core.xacro` |
| **Filtre logiciel** | Nœud `scan_to_scan_filter_chain` (`laser_filters`) masquant une boîte 1.30 × 0.80 m autour du robot | `config/laser_filter.yaml` |

Le topic `/scan` (brut) reste disponible. Le topic `/scan_filtered` est produit par le filtre logiciel et doit être utilisé par Cartographer / Nav2.

Dans **RViz**, deux displays sont disponibles :
- 🔴 `/scan` — scan brut (rouge)
- 🟢 `/scan_filtered` — obstacles externes uniquement (vert)

