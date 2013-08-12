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
import re
import gzip
from clint.textui import progress

import topology
from ns.core import Simulator, Seconds, Config, IntegerValue, BooleanValue, Time, Names
from ns.network import NodeContainer, NodeList
from ns.ndnSIM import L2RateTracer, ndn as ndnSIM
import ndn

from ndns.tools import Params
from ndns.tools.ndns_daemon import NdnsDaemon
from ndns.tools.dig import dig
from ndns.dnsifier import ndnify

import ndns.query

######################################################################
######################################################################

_LOG = logging.getLogger ("")
_LOG.setLevel (logging.DEBUG)

logging.getLogger ("ndn.nre").setLevel (logging.ERROR)

_handler = logging.StreamHandler (sys.stderr)

class Formatter (object):
    def format (self, record):
        print "%f\t%s" % (Simulator.Now ().ToDouble (Time.S), record.msg)
x = Formatter ()
        
# _handler.setFormatter (logging.Formatter('%(asctime)s %(name)s [%(levelname)s]  %(message)s')) #, '%H:%M:%S'))
_handler.setFormatter (x)
_LOG.addHandler (_handler)

######################################################################
######################################################################

Config.SetGlobal ("RngRun", IntegerValue (args.run))

Config.SetDefault ("ns3::ndn::ForwardingStrategy::DetectRetransmissions", BooleanValue (False))

topology.getLargeTopology ()

clients, gw, bb = topology.getClientsGatewaysBackbones ()

routing = ndnSIM.GlobalRoutingHelper ()
routing.InstallAll ()

##########################################################################
##########################################################################

class Daemon (NdnsDaemon):
    def __init__ (self, node, daemonType):
        self.node = node
        if daemonType == "root":
            super (Daemon, self).__init__ (data_dir = "input/root-ns", scopes = [], enable_dyndns = False)
            routing.AddOrigin ("/DNS", self.node)
            print "ROOT NS on [%s]" % Names.FindName (self.node)
        elif daemonType == "com":
            super (Daemon, self).__init__ (data_dir = "input/com-ns", scopes = [], enable_dyndns = False)
            routing.AddOrigin ("/com/DNS", self.node)
            print "COM NS on [%s]" % Names.FindName (self.node)
        else:
            raise TypeError ("daemonType can be either 'root' or 'com' for now")

        Simulator.ScheduleWithContext (self.node.GetId (), Seconds (0), self.Run)

    def Run (self, context):
        super (Daemon, self).run ()

    def Shutdown (self, context):
        super (Daemon, self).terminate ()

##########################################################################
##########################################################################
COUNTER = 0
SCHEDULED = 0

def getCacheSize ():
    totalSize = 0
    for i in xrange (0, NodeList.GetNNodes ()):
        node = NodeList.GetNode (i)
        store = ndnSIM.ContentStore.GetContentStore (node)
        totalSize += store.GetSize ()

    return totalSize

def test ():
    print "%s Total Cache size: [%d]" % (Simulator.Now ().ToDouble (Time.S), getCacheSize ())
    # print x

    Simulator.Schedule (Seconds (100.0), test)


class Digger (object):
    def __init__ (self, node, inputTrace):
        self.node = node
        # self.cachingQuery = ndns.query.NonCachingQuery ()
        self.cachingQuery = ndns.query.CachingQuery ()
        self.policy = 1
        # copy.copy (ndns.TrustPolicy)
        self.inputTrace = gzip.open (inputTrace)
        self.inputTraceName = inputTrace

        Simulator.ScheduleWithContext (self.node.GetId (), Seconds (0), self.init)
        print "Digger on [%s]" % Names.FindName (self.node)

        self.scheduledEvents = 0

    def init (self, context):
        self.face = ndn.Face ()
        self.scheduleNext ()

    def scheduleNext (self, *kw, **kwargs):
        global SCHEDULED
        try:
            while self.scheduledEvents < 100:
                line = self.inputTrace.next ()
                time, domain, rrtype, not_used = re.split("\s+", line)

                rel_time = Seconds (10*(float (time)-1273795499)) - Simulator.Now ()
                if rel_time.IsNegative ():
                    print "TIME IS NEGATIVE. WRONG!!!"
                    exit (1)
                Simulator.Schedule (rel_time, self.Run, domain)
                
                self.scheduledEvents += 1
                SCHEDULED += 1

        except StopIteration:
            print "Done with [%s]" % self.inputTraceName


    def onResult (self, result, msg):
        self.scheduledEvents -= 1
        self.scheduleNext ()

    def onError (self, errmsg, *k, **kw):
        self.scheduledEvents -= 1
        self.scheduleNext ()

    # def onPreResult (self, result, msg):
    #     def _onVerify (data, status):
    #         if status:
    #             self.onResult (result, msg)
    #         else:
    #             self.onError ("Got answer, but it cannot be verified")

    #     self.policy.verifyAsync (self.face, result, _onVerify)

    def Run (self, domain, *kw, **kwargs):
        global COUNTER, SCHEDULED

        sld_zone = ndn.Name (ndnify (domain.lower ())[0:2])
        if len(sld_zone) != 2:
            self.scheduleNext ()

        COUNTER += 1
        if (COUNTER % 500 == 0):
            print "%s Procesed: [%d], total scheduled: [%d], cache size: [%d]" % (Simulator.Now ().ToDouble (Time.S), COUNTER, SCHEDULED, getCacheSize ())

        if COUNTER > 500000:
            print "(SPECIAL) Done with [%s]" % self.inputTraceName
            return

        # _LOG.debug (sld_zone)
        self.cachingQuery.expressQueryForZoneFh (self.face, self.onResult, self.onError, sld_zone, verify = False)

##########################################################################
##########################################################################

input_data = "input/run-%d" % args.run

ns_servers = []
ns_nodes = NodeContainer ()
diggers = []
digger_nodes = NodeContainer ()

for root_ns in glob.glob ("%s/root-ns-*" % input_data):
    node = re.sub (r'^.*/root-ns-(.+)\.txt.*$', r'\1', root_ns)
    ns_nodes.Add (bb.Get (int (node)))
    ns_servers.append (Daemon (bb.Get (int (node)), "root"))

for com_ns in glob.glob ("%s/com-ns-*" % input_data):
    node = re.sub (r'^.*/com-ns-(.+)\.txt.*$', r'\1', com_ns)
    ns_nodes.Add (bb.Get (int (node)))
    ns_servers.append (Daemon (bb.Get (int (node)), "com"))

for digger in glob.glob ("%s/dig-*" % input_data):
    node = re.sub (r'^.*/dig-(.+)\.txt.*$', r'\1', digger)
    ns_nodes.Add (clients.Get (int (node)))
    diggers.append (Digger (clients.Get (int (node)), digger))

##########################################################################
##########################################################################

    
routing.CalculateRoutes ()

try: os.makedirs ("results/att")
except: pass
ndnSIM.CsTracer.InstallAll ("results/att/cache-run-%d.txt" % args.run, Seconds (10));

ndnSIM.L3RateTracer.Install (NodeContainer (ns_nodes, digger_nodes), "results/att/packets-run-%d.txt" % args.run, Seconds (10));

# L2RateTracer.InstallAll ("drop-trace.txt", Seconds (800));

# Simulator.Schedule (Seconds (100.0), test)

Simulator.Stop (Seconds (1000.01))

Simulator.Run ()
Simulator.Destroy ()

# # exit (1)

# import visualizer
# visualizer.start ()
