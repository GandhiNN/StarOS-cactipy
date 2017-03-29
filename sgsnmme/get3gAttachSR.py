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

def get3gAttachSrStats(node_expect, ip_address, user, password):
    with open("./sgsn_attach_sr_raw.log", 'w') as expect_log:
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
                child.sendline('show gmm-sm statistics gmm-only sgsn-service sgsn-svc verbose')
                child.expect(node_expect)
                child.sendline('exit')            
        if i == 2: # SSH already has the public key
                child.sendline(password)
                child.expect(node_expect)
                child.sendline('show gmm-sm statistics gmm-only sgsn-service sgsn-svc verbose')
                child.expect(node_expect)
                child.sendline('exit')

def parse_data(node, sgsn_attach_sr_raw_log):
    with open(sgsn_attach_sr_raw_log, 'r') as parse_log:
        lines = parse_log.readlines()
        sgsnAttachAccept = ""
        sgsnAttachReject = ""
        sgsAttachFailure = ""
        sgsnGprsSvcNotAllow = ""
        sgsnGprsNonGprsSvcNotAllow = ""
        sgsnRoamingNotAllowedLocArea = ""
        sgsnGprsSvcNotAllowedPlmn = ""
        sgsnNoSuitableCellsLocArea = ""
        sgsnFailOngoingProc = ""
        sgsnNetworkFailureExt = ""
        for index, line in enumerate(lines):
            if re.match(r"Attach Accept:", line):
                line_sgsn_attach_accept = lines[index + 2]
                sgsnAttachAccept = int(line_sgsn_attach_accept.strip().split()[1])
            if re.match(r"Attach Reject:", line):
                line_sgsn_attach_reject = lines[index + 2]
                sgsnAttachReject = int(line_sgsn_attach_reject.strip().split()[1])    
            if re.match(r"Attach Failure:", line):
                line_sgsn_attach_failure = lines[index + 2]
                sgsnAttachFailure = int(line_sgsn_attach_failure.strip().split()[1])       
            if re.match(r"Gprs-Attach Reject Causes:", line):
                line_gprs_svc_not_allow = lines[index + 4]
                line_gprs_non_gprs_not_allow = lines[index + 6]
                line_roaming_not_allow = lines[index + 12]
                line_gprs_svc_not_allow_plmn = lines[index + 14]
                line_no_suitable_cells_la = lines[index + 16]
                sgsnGprsSvcNotAllow = int(line_gprs_svc_not_allow.strip().split()[4])
                sgsnGprsNonGprsSvcNotAllow = int(line_gprs_non_gprs_not_allow.strip().split()[2])
                sgsnRoamingNotAllowedLocArea = int(line_roaming_not_allow.strip().split()[3])
                sgsnGprsSvcNotAllowedPlmn = int(line_gprs_svc_not_allow_plmn.strip().split()[3])
                sgsnNoSuitableCellsLocArea = int(line_no_suitable_cells_la.strip().split()[3])
            if re.match(r"Gprs-Attach Failure Causes:", line):
                line_sgsn_failure_ongoing_proc = lines[index + 4]
                sgsnFailOngoingProc = int(line_sgsn_failure_ongoing_proc.strip().split()[2])
            if re.match(r"GPRS-Attach Network Failure Cause:", line):
                line_sgsn_network_fail_ext = lines[index + 1]
                sgsnNetworkFailureExt = int(line_sgsn_network_fail_ext.strip().split()[4])

    # KPI Calc
    sgsnAttachReq = sgsnAttachAccept + sgsnAttachReject + sgsnAttachFailure
    sgsnAttachSr = (sgsnAttachAccept / (sgsnAttachReq - (sgsnGprsSvcNotAllow + sgsnGprsNonGprsSvcNotAllow 
                    + sgsnRoamingNotAllowedLocArea + sgsnGprsSvcNotAllowedPlmn + sgsnNoSuitableCellsLocArea
                    + sgsnFailOngoingProc + sgsnNetworkFailureExt)) * 100)         
    message = '3gattach_sr:{0:.2f}'
    print(message.format(sgsnAttachSr, end=''))

def main(argv):
    node_expect = sys.argv[1].upper() + "#"
    ip_address = sys.argv[2]
    node_config_file = "/usr/share/cacti/site/COMMON/node_config.json"
    node_config = load_node_config(node_config_file)
    user, password = get_node_user_pass(node_config)
    get3gAttachSrStats(node_expect, ip_address, user, password)
    sgsn_attach_sr_raw = "./sgsn_attach_sr_raw.log"
    parse_data(sys.argv[1].upper(), sgsn_attach_sr_raw)
    os.remove(sgsn_attach_sr_raw)

if __name__ == "__main__":
    main(sys.argv[1:])