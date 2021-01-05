import requests
import os
import argparse
import configparser
import dateutil.parser
import dateutil.utils

TX_TOKEN = os.getenv('TX_TOKEN')
RESOURCES_URL = 'https://www.transifex.com/api/2/project/frc-docs/resources/'
RESOURCE_BASE_URL = 'https://www.transifex.com/api/2/project/frc-docs/resource/'

lock_json = """
    {
        "accept_translations":"False"
    }
"""

headers = {"Content-type": "application/json"}

details_param = {"details":""}

def get_remote_resources():
    remote_request = requests.get(RESOURCES_URL, auth=('api', TX_TOKEN))

    if remote_request.status_code != 200:
        print("Error retrieving remote resources", remote_request.status_code)
        exit(1)
    else:
        print("Successfully retrieved remote resources!")

    resources = []
    for resource in remote_request.json():
        resources.append(resource['slug'])

    return resources


def get_local_resources(tx_config):
    config = configparser.ConfigParser()
    config.read(tx_config)
    
    resources = []
    for section in config.sections():
        section = section.split("frc-docs.", 1)
        
        # Eliminate the main configuration, and remote project identifier
        if section[0] == 'main':
            continue
        else:
            resources.append(section[1])

    print("Successfully retrieved local resources!")

    return resources


def get_unused_resources(remote_resources, local_resources):
    unused_resources = []
    for resource in remote_resources:
        if resource not in local_resources:
            response = requests.get(RESOURCE_BASE_URL + resource + "/",
                    params=details_param,
                    auth=("api", TX_TOKEN))

            if response.status_code != 200:
                print("Error retrieving information for resource:", resource)
                # prevent script from hanging on error
                continue
            elif response.status_code == 404:
                print("Resource not found!", resource)
                # deleted, no need to worry
                continue

            json_response = response.json()
            
            if not json_response["accept_translations"]:
                last_update = dateutil.parser.parse(json_response["last_update"])
                current_time = dateutil.utils.today()
                
                delete_status = (current_time - last_update).days >= 3

                if delete_status:
                    response = requests.delete(RESOURCE_BASE_URL + resource + "/",
                            auth=("api", TX_TOKEN))

                    if response.status_code != 204:
                        print("Error deleting resource ", resource, response.status_code)
                    else:
                        print("Successfully deleted old resource", resource)

                continue

            unused_resources.append(resource)

    return unused_resources


def lock_resources(unused_resources):
    err = False
    for resource in unused_resources:
        response = requests.put(RESOURCE_BASE_URL + resource + "/",
                    auth=("api", TX_TOKEN),
                    headers=headers,
                    data=lock_json)

        if response.status_code != 200:
            print("Error locking resource:", response, resource)
            err = True
        else:
            print("Successfully locked resource:", resource)

    if err:
        print("Script exited with problems!")
        exit(1)
        

def main():
    arg_parser = argparse.ArgumentParser(description="locks the unused files on Transifex")
    arg_parser.add_argument("tx_config_path", type=str, help="path to Transifex config")

    args = vars(arg_parser.parse_args())

    tx_config_path = args["tx_config_path"]
    
    print("Using TX Config Path:", tx_config_path)

    remote_resources = get_remote_resources()
    local_resources = get_local_resources(tx_config_path)

    unused_resources = get_unused_resources(remote_resources, local_resources)

    if len(unused_resources) == 0:
        print("All resources are locked or in use!")
    else:
        for resource in unused_resources:
            print("Unused resource:", resource)

        if os.getenv("CI"):
            lock_resources(unused_resources)
        else:
            print("Skipping lock because not running on CI")


if __name__ == '__main__':
    main()
