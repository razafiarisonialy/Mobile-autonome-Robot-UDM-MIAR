#!/usr/bin/env python3
"""
generate_warehouse.py — Génère un monde SDF d'entrepôt pour Gazebo Harmonic.

Peut être exécuté :
  - Directement :  python3 generate_warehouse.py
  - Via le launch : appelé automatiquement par sim.launch.py (une seule fois)

Modèles Gazebo Fuel :
  - Distribution_Warehouse (OpenRobotics)                : coque entrepôt
  - aws_robomaker_warehouse_ShelfD/E/F_01 (OpenRobotics) : racks
  - pallet_box_mobile (MovAi)                            : palettes
"""

import os
import argparse


def generate_warehouse_sdf(
    num_rows=4,
    shelves_per_row=3,
    pallet_count=4,
    output_path=None,
):
    """
    Génère un fichier SDF d'entrepôt avec racks et palettes.

    Args:
        num_rows:         nombre de rangées parallèles de racks
        shelves_per_row:  nombre de shelves bout à bout par rangée
        pallet_count:     nombre de palettes en zone de chargement
        output_path:      chemin du fichier .sdf à écrire

    Returns:
        Le chemin absolu du fichier généré.
    """
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), '..', 'worlds', 'warehouse.sdf')

    output_path = os.path.abspath(output_path)

    # ── En-tête SDF ──
    header = """\
<?xml version="1.0" ?>
<sdf version="1.9">
  <world name="warehouse_world">

    <!-- ===== Physique ===== -->
    <physics name="1ms" type="dart">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
      <real_time_update_rate>1000</real_time_update_rate>
    </physics>

    <!-- ===== Plugins Gazebo Harmonic ===== -->
    <plugin filename="gz-sim-physics-system"
            name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system"
            name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system"
            name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system"
            name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <plugin filename="gz-sim-contact-system"
            name="gz::sim::systems::Contact"/>
    <plugin filename="gz-sim-imu-system"
            name="gz::sim::systems::Imu"/>

    <!-- ===== Éclairage ===== -->
    <light type="directional" name="sun">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <direction>-0.3 0.1 -0.9</direction>
    </light>

    <!-- ===== Coque de l'entrepôt ===== -->
    <include>
      <name>Warehouse_Shell</name>
      <uri>https://fuel.gazebosim.org/1.0/OpenRobotics/models/Distribution_Warehouse</uri>
      <static>true</static>
      <pose>0 0 0 0 0 0</pose>
    </include>
"""

    # ── Variantes de racks ──
    shelf_variants = [
        "https://fuel.gazebosim.org/1.0/OpenRobotics/models/aws_robomaker_warehouse_ShelfD_01",
        "https://fuel.gazebosim.org/1.0/OpenRobotics/models/aws_robomaker_warehouse_ShelfE_01",
        "https://fuel.gazebosim.org/1.0/OpenRobotics/models/aws_robomaker_warehouse_ShelfF_01",
    ]

    shelf_template = """
    <include>
      <name>{name}</name>
      <uri>{uri}</uri>
      <static>true</static>
      <pose>{x} {y} 0 0 0 {yaw}</pose>
    </include>"""

    pallet_template = """
    <include>
      <name>{name}</name>
      <uri>https://fuel.gazebosim.org/1.0/MovAi/models/pallet_box_mobile</uri>
      <static>true</static>
      <pose>{x} {y} 0 0 0 {yaw}</pose>
    </include>"""

    footer = """
  </world>
</sdf>
"""

    # ── Paramètres de disposition ──
    #
    #   Rangée 0      Allée (3.5m)    Rangée 1      Allée (3.5m)    Rangée 2
    #  ┌────────┐                    ┌────────┐                    ┌────────┐
    #  │ shelf  │                    │ shelf  │                    │ shelf  │
    #  ├────────┤                    ├────────┤                    ├────────┤
    #  │ shelf  │     ← robot →     │ shelf  │     ← robot →     │ shelf  │
    #  ├────────┤                    ├────────┤                    ├────────┤
    #  │ shelf  │                    │ shelf  │                    │ shelf  │
    #  └────────┘                    └────────┘                    └────────┘

    aisle_width = 3.5
    shelf_width = 2.0
    shelf_length = 5.5
    shelf_gap_along_row = 0.5

    row_spacing = shelf_width + aisle_width
    step_along_row = shelf_length + shelf_gap_along_row

    total_width = (num_rows - 1) * row_spacing
    x_start = -total_width / 2.0
    total_length = (shelves_per_row - 1) * step_along_row
    y_start = -total_length / 2.0

    # ── Écriture ──
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(header)

        # --- Racks ---
        shelf_idx = 0
        for row in range(num_rows):
            x = x_start + row * row_spacing
            for col in range(shelves_per_row):
                y = y_start + col * step_along_row
                name = f"Shelf_R{row}_C{col}"
                uri = shelf_variants[shelf_idx % len(shelf_variants)]
                shelf_idx += 1
                # yaw = 1.5708 (90°) oriente les shelves le long de Y
                # Changer à 0.0 si les shelves sont perpendiculaires
                f.write(shelf_template.format(
                    name=name, x=x, y=y, yaw=1.5708, uri=uri
                ))

        # --- Palettes ---
        pallet_x = x_start - aisle_width - 1.0
        pallet_y_start = -3.0
        pallet_spacing_y = 2.5
        for i in range(pallet_count):
            y = pallet_y_start + i * pallet_spacing_y
            name = f"Pallet_{i}"
            f.write(pallet_template.format(name=name, x=pallet_x, y=y, yaw=0.0))

        f.write(footer)

    print(f"[generate_warehouse] Monde généré : {output_path}")
    print(f"  → {num_rows} rangées × {shelves_per_row} shelves, allées {aisle_width}m, {pallet_count} palettes")
    return output_path


# ── Exécution directe (optionnel) ──
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Génère un monde SDF d'entrepôt")
    parser.add_argument('--rows', type=int, default=4, help='Nombre de rangées de racks')
    parser.add_argument('--shelves', type=int, default=3, help='Shelves par rangée')
    parser.add_argument('--pallets', type=int, default=4, help='Nombre de palettes')
    parser.add_argument('-o', '--output', type=str, default=None, help='Chemin de sortie .sdf')
    args = parser.parse_args()

    generate_warehouse_sdf(
        num_rows=args.rows,
        shelves_per_row=args.shelves,
        pallet_count=args.pallets,
        output_path=args.output,
    )