#!/usr/bin/env python
# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (c) 2013, Regents of the University of California
#                     Alexander Afanasyev
#
# BSD license, See the doc/LICENSE file for more information
#
# Author: Alexander Afanasyev <alexander.afanasyev@ucla.edu>
#

import sys
sys.path = ["/usr/local/lib/ndnSIM", "/usr/local/lib/ndns"] + sys.path

from _simulation_hacks import time_

######################################################################

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--debug', dest='debug', action='store_true', default=False,
                    help='''Enable logging (otherwise it will be hacked and completely disabled)''')
parser.add_argument('--run', '-r', dest='run', type=int, default=1,
                    help='''Simulation run (default 1)''')
args = parser.parse_args()

if not args.debug:
    from _simulation_hacks import logging_
######################################################################

from _simulation_hacks import time_

import functools
import logging
import copy
import os
import glob

import topology
from ns.core import Simulator, Seconds, Config, IntegerValue
from ns.ndnSIM import ndn

from ndns.tools import Params
from ndns.tools.ndns_daemon import NdnsDaemon
from ndns.tools.dig import dig

import ndns.query

######################################################################
######################################################################

_LOG = logging.getLogger ("")
_LOG.setLevel (logging.DEBUG)

logging.getLogger ("ndn.nre").setLevel (logging.ERROR)

_handler = logging.StreamHandler (sys.stderr)
_handler.setFormatter (logging.Formatter('%(asctime)s %(name)s [%(levelname)s]  %(message)s', '%H:%M:%S'))
_LOG.addHandler (_handler)

######################################################################
######################################################################

Config.SetGlobal ("RngRun", IntegerValue (args.run))

topology.getLargeTopology ()

clients, gw, bb = topology.getClientsGatewaysBackbones ()

routing = ndn.GlobalRoutingHelper ()
routing.InstallAll ()

class Daemon (NdnsDaemon):
    def __init__ (self, node, daemonType):
        if daemonType == "root":
            super (Daemon, self).__init__ (data_dir = "input/root-ns", scopes = [], enable_dyndns = False)
            routing.AddOrigin ("/DNS", topology.getNode (node))
        elif daemonType == "com":
            super (Daemon, self).__init__ (data_dir = "input/com-ns", scopes = [], enable_dyndns = False)
            routing.AddOrigin ("/com/DNS", topology.getNode (node))
        else:
            raise TypeError ("daemonType can be either 'root' or 'com' for now")

        Simulator.ScheduleWithContext (topology.getContext (node), Seconds (0), self.Run)
        
    def Run (self, context):
        self.run ()
        # super (self, Daemon).run ()

    def Shutdown (self, context):
        # super (self, Daemon).shutdown ()
        self.terminate ()

class Digger (object):
    def __init__ (self, node, start):
        self.cachingQuery = ndns.query.CachingQuery ()
        self.policy = copy.copy (ndns.TrustPolicy)

        Simulator.ScheduleWithContext (topology.getContext (node), Seconds (start), self.Run)

    def Run (self, context):
        dig (Params (zone="/com/cnn", zone_fh_query=True, verify = False, no_output = True),
             sys.stdout, cachingQuery = self.cachingQuery, policy = self.policy)

root_daemon = Daemon (0, "root")
com_daemon = Daemon (0, "com")

dig1 = Digger (4, 1.0)
dig2 = Digger (4, 5.0)



routing.CalculateRoutes ()

try: os.makedirs ("results/att")
except: pass
ndn.CsTracer.InstallAll ("results/att/cache-run-%d.txt" % args.run, Seconds (10));

Simulator.Stop (Seconds (10.01))
Simulator.Run ()
Simulator.Destroy ()

# # exit (1)

# import visualizer
# visualizer.start ()
