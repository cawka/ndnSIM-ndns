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

import time_

import functools
import logging
import sys

import topology
from ns.core import Simulator, Seconds

from ndns.tools import Params
from ndns.tools.ndns_daemon import NdnsDaemon
from ndns.tools.dig import dig

######################################################################
######################################################################

_LOG = logging.getLogger ("")
_LOG.setLevel (logging.DEBUG)

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

def run_dig (context):
    dig (Params (simple=True, raw=True, verbose=True, zone="/DNS/com/NS"), sys.stdout)

Simulator.ScheduleWithContext (topology.getContext (0), Seconds (0.0), root_daemon.Run)
Simulator.ScheduleWithContext (topology.getContext (0), Seconds (8.0), root_daemon.Shutdown)

Simulator.ScheduleWithContext (topology.getContext (4), Seconds (1.0), run_dig)

Simulator.Stop (Seconds (10))
Simulator.Run ()
Simulator.Destroy ()

# import visualizer
# visualizer.start ()
