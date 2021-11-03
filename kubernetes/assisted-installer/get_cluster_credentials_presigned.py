import argparse
import requests
import json

API_PREFIX = 'api/assisted-install/v2/'
API_ENDPOINT = 'downloads/credentials-presigned'


def process_args():
    parser = argparse.ArgumentParser(
        prog='get_cluster_credentials_presigned',
        add_help=True,
    )
    parser.add_argument(
        '-c', '--cluster_id',
        required=True,
        help='cluster uuid'
    )
    parser.add_argument(
        '-f', '--file_name',
        required=True,
        help='file name'
    )
    parser.add_argument(
        '-o_ip', '--object_store_ip',
        required=True,
        help='object store ip address'
    )
    parser.add_argument(
        '-o_p', '--object_store_port',
        required=False,
        default=9000,
        help='object store ip address'
    )
    parser.add_argument(
        '-svc_ip', '--assisted_svc_ip',
        required=True,
        help='object store ip address'
    )

    parser.add_argument(
        '-svc_p', '--assisted_svc_port',
        required=False,
        default=8090,
        help='object store ip address'
    )
    return parser.parse_args()


def get_presigned_url(cmd_line_args):
    svc_url = "http://{svc_ip}:{svc_port}/{api_prefix}/clusters/{cluster_id}/{api_endpoint}?file_name={filename}".format(
        svc_ip=cmd_line_args.assisted_svc_ip,
        svc_port=cmd_line_args.assisted_svc_port,
        api_prefix=API_PREFIX,
        cluster_id=cmd_line_args.cluster_id,
        api_endpoint=API_ENDPOINT,
        filename=cmd_line_args.file_name
    )
    res = requests.get(svc_url)
    content = json.loads(res.content)
    return content.get('url')


def get_auth_headers(url):
    headers = dict()
    raw_args = url.split('?')[1]
    args_list = raw_args.split('&')

    for arg in args_list:
        header_name = arg.split('=')[0]
        header_value = arg.split('=')[1]
        headers[header_name] = header_value
    return headers


def download_file(cmd_line_args, headers):
    url = 'http://{object_store_ip}:{object_store_port}/test/{cluster_id}/{filename}'.format(
        object_store_ip=cmd_line_args.object_store_ip,
        object_store_port=cmd_line_args.object_store_port,
        cluster_id=cmd_line_args.cluster_id,
        filename=cmd_line_args.file_name
    )
    res = requests.get(url=url, headers=headers)
    print(res.content)


if __name__ == '__main__':
    cmd_line_args = process_args()
    print('Got the following args:', cmd_line_args)
    url = get_presigned_url(cmd_line_args)
    headers = get_auth_headers(url)
    download_file(cmd_line_args,headers)
