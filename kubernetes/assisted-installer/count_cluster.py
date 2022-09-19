import json
import requests
import subprocess
import pprint

CLUSTERS_FILE = './data/clusters.json'
INFRAENV_FILE = './data/infraenvs.json'

# prod
URL = 'https://api.openshift.com/api/assisted-install/v2'
# staging 
# URL = 'https://api.stage.openshift.com/api/assisted-install/v2'


def get_token():
    return subprocess.check_output('ocm token', shell=True).decode("utf-8")[:-1]


def load_json_from_file(file):
    with open(file, 'r') as openfile:
        json_object = json.load(openfile)
    return json_object


def get_clusters(url):
    print("Downloading Clusters data...")
    clusters = requests.get(f'{url}/clusters', headers={'Authorization': 'Bearer {}'.format(get_token())}).json()
    print("Done!")
    json_object = json.dumps(clusters, indent=4)
    with open(CLUSTERS_FILE, "w") as f:
        f.seek(0)
        f.write(json_object)
        f.truncate()
    return load_json_from_file(CLUSTERS_FILE)


def get_infraenvs(url):
    print("Downloading InfraEnvs data...")
    infraenvs = requests.get(f'{url}/infra-envs', headers={'Authorization': 'Bearer {}'.format(get_token())}).json()
    print("Done!")
    json_object = json.dumps(infraenvs, indent=4)
    with open(INFRAENV_FILE, "w") as f:
        f.seek(0)
        f.write(json_object)
        f.truncate()
    return load_json_from_file(INFRAENV_FILE)


def build_search_index_by_id(obj_list):
    return {obj["id"]: obj for obj in obj_list}


if __name__ == '__main__':
    count_static_network_configs = 0
    count_unbound_infraenvs = 0
    cluster_not_found = 0
    cluster_states = {'no_status': 0}
    clusters = get_clusters(URL)
    infraenvs = get_infraenvs(URL)

    clusters_search_index = build_search_index_by_id(clusters)

    for infraenv in infraenvs:
        static_network_config = infraenv.get('static_network_config')
        # Do not process infraenvs with no static_network_config
        if not(static_network_config and static_network_config != ''):
            continue

        count_static_network_configs += 1
        cluster_id = infraenv.get('cluster_id')

        if not(cluster_id and cluster_id != ''):
            count_unbound_infraenvs += 1
        else: # Bounded infraenvs
            infraenv_cluster = clusters_search_index.get(cluster_id)
            if not infraenv_cluster:
                cluster_not_found += 1
                continue
            infraenv_cluster_status = infraenv_cluster.get('status')
            if not infraenv_cluster_status or infraenv_cluster == '':
                cluster_states['no_status'] += 1
            else:
                try:
                    cluster_states[infraenv_cluster_status] += 1
                except KeyError:
                    cluster_states[infraenv_cluster_status] = 1
    print(f"found {len(clusters)} clusters and {len(infraenvs)} infraenvs total")
    print(f"found: {count_unbound_infraenvs} unbounded infraenvs")
    print(f"found: {cluster_not_found} infraenvs that point to a cluster that cannot be found\n")

    print(f"found {len(infraenvs)-count_static_network_configs} infraenvs without static_network_configs")
    print(f"found {count_static_network_configs} infraenvs with static_network_configs. breakdown by status:")
    pprint.pprint(cluster_states)

