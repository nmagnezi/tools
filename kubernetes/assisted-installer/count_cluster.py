import json
import logging
import requests
import subprocess
import time

CLUSTERS_FILE = './data/clusters.json'
INFRAENV_FILE = './data/infraenvs.json'
HOSTS_FILE = './data/hosts.json'

PROD = 'https://api.openshift.com/api/assisted-install/v2'
STAGE = 'https://api.stage.openshift.com/api/assisted-install/v2'

URL = PROD
HOSTS_GET_ATTEMPTS = 3
DOWNLOAD_FILES = True
TOKEN = ''

LOG_DEBUG = False
LOG = logging.getLogger(__name__)




def configure_logger(debug_mode):
    logging.basicConfig(
        level=logging.DEBUG if debug_mode is True else logging.INFO,
        format='%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s'
    )


def get_token():
    if TOKEN:
        return TOKEN
    return subprocess.check_output('ocm token', shell=True).decode("utf-8")[:-1]


def load_json_from_file(file):
    with open(file, 'r') as openfile:
        json_object = json.load(openfile)
    return json_object


def get_clusters(url, download_files):
    if download_files:
        LOG.info("Downloading Clusters data...")
        clusters = requests.get(f'{url}/clusters', headers={'Authorization': f'Bearer {get_token()}'}).json()
        LOG.info("Done!")
        json_object = json.dumps(clusters, indent=4)
        with open(CLUSTERS_FILE, "w") as f:
            f.seek(0)
            f.write(json_object)
            f.truncate()
    clusters = load_json_from_file(CLUSTERS_FILE)
    return build_search_index_by_id(clusters)


def get_infraenvs(url, download_files):
    if download_files:
        LOG.info("Downloading InfraEnvs data...")
        infraenvs = requests.get(f'{url}/infra-envs/',
                                 headers={'Authorization': f'Bearer {get_token()}'}).json()
        LOG.info("Done!")
        json_object = json.dumps(infraenvs, indent=4)
        with open(INFRAENV_FILE, "w") as f:
            f.seek(0)
            f.write(json_object)
            f.truncate()
    return load_json_from_file(INFRAENV_FILE)


def get_hosts(url, download_files, infraenvs):
    infraenv_hosts = dict()
    if download_files:
        LOG.info("Downloading Hosts data. This might take a while...")
        for i, infraenv in enumerate(infraenvs):
            time.sleep(0.5)
            infraenv_id = infraenv["id"]
            attempts = 3
            hosts = []
            for j in range(HOSTS_GET_ATTEMPTS):
                try:
                    hosts = requests.get(f'{url}/infra-envs/{infraenv_id}/hosts',
                                         headers={'Authorization': f'Bearer {get_token()}'}).json()
                except requests.exceptions.RequestException:
                    LOG.debug(f"failed requesting hosts for infraenv {infraenv_id} - attempt ({j}/{attempts})")
                    continue
                break
            infraenv_hosts[infraenv['id']] = list()
            if not hosts:
                LOG.debug(f"adding infraenv ({i}/{len(infraenvs)}) {infraenv_id} has no hosts")
                continue
            for host in hosts:
                host_id = host['id']
                infraenv_hosts[infraenv['id']].append(host)
                LOG.debug(f"adding infraenv ({i}/{len(infraenvs)}) {infraenv_id} host {host_id}")
        LOG.info("Done!")
        json_object = json.dumps(infraenv_hosts, indent=4)
        with open(HOSTS_FILE, "w") as f:
            f.seek(0)
            f.write(json_object)
            f.truncate()
    return load_json_from_file(HOSTS_FILE)


def build_search_index_by_id(obj_list):
    return {obj["id"]: obj for obj in obj_list}


def build_static_network_config_mac_list(infraenv):
    json_object = json.loads(infraenv["static_network_config"])
    return [interface['mac_address'] for interface in json_object[0]['mac_interface_map']]


def build_hosts_inventory_mac_list(infraenv, hosts):
    mac_list = list()
    infraenv_id = infraenv['id']
    hosts_list = hosts.get(infraenv_id)
    if not hosts_list:
        return []
    for host in hosts_list:
        host_inventory = json.loads(host['inventory'])
        for interface in host_inventory['interfaces']:
            mac_list.append(interface['mac_address'])
    return mac_list


def compare_macs(infraenv, hosts):
    static_network_config_mac_list = build_static_network_config_mac_list(infraenv)
    static_network_config_mac_list = sorted(static_network_config_mac_list) if static_network_config_mac_list else []
    hosts_inventory_mac_list = build_hosts_inventory_mac_list(infraenv, hosts)
    static_network_config_mac_list = sorted(static_network_config_mac_list) if static_network_config_mac_list else []
    return static_network_config_mac_list == hosts_inventory_mac_list


if __name__ == '__main__':
    configure_logger(LOG_DEBUG)
    cluster_states = {'no_status': 0}
    count_static_network_configs = 0
    count_unbound_infraenvs = 0
    cluster_not_found = 0
    infra_env_with_no_hosts = 0
    covering_all_macs = 0

    clusters = get_clusters(URL, DOWNLOAD_FILES)
    infraenvs = get_infraenvs(URL, DOWNLOAD_FILES)
    hosts = get_hosts(URL, DOWNLOAD_FILES, infraenvs)

    # Process infraenvs
    for infraenv in infraenvs:
        static_network_config = infraenv.get('static_network_config')
        # Do not process infraenvs with no static_network_config
        if not(static_network_config and static_network_config != ''):
            continue

        count_static_network_configs += 1
        cluster_id = infraenv.get('cluster_id')

        if not(cluster_id and cluster_id != ''):
            count_unbound_infraenvs += 1
        else:  # Bounded infraenvs
            infraenv_cluster = clusters.get(cluster_id)
            if not infraenv_cluster:
                cluster_not_found += 1
                continue
            infraenv_cluster_status = infraenv_cluster.get('status')
            if not infraenv_cluster_status or infraenv_cluster_status == '':
                cluster_states['no_status'] += 1
            else:
                # Should not compare mac addresses for infraenvs with no hosts.
                if not hosts.get(infraenv['id']):
                    infra_env_with_no_hosts += 1
                else:
                    covering_all_macs += 1 if compare_macs(infraenv, hosts) else 0
                try:
                    cluster_states[infraenv_cluster_status] += 1
                except KeyError:
                    cluster_states[infraenv_cluster_status] = 1

    # Results
    LOG.info(f"found {len(clusters)} clusters and {len(infraenvs)} infraenvs total")
    LOG.info(f"found: {count_unbound_infraenvs} unbounded infraenvs")
    LOG.info(f"found: {cluster_not_found} infraenvs that point to a cluster that cannot be found\n")

    LOG.info(f"found {len(infraenvs)-count_static_network_configs} infraenvs without static_network_configs")
    LOG.info(f"found {count_static_network_configs} infraenvs with static_network_configs. breakdown by status:")
    LOG.info(cluster_states)
    LOG.info(f"found that out of {count_static_network_configs} infraenvs with static_network_configs"
             f" --> {covering_all_macs} covering all macs ; {infra_env_with_no_hosts} infraenv with no hosts")


