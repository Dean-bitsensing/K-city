from dataclasses import dataclass, field
import numpy as np

@dataclass
class Obj:
### Additional attributes which is not included in input and output

    info : str = '' # can be atm's ip or intersection name 
    associated : bool = False # attributes for fusion association and management
    associated_ip : str = ''

### From below oriented from input

    id: int = 0 # maximum 256

    status: int = 0 # ? 

    update_state: int = 0  # 0 -> invalid , 1 -> new , 2 -> updated
    move_state: int = 0    # 0 -> incalid , 1-> stopped , 2 -> moving

    alive_age: int = 0

    # Position and velocity attributes
    posx: float = 0.0
    posy: float = 0.0
    ref_posx: float = 0.0
    ref_posy: float = 0.0
    velx: float = 0.0
    vely: float = 0.0

    # Additional attributes

    # Radar
    heading_angle_deg: float = 0.0
    power: float = 0.0

    width: float = 0.0
    length: float = 0.0

    # Camera
    class_id: int = 0

    fusion_type: int = 0 # 1 -> Radar Only, 2 -> Camera Only, 3 -> Both
    fusion_age: int = 0

    
    
    # Need 3 more attributes


@dataclass
class TObj(Obj):
    deletion_age : int = 0
    associated_info: dict = field(default_factory=dict)  # mutable 기본값은 default_factory로 설정
    covariance: list = field(default_factory=lambda: np.array([[16, 0, 0, 0],
                                                               [0, 16, 0, 0],
                                                               [0, 0, 4, 0],
                                                               [0, 0, 0, 4]]))


                                     
 