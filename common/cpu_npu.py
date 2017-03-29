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

def get_cpunpu_logs(node_expect, ip_address, user, password):
    with open("./cpu_npu.log", 'w') as expect_log:
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
                child.sendline("show cpu table")
                child.expect(node_expect)
                child.sendline("cpu")
                child.expect(node_expect)
                child.sendline("show npu utilization table")
                child.expect(node_expect)
                child.sendline("npu")
                child.expect(node_expect)
                child.sendline('exit')            
        if i == 2: # SSH already has the public key
            child.sendline(password)
            child.expect(node_expect)
            child.sendline("show cpu table")
            child.expect(node_expect)
            child.sendline("cpu")
            child.expect(node_expect)
            child.sendline("show npu utilization table")
            child.expect(node_expect)
            child.sendline("npu")
            child.expect(node_expect)
            child.sendline('exit')  

def parse_data(node, cpunpu_raw_log):
    cpu_temp_log = "./cpu_temp_log"
    npu_temp_log = "./npu_temp_log"
    with open(cpunpu_raw_log) as parse_log:
        with open(npu_temp_log, 'w') as npu_temp_log:
            with open(cpu_temp_log, 'w') as cpu_temp_log:
                copy_lines_npu = False
                copy_lines_cpu = False
                for line in parse_log:
                    if ("[local]" + node + "# show npu utilization table") in line:
                        copy_lines_npu = True
                    elif ("[local]" + node + "# npu") in line:
                        copy_lines_npu = False
                    elif ("[local]" + node + "# show cpu table") in line:
                        copy_lines_cpu = True
                    elif ("[local]" + node + "# cpu") in line:
                        copy_lines_cpu = False
                    elif copy_lines_npu:
                        npu_temp_log.write(line.lstrip())
                    elif copy_lines_cpu:
                        cpu_temp_log.write(line.lstrip())     

    with open("./cpu_temp_log", 'r') as cpu_temp_log_dua:
        cpu_load_list = []
        for line in cpu_temp_log_dua:
            if "/0" in line:
                fields_cpu = line.strip().split()
                cpu_load_list.append(float(fields_cpu[5].replace("%", "")))

    with open("./npu_temp_log", 'r') as npu_temp_log_dua:
        npu_load_list = []
        for line in npu_temp_log_dua:
            if "/0/" in line:
                fields_npu = line.strip().split()
                npu_load_list.append(float(fields_npu[1].replace("%", "")))
    
    # List calculation
    cpu_load_min = min(cpu_load_list)
    cpu_load_max = max(cpu_load_list)
    cpu_load_avg = round(sum(cpu_load_list) / len(cpu_load_list))
    npu_load_min = min(npu_load_list)
    npu_load_max = max(npu_load_list)
    npu_load_avg = round(sum(npu_load_list) / len(npu_load_list))
    
    # Print out message to be parsed by cacti
    message = 'cpu_load_min:{} cpu_load_avg:{} cpu_load_max:{} npu_load_min:{} npu_load_avg:{} npu_load_max:{}'
    print(message.format(cpu_load_min, cpu_load_avg, cpu_load_max, npu_load_min, npu_load_avg, npu_load_max), end='')
    os.remove("./cpu_temp_log")
    os.remove("./npu_temp_log")

def main(argv):
    node_expect = sys.argv[1].upper() + "#"
    ip_address = sys.argv[2]
    node_config_file = "/usr/share/cacti/site/COMMON/node_config.json"
    node_config = load_node_config(node_config_file)
    user, password = get_node_user_pass(node_config)
    get_cpunpu_logs(node_expect, ip_address, user, password)
    cpunpu_raw_log = "./cpu_npu.log"
    parse_data(sys.argv[1].upper(), cpunpu_raw_log)
    os.remove(cpunpu_raw_log)

if __name__ == "__main__":
    main(sys.argv[1:])
