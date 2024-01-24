import numpy as np

experimentHash = {
    "exp": "rixx1003721",
    "location": "RixEndstation",
    "fluxSource": "MfxDg1BmMon",
    "fluxChannels": [11],
    "fluxSign": -1,
    "singlePixels": [
        [0, 150, 10],
        [0, 150, 100],
        [0, 275, 100],
        [0, 272, 66],
        [0, 280, 70],
        [0, 282, 90],
        [0, 270, 90],
        [0, 271, 90],
        [0, 272, 90],
        [0, 273, 90],
    ],
    "ROIs": ["XavierV4_2", "OffXavierV4_2"],
    "regionSlice": np.s_[270:288, 59:107],
}