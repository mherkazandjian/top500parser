"""
<keywords>
top, 500, hpc, post, process, data
</keywords>
<description>
Sample scrip that can be use to post process the data of the top 500 list for
all the releases.

In this script all the lists unqie operating systems are collected and printed

</description>
<seealso>
</seealso>
"""
import os
import pickle

# load the data of all the releases
fname = os.path.expanduser('~/tmp/top500.pkl')
with open(fname, 'rb') as fobj:
    all_release_info = pickle.load(fobj)


# collect the OSes into a set and then print them
unique_oses = set()
for release_date, release_info in all_release_info.items():
    print(f'release {release_date}')
    for system_rank, system_info in release_info.items():
        print(f"\trank = {system_rank} os = {system_info['Operating System']}")
        unique_oses.add(system_info['Operating System'])

print('-------------- unique oses -------------------')
for _os in unique_oses:
    print(_os)
