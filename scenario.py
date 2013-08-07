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

from ns.core import *
from ns.network import *
from ns.ndnSIM import *
from ns.point_to_point import *

class MyApp:
    def __init__ (self):
        self.datas = 0
        self.timeouts = 0

    def StartApplication (self, app):
        print "START APP"
        self.face = ndn.ApiFace (app.GetNode ())

        Simulator.Schedule (Seconds (1), self.TestSending)

    def StopApplication (self, app):
        print "STOP APP"

        self.face = None

    def TestSending (self):
        interest = ndn.Interest ()
        interest.SetName (ndn.Name ("/test"))
        interest.SetInterestLifetime (Seconds (1.0))

        def onData (interest, data):
            print "data"
            pass

        def onTimeout (interest):
            print "timeout"
            pass

        self.face.ExpressInterest (interest, onData, onTimeout)

Config.SetDefault ("ns3::PointToPointNetDevice::DataRate", StringValue ("1Mbps"))
Config.SetDefault ("ns3::PointToPointChannel::Delay", StringValue ("10ms"))
Config.SetDefault ("ns3::DropTailQueue::MaxPackets", StringValue ("20"))

Config.SetDefault ("ns3::ndn::Face::WireFormat", StringValue ("1"))

# Creating nodes
nodes = NodeContainer ()
nodes.Create (3)

# Connecting nodes using two links
p2p = PointToPointHelper ()
p2p.Install (nodes.Get (0), nodes.Get (1))
p2p.Install (nodes.Get (1), nodes.Get (2))

# // Install NDN stack on all nodes
ndnHelper = ndn.StackHelper ()
ndnHelper.SetDefaultRoutes (True)
ndnHelper.InstallAll ()

# Installing applications

appHelper = ndn.AppHelper ("ns3::CallbackBasedApp")
apps = appHelper.Install (nodes.Get (0))
app = apps.Get (0)

pyapp = MyApp ()
app.SetOnStartCallback (pyapp.StartApplication)
app.SetOnStopCallback (pyapp.StopApplication)

# Producer
appHelper = ndn.AppHelper ("ns3::ndn::Producer");
# Producer will reply to all requests starting with /prefix
appHelper.SetPrefix ("/");
appHelper.SetAttribute ("Postfix", StringValue ("/unique/postfix"))
appHelper.SetAttribute ("PayloadSize", StringValue("1024"))
apps = appHelper.Install (nodes.Get (2))


apps.Stop (Seconds (4.0))

# Simulator.Stop (Seconds (10))
# Simulator.Run ()
# Simulator.Destroy ()

import visualizer
visualizer.start ()
