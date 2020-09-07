#%%
from neuralDX7.datasets import SingleVoiceLMDBDataset
from neuralDX7.constants import VOICE_PARAMETER_RANGES
from neuralDX7.utils import dx7_bulk_pack
import numpy as np
from tqdm import tqdm
from pronounceable import generate_word
from itertools import chain

print(VOICE_PARAMETER_RANGES.keys())

# group_by name, a number and others. corresponds to voice name, oscillator
# and global params respectively

groups = {
    "NAME": [],
    "0": [],
    "1": [],
    "2": [],
    "3": [],
    "4": [],
    "5": [],
    "GLOBAL": [],
}

for key in VOICE_PARAMETER_RANGES.keys():
    if "NAME" in key:
        groups["NAME"] += [key]
        continue
    if "_" in key:
        groups[key[0]] += [key]
        continue
    groups["GLOBAL"] += [key]



dataset = SingleVoiceLMDBDataset(**{
            'keys_file': 'unique_voice_keys.npy',
            'data_file': 'dx7-data.lmdb',
            'root':'~/agoge/artifacts/data',
            'data_size': 1.
        })

data = dataset.data

# for each voice extract all groups to their own matrices
grouped_parameters = {key: [] for key in groups}
for i, key in enumerate(tqdm(data.keys())):

    voice = data.get(key)['voice_params']
    
    for group, params in groups.items():
        grouped_parameters[group] += [voice[params]]

    # if i > 20: break

    

#%%
VOICE_DTYPE = [(a[2:], b) for a,b in grouped_parameters['0'][0].dtype.descr][:-1]
osc_voices = []
for i in range(6):
    osc_voices += [np.concatenate(grouped_parameters[f"{i}"]).astype(VOICE_DTYPE)]

osc_voices = np.concatenate(osc_voices)
combinables = {
    # "OSC": (osc_voices),
    "OSC": np.unique(osc_voices),
    # "GLOBAL": (np.concatenate(grouped_parameters["GLOBAL"])),
    "GLOBAL": np.unique(np.concatenate(grouped_parameters["GLOBAL"])),
}

# %%

from random import choices
VOICE_DTYPE = data.get(data.keys()[0])['voice_params'].dtype
def random_voice():

    oscs = choices(combinables["OSC"], k=6)
    globals_params = choices(combinables["GLOBAL"], k=1)
    name = [ord(i) for i in generate_word().ljust(10, " ")]

    arr = np.array([tuple(chain(*oscs, *globals_params, name))], dtype=VOICE_DTYPE)
    voice_dict = [arr[[key]].item()[0] for key in VOICE_DTYPE.names]
    return voice_dict

def random_cart():
    return list(map(lambda x: random_voice(), range(32)))
# /random_voice()
cart = dx7_bulk_pack(random_cart())
# %%
# import mido
# mido.write_syx_file('/home/nintorac/.local/share/DigitalSuburban/Dexed/Cartridges /doince.syx', [cart])
# %%
from agoge.lmdb_helper import LMDBDataset
from uuid import uuid4

def uuid():
    return uuid4().hex

db_env = LMDBDataset('voice-mixup.lmdb', readonly=False, map_size=180*1e6, max_dbs=2)
# glob_db = LMDBDataset('global-params.lmdb', readonly=False, map_size=40*1e6)
osc_db = 'oscillator'
glob_db = 'global'

for osc in tqdm(combinables['OSC']):
    db_env.put(uuid(), osc, db=osc_db)

for glob in tqdm(combinables['GLOBAL']):
    db_env.put(uuid(), glob, db=glob_db)
# %%>
