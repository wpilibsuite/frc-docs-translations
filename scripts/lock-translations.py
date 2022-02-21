import requests
import os
import argparse
import json
import configparser
import dateutil.parser
import dateutil.utils
import dateutil

TX_TOKEN = os.getenv("TX_TOKEN")
RESOURCES_URL = "https://rest.api.transifex.com/resources"
PROJECT_FILTER_PARAM = {"filter[project]": "o:wpilib:p:frc-docs"}
PROJECT_DELETE_PARAM = {"o:wpilib:p:frc-docs:r:"}  # resource slug appended to end

lock_json = {
    "data": {
        "attributes": {"accept_translations": False},
        "id": "",
        "type": "resources",
    }
}

headers = {
    "Authorization": f"Bearer {TX_TOKEN}",
    "Content-Type": "application/vnd.api+json",
}

details_param = {"details": ""}


def get_remote_resources():
    remote_request = requests.get(
        RESOURCES_URL, headers=headers, params=PROJECT_FILTER_PARAM
    )

    if remote_request.status_code != 200:
        print("Error retrieving remote resources", remote_request.status_code)
        exit(1)
    else:
        print("Successfully retrieved remote resources page 1!")

    data = remote_request.json()

    resources = {}
    for resource in data["data"]:
        resources[resource["attributes"]["slug"]] = resource

    pagination = 1
    while True:  # Exit if no more pages to paginate
        if data["links"]["next"] is None:
            break
        else:
            next_page = data["links"]["next"].split("page[cursor]=")[1]
            PROJECT_FILTER_PARAM.update({"page[cursor]": next_page})  # Begin pagination
            remote_request = requests.get(
                RESOURCES_URL, headers=headers, params=PROJECT_FILTER_PARAM
            )

            if remote_request.status_code != 200:
                print("Error retrieving remote resources", remote_request.status_code)
                exit(1)
            else:
                pagination += 1
                print(f"Successfully retrieved remote resources page {pagination}!")
                data = remote_request.json()
                for resource in data["data"]:
                    resources[resource["attributes"]["slug"]] = resource

    return resources


def get_local_resources(tx_config):
    config = configparser.ConfigParser()
    config.read(tx_config)

    resources = []
    for section in config.sections():
        section = section.split("frc-docs.", 1)

        # Eliminate the main configuration, and remote project identifier
        if section[0] == "main":
            continue
        else:
            resources.append(section[1])

    print("Successfully retrieved local resources!")

    return resources


def get_unused_resources(remote_resources, local_resources):
    unused_resources = {}
    for resource in remote_resources.keys():
        if resource not in local_resources:
            resource_data = remote_resources[resource]
            if not resource_data["attributes"]["accept_translations"]:
                last_update = dateutil.parser.parse(
                    resource_data["attributes"]["datetime_modified"]
                )
                current_time = dateutil.utils.today().replace(tzinfo=dateutil.tz.UTC)

                delete_status = (current_time - last_update).days >= 3
                if delete_status:
                    TEMP_RESOURCES_URL = RESOURCES_URL + "/" + resource_data["id"]
                    response = requests.delete(TEMP_RESOURCES_URL, headers=headers)

                    if response.status_code != 204:
                        print(
                            "Error deleting resource ", resource, response.status_code
                        )
                    else:
                        print("Successfully deleted old resource", resource)

                continue

            unused_resources[resource] = resource_data

    return unused_resources


def lock_resources(unused_resources):
    err = False
    for resource in unused_resources.keys():
        TEMP_RESOURCES_URL = RESOURCES_URL + "/" + unused_resources[resource]["id"]
        lock_json["data"]["id"] = unused_resources[resource]["id"]
        lock = json.dumps(lock_json)
        response = requests.patch(TEMP_RESOURCES_URL, headers=headers, data=lock)

        if response.status_code != 200:
            print("Error locking resource:", response, resource)
            print(response.content)
            err = True
        else:
            print("Successfully locked resource:", resource)

    if err:
        print("Script exited with problems!")
        exit(1)


def main():
    arg_parser = argparse.ArgumentParser(
        description="locks the unused files on Transifex"
    )
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


if __name__ == "__main__":
    main()
