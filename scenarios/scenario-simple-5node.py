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
args = parser.parse_args()

if not args.debug:
    from _simulation_hacks import logging_
######################################################################

from _simulation_hacks import time_

import functools
import logging
import sys
import copy

import topology
from ns.core import Simulator, Seconds
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

topology.getSimpleTopology (5)

class Daemon (NdnsDaemon):
    def Run (self, context):
        self.run ()
        # super (self, Daemon).run ()

    def Shutdown (self, context):
        # super (self, Daemon).shutdown ()
        self.terminate ()

root_daemon = Daemon (data_dir = "input/root-ns", scopes = [], enable_dyndns = False)
com_daemon = Daemon (data_dir = "input/com-ns", scopes = [], enable_dyndns = False)
slds_daemon = Daemon (data_dir = "input/slds-ns", scopes = ["/sld-ns"], enable_dyndns = False)

class Digger (object):
    def __init__ (self):
        self.cachingQuery = ndns.query.CachingQuery ()
        self.policy = copy.copy (ndns.TrustPolicy)

    def Run (self, context):
        dig (Params (zone="/com/cnn", zone_fh_query=True, verify = False, no_output = True),
             sys.stdout, cachingQuery = self.cachingQuery, policy = self.policy)

dig1 = Digger ()
dig2 = Digger ()

Simulator.ScheduleWithContext (topology.getContext (0), Seconds (0.0), root_daemon.Run)
Simulator.ScheduleWithContext (topology.getContext (0), Seconds (0.0), com_daemon.Run)
# Simulator.ScheduleWithContext (topology.getContext (0), Seconds (0.0), slds_daemon.Run)
# Simulator.ScheduleWithContext (topology.getContext (0), Seconds (8.0), root_daemon.Shutdown)

Simulator.ScheduleWithContext (topology.getContext (4), Seconds (1.0), dig1.Run)
Simulator.ScheduleWithContext (topology.getContext (4), Seconds (5.0), dig2.Run)

routing = ndn.GlobalRoutingHelper ()
routing.InstallAll ()
routing.AddOrigin ("/DNS", topology.getNode (0))
routing.AddOrigin ("/com/DNS", topology.getNode (0))

routing.CalculateRoutes ()

ndn.CsTracer.InstallAll ("results/cs-trace.txt", Seconds (1));

Simulator.Stop (Seconds (10))
Simulator.Run ()
Simulator.Destroy ()

# # exit (1)

# import visualizer
# visualizer.start ()
