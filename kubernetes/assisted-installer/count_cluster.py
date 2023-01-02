import json
import logging
import requests
import pprint
import subprocess
import time

CLUSTERS_FILE = './data/clusters.json'
INFRAENV_FILE = './data/infraenvs.json'
HOSTS_FILE = './data/hosts.json'

PROD = 'https://api.openshift.com/api/assisted-install/v2'
STAGE = 'https://api.stage.openshift.com/api/assisted-install/v2'

URL = PROD
HOSTS_GET_ATTEMPTS = 3
DOWNLOAD_FILES = False
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


def get_dhcp_interfaces_macs_list(infraenv, hosts, static_network_config_mac_list):
    result = list()
    infraenv_id = infraenv['id']
    hosts_list = hosts.get(infraenv_id)
    if not hosts_list:
        return []
    for host in hosts_list[0:2]:
        host_inventory = json.loads(host['inventory'])
        for interface in host_inventory['interfaces']:
            if ((interface.get('ipv4_addresses') or interface.get('ipv6_addresses')) and interface['mac_address']
                    not in static_network_config_mac_list):
                result.append(interface['mac_address'])
    return result


def mixed_network_config(infraenv, hosts):
    static_network_config_mac_list = build_static_network_config_mac_list(infraenv)
    if not static_network_config_mac_list:
        return False
    hosts_dhcp_interfaces_mac_list = get_dhcp_interfaces_macs_list(infraenv, hosts, static_network_config_mac_list)
    if hosts_dhcp_interfaces_mac_list:
        LOG.debug(f"infraenv {infraenv['id']}, has hosts with both nmstate and interfaces that got an IP via dhcp."
                  f" MAC Addresses: {hosts_dhcp_interfaces_mac_list}")
    return bool(hosts_dhcp_interfaces_mac_list)

def update_cluster_stats(stats, infraenv_cluster_status):
    try:
        stats[infraenv_cluster_status] += 1
    except KeyError:
        stats[infraenv_cluster_status] = 1


def no_mac_coverage_user_list(stats, user_types, infraenv):
    if '@' in infraenv['user_name']:
        key = infraenv['user_name']
    else:
        key = f"{infraenv['user_name']}@{infraenv['email_domain']}"

    if 'redhat' in key:
        user_types['redhat'] +=1
    elif 'ibm' in key:
        user_types['ibm'] += 1
    else:
        user_types['external'] += 1

    try:
        stats[key] += 1
    except KeyError:
        stats[key] = 1


def nmstate_stats(clusters, infraenvs, hosts):
    cluster_states = {'no_status': 0}
    covering_all_macs_cluster_states = {'no_status': 0}
    covering_not_all_macs_cluster_states = {'no_status': 0}

    user_types = {'redhat': 0, 'ibm': 0, 'external': 0}

    not_covering_all_macs_user_states = dict()
    count_static_network_configs = 0
    count_unbound_infraenvs = 0
    cluster_not_found = 0
    infra_env_with_no_hosts = 0
    covering_all_macs = 0
    not_covering_all_macs = 0
    clusters_with_nmstate_and_dhcp = 0

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
                    if compare_macs(infraenv, hosts):
                        covering_all_macs += 1
                        update_cluster_stats(covering_all_macs_cluster_states, infraenv_cluster_status)
                    else:
                        not_covering_all_macs += 1
                        update_cluster_stats(covering_not_all_macs_cluster_states, infraenv_cluster_status)
                        no_mac_coverage_user_list(not_covering_all_macs_user_states, user_types, infraenv)
                        if mixed_network_config(infraenv, hosts):
                            clusters_with_nmstate_and_dhcp += 1

                update_cluster_stats(cluster_states, infraenv_cluster_status)

    # Results
    LOG.info(f"found {len(clusters)} clusters and {len(infraenvs)} infraenvs total")
    LOG.info(f"found: {count_unbound_infraenvs} unbounded infraenvs")
    LOG.info(f"found: {cluster_not_found} infraenvs that point to a cluster that cannot be found\n")

    LOG.info(f"found {len(infraenvs)-count_static_network_configs} infraenvs without static_network_configs")
    LOG.info(f"found {count_static_network_configs} infraenvs with static_network_configs. breakdown by status:")
    pprint.pprint(cluster_states)
    LOG.info(f"found that out of {count_static_network_configs} infraenvs with static_network_configs"
             f" --> {covering_all_macs} covering all macs ; {infra_env_with_no_hosts} infraenv with no hosts")
    LOG.info(f"out of {count_static_network_configs-covering_all_macs-infra_env_with_no_hosts} infraenvs with hosts "
             f"and static_network_configs partial mac coverage, found that {clusters_with_nmstate_and_dhcp} "
             f"infraenvs mix both static_network_configs and dhcp.")
    LOG.info(f"found {covering_all_macs} infraenvs with static_network_configs and covering all macs."
             f" breakdown by status:")
    pprint.pprint(covering_all_macs_cluster_states)
    LOG.info(f"found {not_covering_all_macs} Infraenvs with no full mac address coverage. breakdown by status:")
    pprint.pprint(covering_not_all_macs_cluster_states)
    LOG.info("user types:")
    pprint.pprint(user_types)
    LOG.info("Breakdown by users and infraenv count")
    pprint.pprint(not_covering_all_macs_user_states)


