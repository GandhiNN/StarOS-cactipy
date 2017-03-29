#!/usr/bin/env python3
#
# author == __gandhi__
# ngakan.gandhi@packet-systems.com

import pexpect
import sys
import os
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

def get_act_sub(node_expect, ip_address, user, password):
    with open("./act_sub_tmp.log", 'w') as expect_log:
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
                child.sendline("show subscribers data-rate summary")
                child.expect(node_expect)
                child.sendline('exit')
        if i == 2: # SSH already has the public key
            child.sendline(password)
            child.expect(node_expect)
            child.sendline("show subscribers data-rate summary")
            child.expect(node_expect)
            child.sendline('exit')                            

def parse_data():
    with open("./act_sub_tmp.log") as parse_log:
        for line in parse_log:
            if "Total Subscribers" in line:
                fields_a = line.strip().split()
                tot_sub = int(fields_a[3])
            elif "Active" in line:
                fields_b = line.strip().split()
                act_sub = int(fields_b[2])

    message = 'tot_sub:{} act_sub:{}'
    print(message.format(tot_sub, act_sub), end='')

def main(argv):
    node_expect = sys.argv[1].upper() + "#"
    ip_address = sys.argv[2]
    node_config_file = "/usr/share/cacti/site/COMMON/node_config.json"
    node_config = load_node_config(node_config_file)
    user, password = get_node_user_pass(node_config)
    get_act_sub(node_expect, ip_address, user, password)
    parse_data()
    os.remove("./act_sub_tmp.log")

if __name__ == "__main__":
    main(sys.argv[1:])
