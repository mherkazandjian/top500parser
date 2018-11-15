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
import pickle

# load the data of all the releases
with open('top500.pkl', 'rb') as fobj:
    all_release_info = pickle.load(fobj)


# collect the OSes into a set and then print them
unique_oses = set()
all_oses = []
for release_date, release_info in all_release_info.items():
    print(f'release {release_date}')
    for system_rank, system_info in release_info.items():
        print(f"\trank = {system_rank} os = {system_info['Operating System']}")
        unique_oses.add(system_info['Operating System'])
        all_oses.append(system_info['Operating System'])

print('-------------- unique oses -------------------')

print('windows OSes')
n_windows = 0
for _os in all_oses:
    __os = _os.lower()
    if 'win' in __os or 'microsoft' in __os:
        print('\t', _os.lower())
        n_windows += 1

print(f'found {n_windows} systems')
print('windows os = {:.3f}%'.format(100.0*n_windows / len(all_oses)))