def config_has_bonds(static_network_config):
    if not static_network_config:
        return False
    if 'bond' in static_network_config:
        return True
    return False


def mixed_bonds_base_on_hosts_inventory(infraenv, hosts):
    infraenv_id = infraenv['id']
    hosts_list = hosts.get(infraenv_id)
    if not hosts_list:
        return []

    print(infraenv_id)
    roles = set()

    for host in hosts_list:
        host_inventory = json.loads(host['inventory'])
        interface_types = set()
        roles.add(host['role'])
        for interface in host_inventory['interfaces']:
            interface_types.add(interface['type'])


        if host['role'] == 'master' and 'bond' in interface_types:
            return False
        if host['role'] == 'worker' and 'bond' not in interface_types:
            return False

    if 'worker' in roles and 'master' in roles:
        LOG.info(f"infraenv {infraenv_id} has a mixed config")
        hosts_list = hosts.get(infraenv_id)
        for host in hosts_list:
            host_inventory = json.loads(host['inventory'])
            for interface in host_inventory['interfaces']:
                LOG.info(f"host {host['id']}: role {host['role']} interface {interface['type']} with mtu {interface['mtu']}")

    return 'worker' in roles and 'master' in roles


def bond_mix(clusters, infraenvs, hosts):
    cluster_states = {'no_status': 0}
    no_bonds = 0
    count_static_network_configs = 0
    count_unbound_infraenvs = 0
    cluster_not_found = 0
    infraenvs_mixed_bonds = 0

    # Process infraenvs
    for infraenv in infraenvs:
        static_network_config = infraenv.get('static_network_config')

        # Do not process infraenvs with no static_network_config
        if not (static_network_config and static_network_config != ''):
            continue

        count_static_network_configs += 1

        if not config_has_bonds(static_network_config):
            no_bonds += 1
            continue

        cluster_id = infraenv.get('cluster_id')

        if not (cluster_id and cluster_id != ''):
            count_unbound_infraenvs += 1
            continue

        infraenv_cluster = clusters.get(cluster_id)
        if not infraenv_cluster:
            cluster_not_found += 1
            continue

        if not mixed_bonds_base_on_hosts_inventory(infraenv, hosts):
            continue


        infraenvs_mixed_bonds += 1

        infraenv_cluster_status = infraenv_cluster.get('status')

        if not infraenv_cluster_status or infraenv_cluster_status == '':
            cluster_states['no_status'] += 1
        else:
            update_cluster_stats(cluster_states, infraenv_cluster_status)

    LOG.info(f"found: {count_unbound_infraenvs} unbounded infraenvs")
    LOG.info(f"found: {cluster_not_found} infraenvs that point to a cluster that cannot be found\n")
    LOG.info(f"found {len(infraenvs) - count_static_network_configs} infraenvs without static_network_configs")
    LOG.info(f"found {count_static_network_configs} infraenvs with static_network_configs. Out of which "
             f"{count_static_network_configs-no_bonds} with bonds and "
             f"{no_bonds} infraenvs with no bonds.")

    LOG.info(f"found {infraenvs_mixed_bonds} infraenvs with mixed bonds config")
    pprint.pprint(cluster_states)


if __name__ == '__main__':
    configure_logger(LOG_DEBUG)
    clusters = get_clusters(URL, DOWNLOAD_FILES)
    infraenvs = get_infraenvs(URL, DOWNLOAD_FILES)
    hosts = get_hosts(URL, DOWNLOAD_FILES, infraenvs)

    bond_mix(clusters, infraenvs, hosts)
