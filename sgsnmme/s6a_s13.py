#!/usr/bin/env python3
#
# author == __gandhi__
# ngakan.gandhi@packet-systems.com

import pexpect
import sys
import os
import time
import json

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

def split_list(a_list):
    half = int(len(a_list)/2)
    return a_list[:half], a_list[half:]

def get_s6as13_logs(node_expect, ip_address, user, password):
    with open("./tot_s6a_s13.log", 'w') as expect_log:
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
                child.sendline("show mme-service statistics emm-only verbose")
                time.sleep(5)
                child.expect(node_expect)
                child.sendline("show mme-service statistics emm-only verbose")
                child.expect(node_expect)
                child.sendline("show diameter tps-statistics")
                child.expect(node_expect)
                child.sendline('exit')
        if i == 2: # SSH already has the public key
            child.sendline(password)
            child.expect(node_expect)
            child.sendline("show mme-service statistics emm-only verbose")
            time.sleep(5)
            child.expect(node_expect)
            child.sendline("show mme-service statistics emm-only verbose")
            child.expect(node_expect)
            child.sendline("show diameter tps-statistics")
            child.expect(node_expect)
            child.sendline('exit')

def parse_data(s13_raw_log):
    with open(s13_raw_log) as parse_log:
        with open("./s13_temp_log", 'w') as s13_temp_log:
            copy_lines = False
            s6a_tps = ''
            for line in parse_log:
                if "S13 Statistics" in line:
                    copy_lines = True
                elif "Procedure Failure Reasons" in line:
                    copy_lines = False
                elif "Last  1  Sec Average TPS" in line:
                    fields_b = line.strip().split()
                    s6a_tps = int(fields_b[6])
                elif copy_lines:
                    s13_temp_log.write(line.lstrip())

    with open("./s13_temp_log", 'r') as s13_temp_log_dua:
        s13_tps_list = []
        for line in s13_temp_log_dua:
            if "Answer:" in line:
                fields_a = line.strip().split()
                s13_tps_list.append(int(fields_a[3]))
    
    B, C = split_list(s13_tps_list)
    B_sum = sum(B)
    C_sum = sum(C)
    s13_tps = int((C_sum - B_sum) / 5)
    if s6a_tps < 0:
        s6a_tps = 0
    if s13_tps < 0:
        s13_tps = 0
    message = 's6a_tps:{} s13_tps:{}'
    print(message.format(s6a_tps, s13_tps), end='')
    os.remove("./s13_temp_log")

# Treat numbers as counter first
def main(argv):
    node_expect = sys.argv[1].upper() + "#"
    ip_address = sys.argv[2]
    node_config_file = "/usr/share/cacti/site/COMMON/node_config.json"
    node_config = load_node_config(node_config_file)
    user, password = get_node_user_pass(node_config)
    get_s6as13_logs(node_expect, ip_address, user, password)
    s13_raw_log = "./tot_s6a_s13.log"
    parse_data(s13_raw_log)
    os.remove(s13_raw_log)

if __name__ == "__main__":
    main(sys.argv[1:])