# 🤖 Industry Robot — Robot Mobile Autonome d'Entrepôt

[![ROS 2](https://img.shields.io/badge/ROS%202-Jazzy%20Jalisco-blue)](https://docs.ros.org/en/jazzy/)
[![Gazebo](https://img.shields.io/badge/Gazebo-Harmonic-orange)](https://gazebosim.org/)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04%20LTS-purple)](https://ubuntu.com/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE)

Package ROS 2 complet pour la simulation d'un **robot mobile autonome (AMR)** destiné à un entrepôt de fabrication de cartons. Le robot est modélisé en Xacro modulaire, simulé sous Gazebo Harmonic, et communique via le bridge `ros_gz_bridge`.

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

## 🏗️ Structure du Package

```
industry_robot/
├── CMakeLists.txt                      # Build system ament_cmake
├── package.xml                         # Manifeste et dépendances
├── urdf/
│   ├── warehouse_bot.urdf.xacro        # Fichier principal (inclusions)
│   ├── inertial_macros.xacro           # Macros d'inertie (box, cylinder, sphere)
│   ├── robot_core.xacro                # Corps du robot complet
│   ├── lidar.xacro                     # Capteur LiDAR 2D (gpu_lidar)
│   ├── imu.xacro                       # Centrale inertielle
│   └── gazebo_control.xacro            # Plugins DiffDrive + JointStatePublisher
├── launch/
│   ├── sim.launch.py                   # Simulation monde vide
│   └── display.launch.py              # Visualisation URDF seule (RViz)
├── config/
│   └── bridge.yaml                     # Mapping topics Gazebo ↔ ROS 2
└── rviz/
    └── view_robot.rviz                # Config RViz (robot, TF, LiDAR, odom)
```

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

```bash
sudo apt-get update
sudo apt-get install curl lsb-release gnupg

sudo curl https://packages.osrfoundation.org/gazebo.gpg \
  --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] \
  http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null

sudo apt-get update
sudo apt-get install gz-harmonic
```

> ⚠️ **Important** : Définir la variable d'environnement pour forcer la version Harmonic :
> ```bash
> echo 'export GZ_VERSION=harmonic' >> ~/.bashrc
> source ~/.bashrc
> ```

### 3. Installer les dépendances ROS-Gazebo

```bash
sudo apt install -y \
  ros-jazzy-ros-gz-sim \
  ros-jazzy-ros-gz-bridge \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-joint-state-publisher-gui \
  ros-jazzy-xacro \
  ros-jazzy-teleop-twist-keyboard \
  ros-jazzy-rviz2
```

### 4. Cloner et compiler le projet

```bash
# Créer le workspace (si pas déjà fait)
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src

# Cloner le dépôt
git clone https://github.com/razafiarisonialy/Mobile-autonome-Robot-UDM-MIAR.git

# Compiler
cd ~/ros2_ws
colcon build --packages-select industry_robot

# Sourcer l'environnement
source install/setup.bash
```

> 💡 **Astuce** : Ajoutez `source ~/ros2_ws/install/setup.bash` à votre `~/.bashrc` pour ne pas le refaire à chaque terminal.

### 5. Vérifier l'installation

```bash
gz sim --version    # Doit afficher Gazebo Sim 8.x
ros2 pkg list | grep industry_robot   # Doit afficher industry_robot
```

---

## 🚀 Lancement

### Option 1 — Visualisation du modèle URDF seul (sans Gazebo)

```bash
ros2 launch industry_robot display.launch.py
```

Ouvre **RViz** avec un slider GUI pour manipuler les roues. Idéal pour vérifier le modèle 3D et l'arbre TF.

### Option 2 — Simulation dans le monde par défaut (vide)

```bash
ros2 launch industry_robot sim.launch.py
```

Lance **Gazebo Harmonic** (monde vide) + **RViz** + le bridge ROS-Gazebo.

---

## 🎮 Piloter le Robot

Dans un **nouveau terminal** (n'oubliez pas de sourcer) :

```bash
source ~/ros2_ws/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

| Touche | Action |
|--------|--------|
| `i` | Avancer |
| `,` | Reculer |
| `j` | Tourner à gauche |
| `l` | Tourner à droite |
| `k` | Stop |
| `q`/`z` | Augmenter/diminuer vitesse |

---

## 📊 Topics ROS 2 disponibles

| Topic | Type | Direction | Description |
|-------|------|-----------|-------------|
| `/cmd_vel` | `geometry_msgs/Twist` | ROS → GZ | Commande de vitesse |
| `/odom` | `nav_msgs/Odometry` | GZ → ROS | Odométrie du robot |
| `/scan` | `sensor_msgs/LaserScan` | GZ → ROS | Données LiDAR 360° |
| `/imu` | `sensor_msgs/Imu` | GZ → ROS | Accélérations et rotations |
| `/joint_states` | `sensor_msgs/JointState` | GZ → ROS | Position des roues |
| `/tf` | `tf2_msgs/TFMessage` | GZ → ROS | Transformations TF |
| `/clock` | `rosgraph_msgs/Clock` | GZ → ROS | Horloge simulée |

### Commandes utiles de diagnostic

```bash
# Lister tous les topics actifs
ros2 topic list

# Voir l'odométrie en temps réel
ros2 topic echo /odom

# Voir les données LiDAR
ros2 topic echo /scan --once

# Visualiser l'arbre TF complet
ros2 run tf2_tools view_frames
```

---

## 🌳 Hiérarchie TF

```
odom (publié par DiffDrive)
 └── base_footprint
      └── base_link
           ├── chassis_link
           │    ├── cargo_platform_link
           │    │    ├── left_rail_link
           │    │    └── right_rail_link
           │    ├── front_mast_link
           │    │    ├── lidar_link
           │    │    ├── estop_link
           │    │    ├── left_head_light_link
           │    │    ├── right_head_light_link
           │    │    └── status_led_link
           │    ├── imu_link
           │    ├── front_bumper_link
           │    └── 4× support_post_links
           ├── front_left_wheel_link
           ├── front_right_wheel_link
           ├── rear_left_wheel_link
           └── rear_right_wheel_link
```

---

## 🖥️ Configuration WSL2 (Windows)

Si vous travaillez sous **Windows avec WSL2**, Gazebo peut nécessiter une configuration graphique supplémentaire.

### Vérifier et mettre à jour WSL

```powershell
# Dans PowerShell (admin)
wsl --version
wsl --shutdown
wsl --update
```

### Installer les outils graphiques

```bash
sudo apt install -y mesa-utils vulkan-tools
```

