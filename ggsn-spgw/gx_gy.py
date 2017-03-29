#!/usr/bin/env python3
#
# author == __gandhi__
# ngakan.gandhi@packet-systems.com

import pexpect
import sys
import os
import json

def get_data(argv):
    sgsn = sys.argv[1].upper() + '# '
    ip_address = sys.argv[2]
    get_gxgy_logs(sgsn, ip_address)

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

def get_gxgy_logs(node_expect, ip_address, user, password):
    with open("./gxgy_temp.log", 'w') as expect_log:
        ssh_newkey = "Are you sure you want to continue connecting"
        ssh_command = "ssh " + user + "@" + ip_address
        child = pexpect.spawnu(ssh_command)
        child.logfile = expect_log
        # Set conditional based on matched patterns returned by "i" pexpect instance
        i = child.expect([pexpect.TIMEOUT, ssh_newkey, "password:"])
        if i == 0: # Timeout -> expect method match TIMEOUT pattern
            print("ERROR!")
            print("SSH could not login. Here is what SSH said:")
            print(child.before, child.after)
            return None
        if i == 1: # SSH does not have the public key, just accept it -> expect method match ssh_newkey pattern
            child.sendline("yes")
            b = child.expect([pexpect.TIMEOUT, "password:"])
            if b == 0: # Timeout
                print("ERROR!")
                print("SSH Could not login. Here is what SSH said:")
                print(child.before, child.after)
            if b == 1: # Continue
                child.sendline(password)
                child.expect(node_expect)
                child.sendline("show diameter tps-statistics")
                child.expect(node_expect)
                child.sendline('exit')            
        if i == 2: # SSH already has the public key
            child.sendline(password)
            child.expect(node_expect)
            child.sendline("show diameter tps-statistics")
            child.expect(node_expect)
            child.sendline('exit')
        
def parse_data(node, gxgy_raw_log):
    with open(gxgy_raw_log) as parse_log:
        with open("./gxgy_temp.log", 'r') as gxgy_temp_log:
            # read the file line by line and returns a list containing the lines
            lines = gxgy_temp_log.readlines()
            # enumerate (returns a tuple of count and the values) from the list of lines above
            # using its count as "index", get the next line after pattern matched
            for index, line in enumerate(lines):
                if "Gx" in line:
                    gx_nextline = lines[index+1]
                    fields_gx = gx_nextline.strip().split()
                    gx_tps = int(fields_gx[6])
                elif "Gy" in line:
                    gy_nextline = lines[index+1]
                    fields_gy = gy_nextline.strip().split()
                    gy_tps = int(fields_gy[6])
    
    message = 'gx_tps:{} gy_tps:{}'
    print(message.format(gx_tps, gy_tps), end='')

def main(argv):
    node_expect = sys.argv[1].upper() + "#"
    ip_address = sys.argv[2]
    node_config_file = "/usr/share/cacti/site/COMMON/node_config.json"
    node_config = load_node_config(node_config_file)
    user, password = get_node_user_pass(node_config)
    get_gxgy_logs(node_expect, ip_address, user, password)
    gxgy_raw_log = "./gxgy_temp.log"
    parse_data(sys.argv[1].upper(), gxgy_raw_log)
    os.remove(gxgy_raw_log)

if __name__ == "__main__":
    main(sys.argv[1:])
