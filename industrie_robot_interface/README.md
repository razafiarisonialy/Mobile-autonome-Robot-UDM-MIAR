# Interface Robot Industriel — UDM MIAR

Interface web React + TypeScript pour piloter un robot mobile autonome via ROS 2.
Permet de déclencher des missions logistiques, visualiser l'état en temps réel et surveiller la navigation.

---

## Prérequis

- ROS 2 Humble
- Node.js 18+
- Package `rosbridge_server` (`sudo apt install ros-humble-rosbridge-server`)
- Package `industry_robot_mission` (dans ce dépôt)

---

## Lancement complet

Ouvrir **4 terminaux** dans l'ordre :

```bash
# Terminal 1 — Simulation + Navigation + RViz
ros2 launch industry_robot_navigation nav.launch.py

# Terminal 2 — Gestionnaire de missions
ros2 launch industry_robot_mission mission.launch.py

# Terminal 3 — WebSocket bridge (rosbridge)
ros2 launch rosbridge_server rosbridge_websocket_launch.xml

# Terminal 4 — Interface React
cd industrie_robot_interface
npm install
npm run dev
```

Accéder à l'interface : **http://localhost:5173**

---

## Calibration des stations

La calibration permet de définir les coordonnées exactes (x, y, yaw) de chaque station sur la carte.
Elle doit être refaite si la carte ou les positions physiques changent.

**Étape 1** — Lancer Nav2 :

```bash
ros2 launch industry_robot_navigation nav.launch.py
```

**Étape 2** — Lancer le script de calibration (nouveau terminal) :

```bash
ros2 run industry_robot_mission calibrate_stations.py
```

**Étape 3** — Dans RViz2, utiliser l'outil **"Nav2 Goal"** (flèche verte) :
- Cliquer et **glisser** sur la carte pour définir la position et l'orientation du robot
- Répéter pour chaque station

**Étape 4** — Dans le terminal de calibration, entrer le nom de la station quand demandé :

```
1 → base_charge
2 → matieres_premieres
3 → poste_decoupe
4 → controle_qualite
5 → expedition
c → nom personnalisé
s → ignorer cette pose
```

**Étape 5** — Terminer avec `Ctrl+C`. Le script affiche le YAML complet.

**Étape 6** — Copier le résultat dans :

```
industry_robot_mission/config/stations.yaml
```

---

## Missions disponibles

### approvisionnement

Collecte des matières premières et acheminement vers la découpe.

**Stations** : `base_charge → matieres_premieres → poste_decoupe → base_charge`

```bash
ros2 run industry_robot_mission send_mission.py --name approvisionnement
```

---

### cycle_complet

Cycle de production complet de bout en bout.

**Stations** : `matieres_premieres → poste_decoupe → controle_qualite → expedition → base_charge`

```bash
ros2 run industry_robot_mission send_mission.py --name cycle_complet
```

---

### inspection_qualite

Ronde de contrôle qualité et expédition.

**Stations** : `base_charge → controle_qualite → expedition → base_charge`

```bash
ros2 run industry_robot_mission send_mission.py --name inspection_qualite
```

---

### retour_base

Retour d'urgence à la base de recharge. Se déclenche aussi automatiquement après 2 échecs consécutifs.

**Stations** : `base_charge`

```bash
ros2 run industry_robot_mission send_mission.py --name retour_base
```

---

## Stations logistiques

| Station | X (m) | Y (m) | Description |
|---------|-------|-------|-------------|
| base_charge | 13.223 | -11.636 | Base de recharge — point de départ et de retour |
| matieres_premieres | 4.102 | -16.805 | Zone de réception des bobines de papier |
| poste_decoupe | 3.566 | 13.898 | Machines de découpe et rainurage |
| controle_qualite | -8.104 | 4.752 | Station d'inspection des cartons finis |
| expedition | -12.014 | -21.502 | Quai d'expédition |

---

## Interfaces ROS 2

| Interface | Type | Rôle |
|-----------|------|------|
| `/mission_manager/start_mission` | Service | Valide la mission avant exécution |
| `/mission_manager/execute_mission` | Action | Exécute la navigation station par station |
| `/mission_status` | Topic (String) | État courant de la mission |

---

## Architecture des fichiers

```
industry_robot_mission/
├── config/
│   ├── missions.yaml        # Définition des 4 missions
│   └── stations.yaml        # Coordonnées des 5 stations
├── launch/
│   └── mission.launch.py    # Lance le nœud mission_manager
├── scripts/
│   ├── mission_manager.py   # Nœud ROS 2 — orchestre les missions
│   ├── send_mission.py      # Client CLI pour déclencher une mission
│   └── calibrate_stations.py  # Outil interactif de calibration
├── action/
│   └── ExecuteMission.action
└── srv/
    └── StartMission.srv

industrie_robot_interface/    # Ce projet — interface React
```

---

## Développement

```bash
npm run dev      # Serveur de développement (HMR)
npm run build    # Build de production
npm run lint     # ESLint
```
