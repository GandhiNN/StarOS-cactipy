#!/usr/bin/env python3
#
# author == __gandhi__
# ngakan.gandhi@packet-systems.com

import pexpect
import sys
import os
import json
import time
from pathlib import Path

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

def get_gmmsm_stats(node_expect, ip_address, user, password):
    with open("./gmmsm_stats.log", 'w') as expect_log:
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
                child.sendline('show gmm-sm statistics gmm-only | grep -E -i "3g-attach-reject: | 3g-attach-failure: "')
                child.expect(node_expect)
                child.sendline('show mme-service statistics | grep -E -i "attach reject: | esm failure:"')
                child.expect(node_expect)
                child.sendline('exit')            
        if i == 2: # SSH already has the public key
                child.sendline(password)
                child.expect(node_expect)
                child.sendline('show gmm-sm statistics gmm-only | grep -E -i "3g-attach-reject: | 3g-attach-failure: "')
                child.expect(node_expect)
                child.sendline('show mme-service statistics | grep -E -i "attach reject: | esm failure:"')
                child.expect(node_expect)
                child.sendline('exit')

def parse_data(node, gmmsm_raw_log):
    with open(gmmsm_raw_log, 'r') as parse_log:
        lines = parse_log.readlines()
        gprs_att_rej_now = ""
        gprs_att_fail_now = ""
        sgsn_att_rej_now = ""
        sgsn_att_fail_now = ""
        eps_att_rej_now = ""
        eps_esm_fail_now = ""
        for index, line in enumerate(lines):
            if "3G-Attach-Reject:" in line:
                fields_attach_reject = line.strip().split()
                sgsn_att_rej_now = int(fields_attach_reject[1])
                gprs_att_rej_now = int(fields_attach_reject[3])
            elif "3G-Attach-Failure:" in line:
                fields_attach_failure = line.strip().split()
                sgsn_att_fail_now = int(fields_attach_failure[1])
                gprs_att_fail_now = int(fields_attach_failure[3])
            elif "Attach Reject:" in line:
                fields_eps_reject = line.strip().split()
                eps_att_rej_now = int(fields_eps_reject[2])
            elif "ESM Failure:" in line:
                fields_eps_esm_fail = line.strip().split()
                eps_esm_fail_now = int(fields_eps_esm_fail[2])

    # List Calculation
    ref_file = Path("/usr/share/cacti/site/SGSNMME/scripts/gmm_sm_stats_temp.txt")
    if not ref_file.is_file():
        # If file does not exists, assign all vars to have a value of 0
        gprs_att_rej = 0
        gprs_att_fail = 0
        sgsn_att_rej = 0
        sgsn_att_fail = 0
        eps_att_rej = 0
        eps_esm_fail = 0
        with open(ref_file, 'w') as ref_file:
            ref_file.write("{}\n{}\n{}\n{}\n{}\n{}".format(gprs_att_rej_now, gprs_att_fail_now, sgsn_att_rej_now, sgsn_att_fail_now, eps_att_rej_now, eps_esm_fail_now))
    else:
        # If file exists, do diff calculation for each vars
        with open(ref_file, 'r+') as ref_file:
            # Read each line to a list, strip the return char
            data_list_raw = ref_file.readlines()
            data = [x.strip() for x in data_list_raw]

            # Read the previous values
            gprs_att_rej_before = int(data[0])
            gprs_att_fail_before = int(data[1])
            sgsn_att_rej_before = int(data[2])
            sgsn_att_fail_before = int(data[3])
            eps_att_rej_before = int(data[4])
            eps_esm_fail_before = int(data[5])

            # Calculate the increase
            gprs_att_rej = gprs_att_rej_now - gprs_att_rej_before
            gprs_att_fail = gprs_att_fail_now - gprs_att_fail_before
            sgsn_att_rej = sgsn_att_rej_now - sgsn_att_rej_before 
            sgsn_att_fail = sgsn_att_fail_now - sgsn_att_fail_before
            eps_att_rej = eps_att_rej_now - eps_att_rej_before
            eps_esm_fail = eps_esm_fail_now - eps_esm_fail_before
            
            # Overwrite the file with the new value taken
            ref_file.seek(0)
            ref_file.write("{}\n{}\n{}\n{}\n{}\n{}".format(gprs_att_rej_now, gprs_att_fail_now, sgsn_att_rej_now, sgsn_att_fail_now, eps_att_rej_now, eps_esm_fail_now))
            ref_file.truncate() 
                
    message = '2gattach_rej:{} 2gattach_fail:{} 3gattach_rej:{} 3gattach_fail:{} 4gattach_rej:{} 4gesm_fail:{}'
    print(message.format(gprs_att_rej, gprs_att_fail, sgsn_att_rej, sgsn_att_fail, eps_att_rej, eps_esm_fail), end='')

def main(argv):
    node_expect = sys.argv[1].upper() + "#"
    ip_address = sys.argv[2]
    node_config_file = "/usr/share/cacti/site/COMMON/node_config.json"
    node_config = load_node_config(node_config_file)
    user, password = get_node_user_pass(node_config)
    get_gmmsm_stats(node_expect, ip_address, user, password)
    gmmsm_raw_log = "./gmmsm_stats.log"
    parse_data(sys.argv[1].upper(), gmmsm_raw_log)
    os.remove(gmmsm_raw_log)

if __name__ == "__main__":
    main(sys.argv[1:])
