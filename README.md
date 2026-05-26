# 🤖 Industry Robot — Robot Mobile Autonome d'Entrepôt

[![ROS 2](https://img.shields.io/badge/ROS%202-Jazzy%20Jalisco-blue)](https://docs.ros.org/en/jazzy/)
[![Gazebo](https://img.shields.io/badge/Gazebo-Harmonic-orange)](https://gazebosim.org/)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04%20LTS-purple)](https://ubuntu.com/)
[![Nav2](https://img.shields.io/badge/Nav2-Navigation%20Stack-brightgreen)](https://docs.nav2.org/)
[![SLAM](https://img.shields.io/badge/SLAM-Cartographer-red)](https://google-cartographer-ros.readthedocs.io/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE)

Workspace ROS 2 complet pour la simulation, la cartographie et la **navigation autonome** d'un **robot mobile autonome (AMR)** destiné à un entrepôt de fabrication de cartons. Le robot est modélisé en Xacro modulaire, simulé sous Gazebo Harmonic, cartographie son environnement via **Cartographer SLAM**, et navigue de façon autonome grâce à **Nav2**.

### Packages du workspace

| Package | Description |
|---------|-------------|
| `industry_robot_description` | **Source centrale** — URDF/Xacro, configs, monde Gazebo (`worlds/`), cartes SLAM (`maps/`) |
| `industry_robot_sim` | Simulation mono-robot (Gazebo + bridge + filtrage LiDAR) |
| `industry_robot_multi_sim` | Simulation multi-robots (flotte de 4 AMR) |
| `industry_robot_slam` | SLAM 2D Cartographer (cartographie temps réel) |
| `industry_robot_navigation` | **Navigation autonome Nav2** (AMCL + planification + évitement d'obstacles) |

> **Design inspiré** de l'architecture industrielle **Husky A300** de Clearpath Robotics, agrémenté d'une touche académique distinctive (UDM MIAR).

---

## 📐 Caractéristiques du Robot

| Élément | Dimensions | Détail |
|---------|-----------|--------|
| Châssis | 90 × 54 × 25 cm | Boîte rectangulaire robuste |
| Pare-chocs AV/AR | 8 × 62 × 11 cm | Protection avant et arrière |
| 4 Roues motrices | Ø 33 cm, largeur 11.4 cm | Configuration Skid-steer type tout-terrain (μ=0.9) |
| Plateau supérieur | 82 × 48 × 4 cm | Fixé sur le châssis |
| Mât Capteurs | Ø 12 cm × 12 cm | Mât central tubulaire |
| LiDAR 2D | Ø 4 cm × 4 cm | 360°, portée 0.12–10 m, perché au sommet du mât |
| IMU | 3 × 3 × 1 cm | Intégré au centre du châssis |
| Rack de charge | 78 × 48 × 5 cm | Étagère de transport sur 4 piliers |
| Masse totale | ~66 kg | Budget réaliste pour AMR industriel |
| **Empreinte Nav2** | **106 × 86 cm** | Footprint rectangulaire (châssis + pare-chocs + roues) |

**Cinématique** : Skid-steer (4 roues motrices)

**Vitesses max** : 1.0 m/s linéaire, 2.0 rad/s angulaire


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
  ros-jazzy-navigation2 \
  ros-jazzy-nav2-bringup \
  ros-jazzy-turtlebot3-navigation2 \
  ros-jazzy-rosbridge-server
```

### 5. Cloner et compiler le projet

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

### Option 4 — Navigation Autonome (Nav2)
Lance la stack complète de navigation autonome style **TurtleBot3** :
Gazebo + Nav2 (AMCL, Planner, Controller, Behaviors) + RViz2.

**(La simulation sera lancée automatiquement par ce fichier launch)**

**Méthode A — Via le launch du projet (`nav.launch.py`) :**
```bash
ros2 launch industry_robot_navigation nav.launch.py
```

**Méthode B — Via le package TurtleBot3 (`navigation2.launch.py`) :**
```bash
ros2 launch industry_robot_navigation navigation2.launch.py
```
> La carte `warehouse.yaml` du projet est utilisée automatiquement.

> **Utilisation dans RViz** :
> 1. Attendez que tous les nœuds Nav2 soient en état **Active** (affiché dans le terminal).
> 2. Utilisez **« 2D Pose Estimate »** pour donner la position initiale du robot sur la carte.
> 3. Utilisez **« Nav2 Goal »** pour envoyer un objectif — le robot planifie et s'y rend en évitant les obstacles.


---

## 📍 Calibration des Stations

> **A faire avant la première mission**, ou après tout changement de carte ou de positions physiques.

La calibration définit les coordonnées exactes (x, y, yaw) de chaque station logistique sur la carte Gazebo.
Le résultat est sauvegardé dans `industry_robot_mission/config/stations.yaml`.

**Terminal 1** — Lancer la navigation (requis pour la carte et l'outil Nav2 Goal dans RViz) :

```bash
ros2 launch industry_robot_navigation nav.launch.py
```

**Terminal 2** — Lancer le script de calibration interactif :

```bash
ros2 run industry_robot_mission calibrate_stations.py
```

**Dans RViz2**, utiliser l'outil **"Nav2 Goal"** (flèche verte) :
- Cliquer et **glisser** sur la carte pour définir la position et l'orientation du robot sur la station cible
- Le script demande ensuite le nom de la station dans le terminal

**Dans le terminal de calibration**, choisir la station correspondante :

```
1 → base_charge
2 → matieres_premieres
3 → poste_decoupe
4 → controle_qualite
5 → expedition
c → nom personnalisé
s → ignorer cette pose
```

Répéter pour chaque station, puis **`Ctrl+C`** pour terminer.
Le script affiche le YAML complet à copier dans `industry_robot_mission/config/stations.yaml`.

---

## 🎯 Exécution des Missions

> **Prérequis** : avoir effectué la [calibration des stations](#-calibration-des-stations) au moins une fois.

Une fois que la simulation et la navigation autonome sont démarrées, vous avez **2 options** pour déclencher et suivre les missions logistiques (ex: `approvisionnement`, `cycle_complet`, `retour_base`, `inspection_qualite`) :

### 🛠️ Option 1 — Via la Ligne de Commande (CLI)
Idéal pour le diagnostic rapide et le test de fonctionnement direct.

1. **Démarrer le gestionnaire de missions** dans un terminal :
   ```bash
   ros2 launch industry_robot_mission mission.launch.py
   ```

2. **Déclencher une mission** dans un nouveau terminal :

   | Mission | Commande |
   |---------|---------|
   | Approvisionnement (matières premières → découpe) | `ros2 run industry_robot_mission send_mission.py --name approvisionnement` |
   | Cycle complet (production bout en bout) | `ros2 run industry_robot_mission send_mission.py --name cycle_complet` |
   | Inspection qualité (contrôle + expédition) | `ros2 run industry_robot_mission send_mission.py --name inspection_qualite` |
   | Retour base (urgence ou fin de mission) | `ros2 run industry_robot_mission send_mission.py --name retour_base` |

3. **Lister toutes les missions disponibles** :
   ```bash
   ros2 run industry_robot_mission send_mission.py
   ```

---

### 💻 Option 2 — Via l'Interface Web React (rosbridge)
Un tableau de bord moderne et interactif en mode sombre pour piloter le robot et suivre sa progression d'un simple clic !

1. **Lancer le WebSocket rosbridge** (pour connecter le navigateur web à ROS 2) :
   ```bash
   ros2 launch rosbridge_server rosbridge_websocket_launch.xml
   ```
   > [!NOTE]
   > Si le package `rosbridge_server` n'est pas encore installé sur votre système ROS 2 Jazzy, exécutez d'abord :  
   > `sudo apt update && sudo apt install ros-jazzy-rosbridge-server`

2. **Démarrer le gestionnaire de missions** (si pas déjà fait à l'étape précédente) :
   ```bash
   ros2 launch industry_robot_mission mission.launch.py
   ```

3. **Démarrer le dashboard React** :
   ```bash
   cd industrie_robot_interface
   npm run dev
   ```

4. **Accéder à l'interface** :
   - Ouvrez votre navigateur sur [http://localhost:5173](http://localhost:5173).
   - Le statut de connexion ROS 2 dans le header passera automatiquement au **vert** (🟢 Connecté).
   - Cliquez sur **Lancer la mission** sur n'importe quelle carte pour commander le robot et suivre en temps réel la progression grâce au terminal de logs intégré.

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
| `/map` | `nav_msgs/OccupancyGrid` | Nav2 → ROS | Carte d'occupation (chargée par `map_server`) |
| `/plan` | `nav_msgs/Path` | Nav2 | Chemin global planifié |
| `/local_plan` | `nav_msgs/Path` | Nav2 | Chemin local (DWB) |
| `/global_costmap/costmap` | `nav2_msgs/Costmap` | Nav2 | Carte de coût globale |
| `/local_costmap/costmap` | `nav2_msgs/Costmap` | Nav2 | Carte de coût locale |
| `/initialpose` | `geometry_msgs/PoseWithCovarianceStamped` | RViz → AMCL | Pose initiale (2D Pose Estimate) |
| `/goal_pose` | `geometry_msgs/PoseStamped` | RViz → Nav2 | Objectif de navigation (Nav2 Goal) |

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

# Vérifier l'état du lifecycle manager Nav2
ros2 lifecycle list /controller_server
ros2 lifecycle list /planner_server
```

---

## 🏭 Monde Gazebo — Usine de Cartons

Le fichier `industry_robot_description/worlds/tugbot_warehouse.sdf` modélise une usine de fabrication de cartons (~40 m × 28 m) chargé par `sim.launch.py` et `multi_sim.launch.py`.

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
|--------|-----------|--------------------|
| **Filtre intrinsèque (URDF)** | `<collision>` retiré du `cargo_platform_link` → lien transparent au raycasting Gazebo | `urdf/robot_core.xacro` |
| **Filtre logiciel** | Nœud `scan_to_scan_filter_chain` (`laser_filters`) masquant une boîte de 1.60 × 1.10 m autour du robot | `config/laser_filter.yaml` |

Le topic `/scan` (brut) reste disponible. Le topic `/scan_filtered` est produit par le filtre logiciel et doit être utilisé par Cartographer / Nav2.

Dans **RViz**, deux displays sont disponibles :
- 🔴 `/scan` — scan brut (rouge)
- 🟢 `/scan_filtered` — obstacles externes uniquement (vert)

---

## 🗺️ Navigation Autonome (Nav2)

Le package `industry_robot_navigation` intègre la stack complète **Nav2** (identique à l'approche **TurtleBot3**) pour permettre au robot de se déplacer de façon autonome dans l'entrepôt.

### Prérequis Navigation

```bash
# Identique à TurtleBot3
sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup
```

### Architecture de Navigation

```
                    ┌─────────────────────────────────────────────┐
                    │          BT Navigator (Behavior Tree)       │
                    │    navigate_to_pose_w_replanning_and_recovery│
                    └─────────┬──────────────┬───────────────┬────┘
                              │              │               │
                    ┌─────────▼──────┐ ┌─────▼────────┐ ┌────▼──────────┐
                    │ Planner Server │ │  Controller   │ │   Behavior    │
                    │  (NavFn / A*)  │ │  Server (DWB) │ │    Server     │
                    └────────┬───────┘ └──────┬────────┘ │ (Spin/Backup) │
                             │                │          └───────────────┘
                    ┌────────▼───────┐ ┌──────▼────────┐
                    │ Global Costmap │ │ Local Costmap  │
                    │  (static +     │ │ (rolling 3×3m) │
                    │   obstacle +   │ │                │
                    │   inflation)   │ │                │
                    └────────┬───────┘ └──────┬────────┘
                             │                │
                    ┌────────▼────────────────▼────────┐
                    │        /scan_filtered             │
                    │        /map (warehouse.yaml)      │
                    └─────────────────────────────────-─┘
```

### Paramètres clés Nav2

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| **Footprint** | `[[-0.53,-0.43], [-0.53,0.43], [0.53,0.43], [0.53,-0.43]]` | Empreinte réelle du robot (m) |
| **Inflation** | 0.75m, cost_scaling=3.0 | Zone de sécurité autour des obstacles |
| **Planificateur** | NavfnPlanner (Dijkstra) | Planification globale sur la carte |
| **Contrôleur** | DWB Local Planner | Suivi de chemin et évitement réactif |
| **Localisation** | AMCL (3000 particules) | Localisation par Monte Carlo sur la carte |
| **Recovery** | Spin, Backup, DriveOnHeading, Wait | Déblocage automatique |
| **Goal tolerance** | ±0.25m position, ±0.25rad orientation | Précision d'arrivée |

### Arguments du launch Navigation

**`nav.launch.py`**

| Argument | Défaut | Description |
|----------|--------|-------------|
| `use_sim` | `true` | Lancer Gazebo et utiliser l'horloge simulée |
| `use_rviz` | `true` | Lancer RViz2 avec la config navigation |
| `slam` | `false` | Mode SLAM Cartographer (true) ou AMCL + carte (false) |
| `map` | `warehouse.yaml` | Chemin vers la carte YAML |

**`navigation2.launch.py`** (interface TurtleBot3)

| Argument | Défaut | Description |
|----------|--------|-------------|
| `use_sim_time` | `true` | Horloge simulée (true) ou robot réel (false) |
| `use_sim` | `true` | Lancer Gazebo automatiquement |
| `slam` | `false` | Mode SLAM (true) ou localisation (false) |
| `map` | `warehouse.yaml` | Chemin vers la carte YAML |
| `params_file` | `nav2_params.yaml` | Override des paramètres Nav2 |