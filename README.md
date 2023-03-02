# VM-disk-exclusions-checker-for-Rubrik-API

Rubrik Service Account is required:  
`https://<RUBRIK_IP>/web/bin/index.html#/user_management?tab=ServiceAccounts`

The script will check only local VMs and not replicated or relic VMs

Only disks where there are exclusions will be returned

The API playground can be used to review script actions which do the following:
1. Get list of all VMs and use the VM `"id"` for the next step:  
`https://<RUBRIK_IP>/docs/v1/playground/#/%2Fvmware%2Fvm/queryVm`

2. For each VM ID, list it's details and parse for `"virtualDiskIds"`  
`https://<RUBRIK_IP>/docs/v1/playground/#/%2Fvmware%2Fvm/getVm`

3. For each disk, check if `"excludeFromSnapshots"` is True  
`https://<RUBRIK_IP>/docs/v1/playground/#/%2Fvmware%2Fvm/getVirtualDisk`
