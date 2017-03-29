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

# Login to the node and execute CLI sequences
def get_task_resources_log(node_expect, ip_address, user, password):
    with open("./task_resources.log", 'w') as expect_log:
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
                child.sendline("show task resources facility diamproxy all")
                child.expect(node_expect)
                child.sendline("diamproxy")
                child.expect(node_expect)
                child.sendline("show task resources facility linkmgr all")
                child.expect(node_expect)
                child.sendline("linkmgr")
                child.expect(node_expect)
                child.sendline("show task resources facility gbmgr all")
                child.expect(node_expect)
                child.sendline("gbmgr")
                child.expect(node_expect)
                child.sendline("show task resources facility mmemgr all")
                child.expect(node_expect)
                child.sendline("mmemgr")
                child.expect(node_expect)
                child.sendline("show task resources facility sessmgr all")
                child.expect(node_expect)
                child.sendline("sessmgr")
                child.expect(node_expect)
                child.sendline("show task resources facility bulkstat all")
                child.expect(node_expect)
                child.sendline("bulkstat")
                child.expect(node_expect)
                child.sendline('exit')
        if i == 2: # SSH already has the public key
            child.sendline(password)
            child.expect(node_expect)
            child.sendline("show task resources facility diamproxy all")
            child.expect(node_expect)
            child.sendline("diamproxy")
            child.expect(node_expect)
            child.sendline("show task resources facility linkmgr all")
            child.expect(node_expect)
            child.sendline("linkmgr")
            child.expect(node_expect)
            child.sendline("show task resources facility gbmgr all")
            child.expect(node_expect)
            child.sendline("gbmgr")
            child.expect(node_expect)
            child.sendline("show task resources facility mmemgr all")
            child.expect(node_expect)
            child.sendline("mmemgr")
            child.expect(node_expect)
            child.sendline("show task resources facility sessmgr all")
            child.expect(node_expect)
            child.sendline("sessmgr")
            child.expect(node_expect)
            child.sendline("show task resources facility bulkstat all")
            child.expect(node_expect)
            child.sendline("bulkstat")
            child.expect(node_expect)
            child.sendline('exit')

