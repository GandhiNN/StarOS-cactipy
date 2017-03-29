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
def get_subs_all_rat(node_expect, ip_address, user, password):
    with open("./tot_all_rat_sub.log", 'w') as expect_log:
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
                child.sendline("show subscribers gprs-only summary")
                child.expect(node_expect)
                child.sendline("2g")
                child.expect(node_expect)
                child.sendline("show subscribers sgsn-only summary")
                child.expect(node_expect)
                child.sendline("3g")
                child.expect(node_expect)
                child.sendline("show subscribers mme-only summary")
                child.expect(node_expect)
                child.sendline("4g")
                child.expect(node_expect)
                child.sendline('exit')
        if i == 2: # SSH already has the public key
            child.sendline(password)
            child.expect(node_expect)
            child.sendline("show subscribers gprs-only summary")
            child.expect(node_expect)
            child.sendline("2g")
            child.expect(node_expect)
            child.sendline("show subscribers sgsn-only summary")
            child.expect(node_expect)
            child.sendline("3g")
            child.expect(node_expect)
            child.sendline("show subscribers mme-only summary")
            child.expect(node_expect)
            child.sendline("4g")
            child.expect(node_expect)
            child.sendline('exit')     

def parse_data(node, all_sub_raw_log):
    gprs_temp_log = "./gprs_temp_log"
    sgsn_temp_log = "./sgsn_temp_log"
    mme_temp_log = "./mme_temp_log"
    with open(all_sub_raw_log) as parse_log:
        with open(gprs_temp_log, 'w') as gprs_temp_log:
            with open(sgsn_temp_log, 'w') as sgsn_temp_log:
                with open(mme_temp_log, 'w') as mme_temp_log:
                    copy_lines_gprs = False
                    copy_lines_sgsn = False
                    copy_lines_mme = False
                    for line in parse_log:
                        if ("[local]" + node + "# show subscribers gprs-only summary") in line:
                            copy_lines_gprs = True
                        elif ("[local]" + node + "# 2g") in line:
                            copy_lines_gprs = False
                        elif ("[local]" + node + "# show subscribers sgsn-only summary") in line:
                            copy_lines_sgsn = True
                        elif ("[local]" + node + "# 3g") in line:
                            copy_lines_sgsn = False
                        elif ("[local]" + node + "# show subscribers mme-only summary") in line:
                            copy_lines_mme = True
                        elif ("[local]" + node + "# 4g") in line:
                            copy_lines_mme = False                            
                        elif copy_lines_gprs:
                            gprs_temp_log.write(line.lstrip())
                        elif copy_lines_sgsn:
                            sgsn_temp_log.write(line.lstrip())
                        elif copy_lines_mme:
                            mme_temp_log.write(line.lstrip())                                  

    with open("./gprs_temp_log", 'r') as gprs_temp_log_dua:
        for line in gprs_temp_log_dua:
            if "Total Ready Subscribers" in line:
                fields_a = line.strip().split()
                gprs_ready = int(fields_a[8])
            elif "Total Standby Subscribers" in line:
                fields_b = line.strip().split()
                gprs_idle = int(fields_b[9])
            elif "Total Active Subscribers" in line:
                fields_c = line.strip().split()
                gprs_active = int(fields_c[4])
                gprs_pdp_ctx = int(fields_c[9])          

    with open("./sgsn_temp_log", 'r') as sgsn_temp_log_dua:
        for line in sgsn_temp_log_dua:
            if "Total Connected Subscribers" in line:
                fields_a = line.strip().split()
                sgsn_conn = int(fields_a[8])
            elif "Total Idle Subscribers" in line:
                fields_b = line.strip().split()
                sgsn_idle = int(fields_b[4])
            elif "Total Active Subscribers" in line:
                fields_c = line.strip().split()
                sgsn_active = int(fields_c[4])
                sgsn_pdp_ctx = int(fields_c[9])

    with open("./mme_temp_log", 'r') as mme_temp_log_dua:
        for line in mme_temp_log_dua:
            if "Total Subscribers" in line:
                fields_a = line.strip().split()
                mme_total = int(fields_a[2])
            elif "Active" in line:
                fields_b = line.strip().split()
                mme_active = int(fields_b[1])
                mme_dormant = int(fields_b[3])             

    # Print out message to be parsed by cacti
    message = '2g_ready:{} 2g_idle:{} 2g_active:{} 2g_pdp_ctx:{} 3g_conn:{} 3g_idle:{} 3g_active:{} 3g_pdp_ctx:{} 4g_total:{} 4g_active:{} 4g_dormant:{}'
    print(message.format(gprs_ready, gprs_idle, gprs_active, gprs_pdp_ctx, sgsn_conn, sgsn_idle, sgsn_active, sgsn_pdp_ctx, mme_total, mme_active, mme_dormant), end='')
    os.remove("./gprs_temp_log")
    os.remove("./sgsn_temp_log")
    os.remove("./mme_temp_log")

def main(argv):
    node_expect = sys.argv[1].upper() + "#"
    ip_address = sys.argv[2]
    node_config_file = "/usr/share/cacti/site/COMMON/node_config.json"
    node_config = load_node_config(node_config_file)
    user, password = get_node_user_pass(node_config)
    get_subs_all_rat(node_expect, ip_address, user, password)
    all_sub_raw_log = "./tot_all_rat_sub.log"
    parse_data(sys.argv[1].upper(), all_sub_raw_log)
    os.remove("./tot_all_rat_sub.log")

if __name__ == "__main__":
    main(sys.argv[1:])
