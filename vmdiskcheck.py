# Script to check if VMware virtual disks are excluded.

import requests
import json
import urllib3
import datetime
import sys
import getpass

# NOTE: this disables warnings for insecure SSL/TLS connections to maintain clean terminal output for testing purposes only.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create a unique filename based on the current date and time
result_text = "vmDiskExclusions_" + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt"

# User input
rubrik_ip=input("Please enter Rubrik node IP: ")
user_id=input("Please enter Service Account User ID: ")
user_secret=getpass.getpass("Please enter Service Account Secret: ")
print("\n")

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
        
        # move the cursor to the beginning of the line
        sys.stdout.write("\033[F")
        # clear the line
        sys.stdout.write("\033[K")
        
        for each_vm in vm_details_json:    
            
            current_vm = dict(each_vm)
            vm_output = {}
            
            # Get VM info for each VM in the response
            vm_id = current_vm["id"]
            vm_name = current_vm["name"]
            
            # Build new dictionary per VM
            vm_output["name"] = vm_name
            vm_output["vmId"] = vm_id
            disk_counter = 0
            excluded_disk_counter = 0
            
                    
            print(f"Checking VM: " + vm_name + " | " + vm_id)
            
            vm_info_url = f"https://{rubrik_ip}/api/v1/vmware/vm/{vm_id}"
            vm_info_headers = {
                "accept": "application/json",
                "authorization": f"Bearer {user_token}",
                "Content-Type": "application/json"
            }
            vm_info_reponse = requests.get(vm_info_url, headers=vm_info_headers, verify=False)
            vm_info_json = json.loads(vm_info_reponse.content.decode('utf-8'))
            
            # Get disk info for each disk per VM iteration from the response above
            vm_disks = dict(vm_info_json)["virtualDiskIds"]
            
            for each_disk in list(vm_disks):
                disk_counter += 1
                vm_output["diskCount"] = disk_counter
                
                vm_disk_url = f"https://{rubrik_ip}/api/v1/vmware/vm/virtual_disk/{each_disk}"
                vm_disk_headers = {
                    "accept": "application/json",
                    "authorization": f"Bearer {user_token}",
                    "Content-Type": "application/json"
                }
                vm_disk_reponse = requests.get(vm_disk_url, headers=vm_disk_headers, verify=False)
                vm_disk_json = json.loads(vm_disk_reponse.content.decode('utf-8'))
                
                if vm_disk_json["excludeFromSnapshots"]:
                    excluded_disk_counter += 1
                    vm_output["excludedDiskCount"] = excluded_disk_counter
                    vm_output[f"excludedDisk{excluded_disk_counter}"] = vm_disk_json
                else:
                    pass
                    
            if excluded_disk_counter > 0:
                with open(result_text, 'a', encoding='utf-8') as f:
                    f.write(str(vm_output) + "\n")
            
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")
    else:
        print(f"Request failed with status code {vm_details_reponse.status_code}: {vm_details_reponse.text}")
except Exception as e:
    print(f"An error occurred: {e}")

# Close open session
close_sessions_url = f"https://{rubrik_ip}/api/v1/session/me"
close_sessions_headers = {
    "accept": "application/json",
    "authorization": f"Bearer {user_token}",
    "Content-Type": "application/json"
}

try:
    close_sessions__response = requests.delete(close_sessions_url, headers=close_sessions_headers, verify=False)
    if close_sessions__response.status_code == 204:
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[K")
        print("\nSession was closed successfully")
        print(f"Result of the check can be found in file {result_text}\n")
    else:
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[K")
        print(f"\nRequest failed with status code {close_sessions__response.status_code}")
        print(f"Please try to close the session manually:")
        print(f"curl -s -X DELETE 'https://{rubrik_ip}/api/v1/session/me' -H 'accept: application/json' -H 'Authorization: Bearer {user_token}'")
except Exception as e:
    print(f"\nAn error occurred: {e}")