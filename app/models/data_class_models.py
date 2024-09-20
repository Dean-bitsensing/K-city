from dataclasses import dataclass, field
from typing import List
import numpy as np
import h5py, json
import math


@dataclass
class RadarObj:
        idx : int


@dataclass
class VisionObj:
    # Basic attributes
    id: int = 0
    class_id: int = 0
    confidence: float = 0.0

    # Bounding box attributes
    bbox_posx: int = 0
    bbox_posy: int = 0
    bbox_width: int = 0
    bbox_length: int = 0

    # Matching and status attributes
    match_robj_id: int = 0
    status: int = 0
    move_state: int = 0
    alive_age: int = 0

    # Position and velocity attributes
    posx: float = 0.0
    posy: float = 0.0
    velx: float = 0.0
    vely: float = 0.0

    # Size attributes
    width: float = 0.0
    length: float = 0.0

    # Additional attributes
    lane: int = 0
    heading_angle_deg: float = 0.0

    # Transformed position attributes
    trns_posx: float = 0.0
    trns_posy: float = 0.0
    ul_pos: List[float] = field(default_factory=lambda: [0.0, 0.0])
    ur_pos: List[float] = field(default_factory=lambda: [0.0, 0.0])
    dl_pos: List[float] = field(default_factory=lambda: [0.0, 0.0])
    dr_pos: List[float] = field(default_factory=lambda: [0.0, 0.0])

    # Visualization attributes
    selected: bool = False  # For changing color during display
    before_posx: float = 0.0
    before_posy: float = 0.0


@dataclass
class FusionObj:
    # Basic attributes
    id: int = 0
    status: int = 0
    update_state: int = 0  # Corrected typo from 'updata_state' to 'update_state'
    move_state: int = 0
    alive_age: int = 0

    # Position and velocity attributes
    posx: float = 0.0
    posy: float = 0.0
    ref_posx: float = 0.0
    ref_posy: float = 0.0
    velx: float = 0.0
    vely: float = 0.0

    # Additional attributes
    heading_angle_deg: float = 0.0
    power: float = 0.0
    width: float = 0.0
    length: float = 0.0
    class_id: int = 0
    fusion_type: int = 0
    fusion_age: int = 0
    match_vobj_id: int = 0

    # Transformed position attributes
    trns_posx: float = 0.0
    trns_posy: float = 0.0
    ul_pos: List[float] = field(default_factory=lambda: [0.0, 0.0])
    ur_pos: List[float] = field(default_factory=lambda: [0.0, 0.0])
    dl_pos: List[float] = field(default_factory=lambda: [0.0, 0.0])
    dr_pos: List[float] = field(default_factory=lambda: [0.0, 0.0])

    # Visualization attributes
    selected: bool = False  # For changing color during display
    before_posx: float = 0.0
    before_posy: float = 0.0

