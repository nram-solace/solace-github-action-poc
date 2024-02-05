#!/usr/bin/python3
########################################################################
# create-queues
#
# This program creates new or update existing queues on a Solace PubSub+ broker using SEMPv2
# While updating, exisitng Queue will be temporarliy disabled, updated and enabled.
# All config and inputs are read from files for batch processing
#
# Requirements:
#  Python 3
#  Modules: pandas, json, yaml
#
# Required input files:
# Config Yaml file:
#   This file has Solace PubSub+ broker access info, default values for queues, etc.
#   See config/sample-config.yaml
# Input CSV file:
#   This file has list of queue names and properties that should be overwritten.
#   See input/sample-queues.csv
#   Properties will  be taken from the input CSV file if present 
#   Otherwise, default values from config file will be used
#   Otherwise, Solace default values will be used
#
# Running:
# Create queues:
#   python3 create-queues.py --config config/nram-local-config.yaml  --input input/nram-test-queues.csv
# Create new or update existing queues: Use --patch option
#   python3 create-queues.py --config private/nram/nram-dev1.yaml  --input private/abc/abc-queues-tests1.csv --patch 
#
# Ramesh Natarajan (nram), Solace PSG (ramesh.natarajan@solace.com)
########################################################################

import sys, os
import argparse
import json, yaml
import pandas as pd
import pprint
from urllib.parse import unquote, quote

sys.path.insert(0, os.path.abspath("."))
from common import LogHandler
from common import SempHandler
#from common import JsonHandler
from common import QueueConfig 
from common import YamlHandler


pp = pprint.PrettyPrinter(indent=4)

me = "create-queues"
ver = '1.3.0'

# Globals
Cfg = {}    # global handy config dict
Verbose = 0
# Define the minimum required Python version
MIN_PYTHON_VERSION = (3, 6)

yaml_h = YamlHandler.YamlHandler()

#--------------------------------------------------------------------
# read_input_csv_file
# Read input csv file and return as pandas dataframe
#--------------------------------------------------------------------
def read_input_csv_file (input_csv_file):
    print ('Reading input file: ', input_csv_file)
    df = pd.read_csv(input_csv_file)
    # Strip leading and trailing spaces from column names
    df.rename(columns=lambda x: x.strip(), inplace=True)
    return df


def main(argv):
    """ program entry drop point """

    # parse command line arguments
    p = argparse.ArgumentParser()
    p.add_argument('--config', dest="config_file", required=True, 
                   help='system and profile config yaml file') 
    p.add_argument('--input', dest="input_file", required=True, 
                   help='user input csv file') 
    p.add_argument('--patch', dest="patch_it", action='store_true', required=False, default=False, 
                   help='user input csv file') 
    p.add_argument( '--verbose', '-v', action="count",  required=False, default=0,
                help='Verbose output. use -vvv for tracing')
    r = p.parse_args()

    print ('\n{}-{} Starting\n'.format(me,ver))

    Verbose = r.verbose

    # read config and input files
    Cfg = yaml_h.read_config_file(r.config_file)
    if Verbose > 2:
        print ('CONFIG', json.dumps(Cfg, indent=4))

    sys_cfg_file = Cfg["internal"]["systemConfig"]
    print ("Reading system config file: {}".format(sys_cfg_file))

    system_config_all = yaml_h.read_config_file (sys_cfg_file)
    if Verbose > 2:
        print ('SYSTEM CONFIG'); pp.pprint (system_config_all)
    Cfg['system'] = system_config_all.copy() # store system cfg in the global Cfg dict
    Cfg['script_name'] = me
    Cfg['verbose'] = Verbose

    log_h = LogHandler.LogHandler(Cfg)
    log = log_h.get()
    log.info('Starting {}-{}'.format(me, ver))

    input_df = read_input_csv_file(r.input_file)

    log.info ('SYSTEM CONFIG : {}'.format(json.dumps(system_config_all, indent=4)))
    log.info ('USER CONFIG   : {}'.format(json.dumps(Cfg, indent=4)))
    log.info ('INPUT DATA    : {}'.format(json.dumps(input_df.to_dict(), indent=4)))
    # add this after dumping Cfg. josn.dumps() can't handle log object
    Cfg['log_handler'] = log_h

    # split input_df into regular queues and DLQs
    # Add your logic here
    regularqs = input_df[-input_df['queueName'].str.contains('(_DLQ)')]
    dmqs = input_df[input_df['queueName'].str.contains('(_DLQ)')]

    log.info ('REGULAR QUEUES : {}'.format(json.dumps(regularqs['queueName'].to_dict(), indent=4)))
    log.info ('DMQS : {}'.format(json.dumps(dmqs['queueName'].to_dict(), indent=4)))

    if Verbose > 2:
        print ('INPUT')
        print (input_df)
        print ('Regular Queues')
        print (regularqs)
        print ('DLQs')
        print (dmqs)

    # create semp handler -- see common/SimpleSempHandler.py
    semp_h = SempHandler.SempHandler(Cfg, Verbose)

    # create queue handlers
    queue_h = QueueConfig.Queues(semp_h, Cfg, regularqs, Verbose)
    dmqueue_h = QueueConfig.Queues(semp_h, Cfg, dmqs, Verbose)

    # create / update queues
    # Create DMQs followed by regular queues
    dmqueue_h.create_or_update_dmqueue ( r.patch_it)
    queue_h.create_or_update_queue   ( r.patch_it)
    
# Program entry point
if __name__ == "__main__":
    """ program entry point - must be  below main() """
    # Check if the current Python version meets the requirement
    if sys.version_info < MIN_PYTHON_VERSION:
        print(f"This script requires Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} or later.")
        print(f"Your Python version is {sys.version_info.major}.{sys.version_info.minor}.")
        sys.exit(1)  # Exit the script with a non-zero status code

    main(sys.argv[1:])