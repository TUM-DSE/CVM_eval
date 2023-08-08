from dataclasses import dataclass

# mt : iot (grouped), (unique triplet) env, device, mt_res
# NOTE: could replace w/ enums
@dataclass
class IotGroup():
    env: str
    device: str
    mt_res: int
