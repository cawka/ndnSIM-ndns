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

from ns.core import Config, StringValue, IntegerValue, Names
from ns.network import Node, NodeContainer, NodeList
from ns.point_to_point import PointToPointHelper
from ns.ndnSIM import ndn, AnnotatedTopologyReader

Config.SetDefault ("ns3::PointToPointNetDevice::DataRate", StringValue ("1Mbps"))
Config.SetDefault ("ns3::PointToPointChannel::Delay", StringValue ("10ms"))
Config.SetDefault ("ns3::DropTailQueue::MaxPackets", StringValue ("20"))

Config.SetGlobal ("ndn::WireFormat", IntegerValue (ndn.Wire.WIRE_FORMAT_CCNB))

def getSimpleTopology (numNodes = 3):
    # Creating nodes
    nodes = NodeContainer ()
    nodes.Create (numNodes)

    # Connecting nodes using two links
    p2p = PointToPointHelper ()
    for i in xrange (1, numNodes):
        p2p.Install (nodes.Get (i-1), nodes.Get (i))

    # // Install NDN stack on all nodes
    ndnHelper = ndn.StackHelper ()
    # ndnHelper.SetDefaultRoutes (True)
    ndnHelper.SetForwardingStrategy ("ns3::ndn::fw::BestRoute", "","", "","", "","", "","")
    ndnHelper.SetContentStore ("ns3::ndn::cs::Lru::Freshness", "MaxSize", "100", "","", "","", "","")
    ndnHelper.InstallAll ()

def getLargeTopology (cache = "Lru", size = "1000"):
    topologyReader = AnnotatedTopologyReader ("", 1.0)
    topologyReader.SetFileName ("topology/7018.r0.txt")
    topologyReader.Read ()

    # // Install NDN stack on all nodes
    ndnHelper = ndn.StackHelper ()
    # ndnHelper.SetDefaultRoutes (True)
    ndnHelper.SetForwardingStrategy ("ns3::ndn::fw::BestRoute", "","", "","", "","", "","")
    ndnHelper.SetContentStore ("ns3::ndn::cs::%s" % cache, "MaxSize", size, "","", "","", "","")
    ndnHelper.InstallAll ()

    topologyReader.ApplyOspfMetric ();

def getClientsGatewaysBackbones ():
    leaves = NodeContainer ()
    gw = NodeContainer ()
    bb = NodeContainer ()

    for nodeId in xrange (0, NodeList.GetNNodes ()):
        node = NodeList.GetNode (nodeId)
        name = Names.FindName (node)

        if name[0:5] == "leaf-":
            leaves.Add (node)
        elif name[0:3] == "gw-":
            gw.Add (node)
        elif name[0:3] == "bb-":
            bb.Add (node)

    return leaves, gw, bb

def getNode (node):
    if isinstance (node, str):
        raise TypeError ("Not supported type [%s]" % type (node))
        # return Names.FindNode (node)
    elif isinstance (node, int):
        return NodeList.GetNode (node)
    elif isinstance (node, Node):
        return node
    else:
        raise TypeError ("Not supported type [%s]" % type (node))

def getContext (node):
    if isinstance (node, int):
        return node
    elif isinstance (node, str):
        raise TypeError ("Not supported type [%s]" % type (node))
        # return Names.FindNode (node).GetId ()
    elif isinstance (node, Node):
        return node.GetId ()
    else:
        raise TypeError ("Not supported type [%s]" % type (node))
