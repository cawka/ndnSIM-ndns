#!/usr/bin/env python
# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */

import gzip
import re
import sys
import random
import os

from ns.core import Config, IntegerValue, UniformVariable

f = gzip.open ("time-name-type-sanitized.trace.gz")


######################################################################

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--clients', dest='clients', type=int,
                    help='''Number clients to split input to''')
parser.add_argument('--maxclients', dest='maxclients', type=int,
                    help='''Maximum number of clients (if clients < maxclients, client IDs will be randomized)''')
parser.add_argument('--maxbbs', dest='maxbbs', type=int,
                    help='''Maximum number of backbones, so the positions of the ROOT and COM NS will be properly randomized''')
parser.add_argument('--run', '-r', dest='run', type=int, default=1,
                    help='''Simulation run (default 1)''')
args = parser.parse_args()

if not args.clients:
    print "ERROR: Please provide the number of clients to split trace into"
    exit (1)

if args.maxclients is None:
    args.maxclients = args.clients

if args.maxbbs is None:
    print "ERROR: Please specify the number of the backbone nodes"
    exit (1)
    
if args.maxclients < args.clients:
    print "ERROR: Number of clients is larger than the maximum number of clients???"
    exit (1)
######################################################################

os.makedirs ("run-%d" % args.run)

Config.SetGlobal ("RngRun", IntegerValue (args.run))

randVar = UniformVariable ()
client_ids = [i for i in xrange (0, args.maxclients)]
random.shuffle (client_ids, randVar.GetValue)

bb_ids = [i for i in xrange (0, args.maxbbs)]
random.shuffle (bb_ids, randVar.GetValue)

open ("run-%d/root-ns-%d.txt" % (args.run, bb_ids[0]), 'wt')
for i in xrange (0, 13):
    open ("run-%d/com-ns-%d.txt" % (args.run, bb_ids[1+i]), 'wt')

outputs = []

for i in xrange (0, args.clients):
    out = gzip.open ("run-%d/dig-%d.txt.gz" % (args.run, client_ids[i]), 'wt')
    outputs.append (out)

for line in f:
    time, domain, rrtype, not_used = re.split("\s+", line)

    out = outputs [randVar.GetInteger (0, len(outputs)-1)]
    out.write ("%s\t%s\t%s\n" % (time, domain, rrtype))
