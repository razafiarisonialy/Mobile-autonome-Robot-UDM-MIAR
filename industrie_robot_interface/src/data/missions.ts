/**
 * Données statiques des missions logistiques AMR.
 * Miroir du fichier config/missions.yaml + config/stations.yaml du package ROS 2.
 */

export interface Station {
  id: string;
  label: string;
  description: string;
}

export interface Mission {
  id: string;
  name: string;
  description: string;
  icon: string;
  stations: string[];
  color: string;
}

/** Stations de l'entrepôt */
export const STATIONS: Record<string, Station> = {
  base_charge: {
    id: 'base_charge',
    label: 'Base de recharge',
    description: 'Point de départ et de retour',
  },
  matieres_premieres: {
    id: 'matieres_premieres',
    label: 'Matières premières',
    description: 'Zone de réception des bobines de papier',
  },
  poste_decoupe: {
    id: 'poste_decoupe',
    label: 'Poste découpe',
    description: 'Machines de découpe et rainurage',
  },
  controle_qualite: {
    id: 'controle_qualite',
    label: 'Contrôle qualité',
    description: "Station d'inspection des cartons finis",
  },
  expedition: {
    id: 'expedition',
    label: 'Expédition',
    description: "Quai d'expédition",
  },
};

/** Missions disponibles */
export const MISSIONS: Mission[] = [
  {
    id: 'approvisionnement',
    name: 'Approvisionnement',
    description: 'Collecte matières premières et acheminement vers la découpe',
    icon: '📦',
    stations: ['base_charge', 'matieres_premieres', 'poste_decoupe', 'base_charge'],
    color: '#4FC3F7',
  },
  {
    id: 'cycle_complet',
    name: 'Cycle Complet',
    description: 'Cycle de production complet de bout en bout',
    icon: '🔄',
    stations: ['matieres_premieres', 'poste_decoupe', 'controle_qualite', 'expedition', 'base_charge'],
    color: '#81C784',
  },
  {
    id: 'inspection_qualite',
    name: 'Inspection Qualité',
    description: "Ronde de contrôle qualité et expédition",
    icon: '🔍',
    stations: ['base_charge', 'controle_qualite', 'expedition', 'base_charge'],
    color: '#FFB74D',
  },
  {
    id: 'retour_base',
    name: 'Retour Base',
    description: "Retour d'urgence à la base de recharge",
    icon: '🏠',
    stations: ['base_charge'],
    color: '#E57373',
  },
];
