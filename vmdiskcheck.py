# Script to check if VMware virtual disks are excluded.
# Rubrik Service Account is required https://<RUBRIK_IP>/web/bin/index.html#/user_management?tab=ServiceAccounts
# The script will check only local VMs and not replicated or relic VMs: Line #44
# Only disks where there are exclusions will be returned

import requests
import json
import urllib3

# NOTE: this disables warnings for insecure SSL/TLS connections to maintain clean terminal output for testing purposes only.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

rubrik_ip=input("Please enter Rubrik node IP: ")
user_id=input("Please enter User ID: ")
user_secret=input("Please enter Secret: ")

# Authenticate service account and return 24 hour token
open_session_url = f"https://{rubrik_ip}/api/v1/service_account/session"
open_session_headers = {
    "accept": "application/json",
    "authorization": f"apikey {user_secret}",
    "Content-Type": "application/json"
}
open_session_data = {
    "serviceAccountId": user_id,
    "secret": user_secret
}

try:
    open_session_response = requests.post(open_session_url, headers=open_session_headers, json=open_session_data, verify=False)
    if open_session_response.status_code == 200:
        user_token = open_session_response.json().get('token')
        print(f"\nToken for user is: \n{user_token}\nThis will be vlid for 24 hours or until session is closed\n")
    else:
        print(f"Request failed with status code {open_session_response.status_code}")
except Exception as e:
    print(f"An error occurred: {e}")


# Get list of VMs and their disks
vms_list_url = f"https://{rubrik_ip}/api/v1/vmware/vm?primary_cluster_id=local&is_relic=false&sort_by=name&sort_order=asc"
vms_list_headers = {
    "accept": "application/json",
    "authorization": f"Bearer {user_token}",
    "Content-Type": "application/json"
}

try:
    vm_details_reponse = requests.get(vms_list_url, headers=vms_list_headers, verify=False)
    if vm_details_reponse.status_code == 200:
        vm_details_json = json.loads(vm_details_reponse.content.decode('utf-8'))['data']
        for each_vm in vm_details_json:
            current_vm = dict(each_vm)
            
            # Get VM info for each VM in the dict
            vm_id = current_vm["id"]
            
            vm_info_url = f"https://{rubrik_ip}/api/v1/vmware/vm/{vm_id}"
            vm_info_headers = {
                "accept": "application/json",
                "authorization": f"Bearer {user_token}",
                "Content-Type": "application/json"
            }
            vm_info_reponse = requests.get(vm_info_url, headers=vm_info_headers, verify=False)
            vm_info_json = json.loads(vm_info_reponse.content.decode('utf-8'))
            
            # Get disk info for each disk per VM iteration
            vm_disks = dict(vm_info_json)["virtualDiskIds"]    
            #print(str(vm_disks) + "\n")
            for each_disk in list(vm_disks):
                #print(each_disk)
                            
                vm_disk_url = f"https://{rubrik_ip}/api/v1/vmware/vm/virtual_disk/{each_disk}"
                vm_disk_headers = {
                    "accept": "application/json",
                    "authorization": f"Bearer {user_token}",
                    "Content-Type": "application/json"
                }
                vm_disk_reponse = requests.get(vm_disk_url, headers=vm_disk_headers, verify=False)
                vm_disk_json = json.loads(vm_disk_reponse.content.decode('utf-8'))
                #print(vm_disk_json)
                if vm_disk_json["excludeFromSnapshots"]:
                    print("VM Name: " + current_vm["name"] + "\nVM ID: " + current_vm["id"] + "\nVM disk exclusions:")
                    print(f"{each_disk}\n")
                else:
                    pass
    else:
        print(f"Request failed with status code {vm_details_reponse.status_code}: {vm_details_reponse.text}")
except Exception as e:
    print(f"An error occurred: {e}")


# Close open sessions (Max sessions allowed per service account is 10)
close_sessions_url = f"https://{rubrik_ip}/api/v1/session/me"
close_sessions_headers = {
    "accept": "application/json",
    "authorization": f"Bearer {user_token}",
    "Content-Type": "application/json"
}

try:
    close_sessions__response = requests.delete(close_sessions_url, headers=close_sessions_headers, verify=False)
    if close_sessions__response.status_code == 204:
        print("\nSession was closed successfully")
    else:
        print(f"\nRequest failed with status code {close_sessions__response.status_code}")
except Exception as e:
    print(f"\nAn error occurred: {e}")