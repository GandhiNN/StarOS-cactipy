#!/usr/bin/env python3
#
# author == __gandhi__
# ngakan.gandhi@packet-systems.com

import pexpect
import sys
import os
import json
import time
import re

# Load node user and password configuration file
def load_node_config(node_config_file):
    with open(node_config_file) as node_confile:
        return json.load(node_confile)

def get_node_user_pass(node_config):
    node = sys.argv[1].upper()
    user = ''
    password = ''
    user = node_config[node]['user']
    password = node_config[node]['password']
    return user, password    

def get2gAttachSrStats(node_expect, ip_address, user, password):
    with open("./gprs_attach_sr_raw.log", 'w') as expect_log:
        ssh_command = "ssh " + user + "@" + ip_address
        ssh_newkey = "Are you sure you want to continue connecting"
        child = pexpect.spawnu(ssh_command)
        child.logfile = expect_log
        # Set conditional based on matched patterns returned by "i" pexpect instance
        i = child.expect([pexpect.TIMEOUT, ssh_newkey, "password:"])
        if i == 0: # Timeout -> expect method match TIMEOUT pattern
            print("ERROR!")
            print("SSH could not login. Here is what SSH said:")
            print(child.before, child.after)
            return None
        if i == 1: # SSH does not have the public key, just accept it
            child.sendline("yes")
            b = child.expect([pexpect.TIMEOUT, "password:"])
            if b == 0: # Timeout
                print("ERROR!")
                print("SSH Could not login. Here is what SSH said:")
                print(child.before, child.after)
            if b == 1: # Continue
                child.sendline(password)
                child.expect(node_expect)
                child.sendline('show gmm-sm statistics gmm-only gprs-service gprs-svc verbose')
                child.expect(node_expect)
                child.sendline('exit')            
        if i == 2: # SSH already has the public key
                child.sendline(password)
                child.expect(node_expect)
                child.sendline('show gmm-sm statistics gmm-only gprs-service gprs-svc verbose')
                child.expect(node_expect)
                child.sendline('exit')

def parse_data(node, gprs_attach_sr_raw_log):
    with open(gprs_attach_sr_raw_log, 'r') as parse_log:
        lines = parse_log.readlines()
        gprsAttachAccept = ""
        gprsAttachReject = ""
        gprsAttachFailure = ""
        gprsGprsSvcNotAllow = ""
        gprsGprsNonGprsSvcNotAllow = ""
        gprsRoamingNotAllowedLocArea = ""
        gprsGprsSvcNotAllowedPlmn = ""
        gprsNoSuitableCellsLocArea = ""
        gprsFailOngoingProc = ""
        gprsNetworkFailureExt = ""
        for index, line in enumerate(lines):
            if re.match(r"Attach Accept:", line):
                line_gprs_attach_accept = lines[index + 2]
                gprsAttachAccept = int(line_gprs_attach_accept.strip().split()[3])
            if re.match(r"Attach Reject:", line):
                line_gprs_attach_reject = lines[index + 2]
                gprsAttachReject = int(line_gprs_attach_reject.strip().split()[3])    
            if re.match(r"Attach Failure:", line):
                line_gprs_attach_failure = lines[index + 2]
                gprsAttachFailure = int(line_gprs_attach_failure.strip().split()[3])
            if re.match(r"Gprs-Attach Reject Causes:", line):
                line_gprs_svc_not_allow = lines[index + 4]
                line_gprs_non_gprs_not_allow = lines[index + 6]
                line_roaming_not_allow = lines[index + 12]
                line_gprs_svc_not_allow_plmn = lines[index + 14]
                line_no_suitable_cells_la = lines[index + 16]
                gprsGprsSvcNotAllow = int(line_gprs_svc_not_allow.strip().split()[9])
                gprsGprsNonGprsSvcNotAllow = int(line_gprs_non_gprs_not_allow.strip().split()[5])
                gprsRoamingNotAllowedLocArea = int(line_roaming_not_allow.strip().split()[7])
                gprsGprsSvcNotAllowedPlmn = int(line_gprs_svc_not_allow_plmn.strip().split()[7])
                gprsNoSuitableCellsLocArea = int(line_no_suitable_cells_la.strip().split()[7])
            if re.match(r"Gprs-Attach Failure Causes:", line):
                line_gprs_failure_ongoing_proc = lines[index + 4]
                gprsFailOngoingProc = int(line_gprs_failure_ongoing_proc.strip().split()[5])
            if re.match(r"GPRS-Attach Network Failure Cause:", line):
                line_gprs_network_fail_ext = lines[index + 2]
                gprsNetworkFailureExt = int(line_gprs_network_fail_ext.strip().split()[7])

    # KPI Calc
    gprsAttachReq = gprsAttachAccept + gprsAttachReject + gprsAttachFailure
    gprsAttachSr = (gprsAttachAccept / (gprsAttachReq - (gprsGprsSvcNotAllow + gprsGprsNonGprsSvcNotAllow 
                    + gprsRoamingNotAllowedLocArea + gprsGprsSvcNotAllowedPlmn + gprsNoSuitableCellsLocArea
                    + gprsFailOngoingProc + gprsNetworkFailureExt)) * 100)         
    message = '2gattach_sr:{0:.2f}'
    print(message.format(gprsAttachSr, end=''))

def main(argv):
    node_expect = sys.argv[1].upper() + "#"
    ip_address = sys.argv[2]
    node_config_file = "/usr/share/cacti/site/COMMON/node_config.json"
    node_config = load_node_config(node_config_file)
    user, password = get_node_user_pass(node_config)
    get2gAttachSrStats(node_expect, ip_address, user, password)
    gprs_attach_sr_raw = "./gprs_attach_sr_raw.log"
    parse_data(sys.argv[1].upper(), gprs_attach_sr_raw)
    os.remove(gprs_attach_sr_raw)

if __name__ == "__main__":
    main(sys.argv[1:])