def parse_data(node, task_resources_raw_log):
    diamproxy_temp_log = "./diamproxy_temp_log"
    linkmgr_temp_log = "./linkmgr_temp_log"
    gbmgr_temp_log = "./gbmgr_temp_log"
    mmemgr_temp_log = "./mmemgr_temp_log"
    sessmgr_temp_log = "./sessmgr_temp_log"
    bulkstat_temp_log = "./bulkstat_temp_log"
    with open(task_resources_raw_log) as parse_log:
        with open(diamproxy_temp_log, 'w') as diamproxy_temp_log:
            with open(linkmgr_temp_log, 'w') as linkmgr_temp_log:
                with open(gbmgr_temp_log, 'w') as gbmgr_temp_log:
                    with open(mmemgr_temp_log, 'w') as mmemgr_temp_log:
                        with open(sessmgr_temp_log, 'w') as sessmgr_temp_log:
                            with open(bulkstat_temp_log, 'w') as bulkstat_temp_log:
                                copy_lines_diamproxy = False
                                copy_lines_linkmgr = False
                                copy_lines_gbmgr = False
                                copy_lines_mmemgr = False
                                copy_lines_sessmgr = False
                                copy_lines_bulkstat = False

                                for line in parse_log:
                                    if ("[local]" + node + "# show task resources facility diamproxy all") in line:
                                        copy_lines_diamproxy = True
                                    elif ("[local]" + node + "# diamproxy") in line:
                                        copy_lines_diamproxy = False
                                    elif ("[local]" + node + "# show task resources facility linkmgr all") in line:
                                        copy_lines_linkmgr = True
                                    elif ("[local]" + node + "# linkmgr") in line:
                                        copy_lines_linkmgr = False
                                    elif ("[local]" + node + "# show task resources facility gbmgr all") in line:
                                        copy_lines_gbmgr = True
                                    elif ("[local]" + node + "# gbmgr") in line:
                                        copy_lines_gbmgr = False
                                    elif ("[local]" + node + "# show task resources facility mmemgr all") in line:
                                        copy_lines_mmemgr = True
                                    elif ("[local]" + node + "# mmemgr") in line:
                                        copy_lines_mmemgr = False
                                    elif ("[local]" + node + "# show task resources facility sessmgr all") in line:
                                        copy_lines_sessmgr = True
                                    elif ("[local]" + node + "# sessmgr") in line:
                                        copy_lines_sessmgr = False
                                    elif ("[local]" + node + "# show task resources facility bulkstat all") in line:
                                        copy_lines_bulkstat = True
                                    elif ("[local]" + node + "# bulkstat") in line:
                                        copy_lines_bulkstat = False                                    
                                    elif copy_lines_diamproxy:
                                        diamproxy_temp_log.write(line.lstrip())
                                    elif copy_lines_linkmgr:
                                        linkmgr_temp_log.write(line.lstrip())     
                                    elif copy_lines_gbmgr:
                                        gbmgr_temp_log.write(line.lstrip())
                                    elif copy_lines_mmemgr:
                                        mmemgr_temp_log.write(line.lstrip()) 
                                    elif copy_lines_sessmgr:
                                        sessmgr_temp_log.write(line.lstrip())
                                    elif copy_lines_bulkstat:
                                        bulkstat_temp_log.write(line.lstrip()) 

    with open("./diamproxy_temp_log", 'r') as diamproxy_temp_log_dua:
        diamproxy_load_list = []
        for line in diamproxy_temp_log_dua:
            if "/0" in line:
                fields_diamproxy = line.strip().split()
                diamproxy_load_list.append(float(fields_diamproxy[3].replace("%", "")))

    with open("./linkmgr_temp_log", 'r') as linkmgr_temp_log_dua:
        linkmgr_load_list = []
        for line in linkmgr_temp_log_dua:
            if "/0" in line:
                fields_linkmgr = line.strip().split()
                linkmgr_load_list.append(float(fields_linkmgr[3].replace("%", "")))

    with open("./gbmgr_temp_log", 'r') as gbmgr_temp_log_dua:
        gbmgr_load_list = []
        for line in gbmgr_temp_log_dua:
            if "/0" in line:
                fields_gbmgr = line.strip().split()
                gbmgr_load_list.append(float(fields_gbmgr[3].replace("%", "")))

    with open("./mmemgr_temp_log", 'r') as mmemgr_temp_log_dua:
        mmemgr_load_list = []
        for line in mmemgr_temp_log_dua:
            if "/0" in line:
                fields_mmemgr = line.strip().split()
                mmemgr_load_list.append(float(fields_mmemgr[3].replace("%", "")))  

    with open("./sessmgr_temp_log", 'r') as sessmgr_temp_log_dua:
        sessmgr_load_list = []
        for line in sessmgr_temp_log_dua:
            if "/0" in line:
                fields_sessmgr = line.strip().split()
                sessmgr_load_list.append(float(fields_sessmgr[3].replace("%", "")))

    with open("./bulkstat_temp_log", 'r') as bulkstat_temp_log_dua:
        bulkstat_load_list = []
        for line in bulkstat_temp_log_dua:
            if "/0" in line:
                fields_bulkstat = line.strip().split()
                bulkstat_load_list.append(float(fields_bulkstat[3].replace("%", "")))         

    # List calculation
    diamproxy_load = max(diamproxy_load_list)
    linkmgr_load = max(linkmgr_load_list)
    gbmgr_load = max(gbmgr_load_list)
    mmemgr_load = max(mmemgr_load_list)
    sessmgr_load = max(sessmgr_load_list)
    bulkstat_load = max(bulkstat_load_list)

    # Print out message to be parsed by cacti
    message = 'diamproxy_load:{} linkmgr_load:{} gbmgr_load:{} mmemgr_load:{} sessmgr_load:{} bulkstat_load:{}'
    print(message.format(diamproxy_load, linkmgr_load, gbmgr_load, mmemgr_load, sessmgr_load, bulkstat_load), end='')
    os.remove("./diamproxy_temp_log")
    os.remove("./linkmgr_temp_log")
    os.remove("./gbmgr_temp_log")
    os.remove("./mmemgr_temp_log")  
    os.remove("./sessmgr_temp_log")
    os.remove("./bulkstat_temp_log")       

def main(argv):
    node_expect = sys.argv[1].upper() + "#"
    ip_address = sys.argv[2]
    node_config_file = "/usr/share/cacti/site/COMMON/node_config.json"
    node_config = load_node_config(node_config_file)
    user, password = get_node_user_pass(node_config)
    get_task_resources_log(node_expect, ip_address, user, password)
    task_resources_raw_log = "./task_resources.log"
    parse_data(sys.argv[1].upper(), task_resources_raw_log)
    os.remove(task_resources_raw_log)

if __name__ == "__main__":
    main(sys.argv[1:])
