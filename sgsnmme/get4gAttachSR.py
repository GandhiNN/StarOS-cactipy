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

def get4gAttachSrStats(node_expect, ip_address, user, password):
    with open("./eps_attach_sr_raw.log", 'w') as expect_log:
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
                child.sendline('show mme-service statistics emm-only verbose')
                child.expect(node_expect)
                child.sendline('exit')            
        if i == 2: # SSH already has the public key
                child.sendline(password)
                child.expect(node_expect)
                child.sendline('show mme-service statistics emm-only verbose')
                child.expect(node_expect)
                child.sendline('exit')

def parse_data(node, eps_attach_sr_raw_log):
    with open(eps_attach_sr_raw_log, 'r') as parse_log:
        lines = parse_log.readlines()
        emmAttachReject = ""
        emmAttachRequest = ""
        emmNoSuitableCellTA = ""
        emmNoEpsSvcPlmn = ""
        emmPlmnNotAllow = ""
        emmIllegalUe = ""
        emmImeiNotAccept = ""
        emmTANotAllowed = ""
        emmAttachRejSvcNotSubscribed = ""
        emmAttachRejActivationRejected = ""
        emmAttachRejApnRestrictIncomt = ""
        emmAttachDetachInProgress = ""
        emmEpsNonEpsNotAllowed = ""
        emmEpsNotAllowed = ""
        emmRoamingRestrictTA = ""
        emmIllegalMe = ""
        emmDecodeFailure = ""
        emmAttachRejSvcOptNotSupported = ""
        emmAttachRejOdb = ""
        emmAttachRejProtError = ""
        emmAttachUeInitDetach = ""
        for index, line in enumerate(lines):
            if re.match(r"    Attach Reject:", line): # 4 leading whitespaces included, due to match exact string
                emmAttachReject = int(line.strip().split()[2])
                line_emm_no_suitable_cell_ta = lines[index + 15]
                emmNoSuitableCellTA = int(line_emm_no_suitable_cell_ta.strip().split()[10])
                line_emm_no_eps_svc_plmn = lines[index + 16]
                emmNoEpsSvcPlmn = int(line_emm_no_eps_svc_plmn.strip().split()[8])
                line_emm_plmn_not_allow = lines[index + 14]
                emmPlmnNotAllow = int(line_emm_plmn_not_allow.strip().split()[3])
                line_emm_illegal_ue = lines[index + 1]
                emmIllegalUe = int(line_emm_illegal_ue.strip().split()[7])
                line_emm_imei_not_accepted = lines[index + 13]
                emmImeiNotAccept = int(line_emm_imei_not_accepted.strip().split()[3])
                line_emm_ta_not_allowed = lines[index + 14]
                emmTANotAllowed = int(line_emm_ta_not_allowed.strip().split()[7])
                line_emm_eps_non_eps_not_allowed = lines[index + 15]
                emmEpsNonEpsNotAllowed = int(line_emm_eps_non_eps_not_allowed.strip().split()[4])
                line_emm_eps_not_allowed = lines[index + 2]
                emmEpsNotAllowed = int(line_emm_eps_not_allowed.strip().split()[6])
                line_roam_restrict_ta = lines[index + 13]
                emmRoamingRestrictTA = int(line_roam_restrict_ta.strip().split()[7])
                line_emm_illegal_me = lines[index + 2]
                emmIllegalMe = int(line_emm_illegal_me.strip().split()[2])
                line_emm_decode_failure = lines[index + 12]
                emmDecodeFailure = int(line_emm_decode_failure.strip().split()[6])
            if re.match(r"    ESM Failure:", line):
                line_emm_attach_rej_svc_not_subscribed = lines[index + 2]
                emmAttachRejSvcNotSubscribed = int(line_emm_attach_rej_svc_not_subscribed.strip().split()[9])
                line_emm_attach_rej_act_rejected = lines[index + 4]
                emmAttachRejActivationRejected = int(line_emm_attach_rej_act_rejected.strip().split()[5])
                line_emm_attach_rej_apn_restrict_incomt = lines[index + 6]
                emmAttachRejApnRestrictIncomt = int(line_emm_attach_rej_apn_restrict_incomt.strip().split()[3])
                line_emm_attach_rej_svc_opt_not_supp = lines[index + 2]
                emmAttachRejSvcOptNotSupported = int(line_emm_attach_rej_svc_opt_not_supp.strip().split()[4])
                line_emm_odb = lines[index + 3]
                emmAttachRejOdb = int(line_emm_odb.strip().split()[6])
                line_emm_attach_rej_prot_error = lines[index + 5]
                emmAttachRejProtError = int(line_emm_attach_rej_prot_error.strip().split()[7])
            if re.match(r"    No Attach Reject/Accept", line):
                line_emm_attach_detach_in_progress = lines[index + 2]
                emmAttachDetachInProgress = int(line_emm_attach_detach_in_progress.strip().split()[3])
                line_emm_ue_init_detach = lines[index + 1]
                emmAttachUeInitDetach = int(line_emm_ue_init_detach.strip().split()[6])
            if re.match(r"    Attach Request:", line):
                emmAttachRequest = int(line.strip().split()[2])    
            
    # KPI Calc
    emmValidReasonExclude = (emmNoSuitableCellTA + emmNoEpsSvcPlmn + emmPlmnNotAllow + emmIllegalUe
                            + emmImeiNotAccept + emmTANotAllowed + emmAttachRejSvcNotSubscribed 
                            + emmAttachRejActivationRejected + emmAttachRejApnRestrictIncomt
                            + emmAttachDetachInProgress + emmEpsNonEpsNotAllowed + emmEpsNotAllowed
                            + emmRoamingRestrictTA + emmIllegalMe + emmDecodeFailure + emmAttachRejSvcOptNotSupported
                            + emmAttachRejOdb + emmAttachRejProtError + emmAttachUeInitDetach)

    epsAttachSr = (1 - ((emmAttachReject - emmValidReasonExclude) / emmAttachRequest)) * 100         
    message = '4gattach_sr:{0:.2f}'
    print(message.format(epsAttachSr, end=''))

def main(argv):
    node_expect = sys.argv[1].upper() + "#"
    ip_address = sys.argv[2]
    node_config_file = "/usr/share/cacti/site/COMMON/node_config.json"
    node_config = load_node_config(node_config_file)
    user, password = get_node_user_pass(node_config)
    get4gAttachSrStats(node_expect, ip_address, user, password)
    eps_attach_sr_raw = "./eps_attach_sr_raw.log"
    parse_data(sys.argv[1].upper(), eps_attach_sr_raw)
    os.remove(eps_attach_sr_raw)

if __name__ == "__main__":
    main(sys.argv[1:])