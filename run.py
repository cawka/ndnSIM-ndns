#!/usr/bin/env python
# -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-

from subprocess import call
from sys import argv
import os
import subprocess
import workerpool
import multiprocessing
import argparse

######################################################################
######################################################################
######################################################################

parser = argparse.ArgumentParser(description='Simulation runner')
parser.add_argument('scenarios', metavar='scenario', type=str, nargs='*',
                    help='Scenario to run')

parser.add_argument('-l', '--list', dest="list", action='store_true', default=False,
                    help='Get list of available scenarios')

parser.add_argument('-s', '--simulate', dest="simulate", action='store_true', default=False,
                    help='Run simulation and postprocessing (false by default)')

parser.add_argument('-p', '--postprocess', dest="postprocess", action='store_true', default=False,
                    help='Run postprocessing (false by default, always true if simulate is enabled)')

parser.add_argument('-g', '--no-graph', dest="graph", action='store_false', default=True,
                    help='Do not build a graph for the scenario (builds a graph by default)')

args = parser.parse_args()

if not args.list and len(args.scenarios)==0:
    print "ERROR: at least one scenario need to be specified"
    parser.print_help()
    exit (1)

if args.list:
    print "Available scenarios: "
else:
    if args.simulate:
        print "Simulating the following scenarios: " + ",".join (args.scenarios)

    if args.graph:
        print "Building graphs for the following scenarios: " + ",".join (args.scenarios)

######################################################################
######################################################################
######################################################################

class SimulationJob (workerpool.Job):
    "Job to simulate things"
    def __init__ (self, cmdline):
        self.cmdline = cmdline
    def run (self):
        print (" ".join (self.cmdline))
        subprocess.call (self.cmdline)

pool = workerpool.WorkerPool(size = 1)
# multiprocessing.cpu_count())

class Processor:
    def run (self):
        if args.list:
            print "    " + self.name
            return

        if "all" not in args.scenarios and self.name not in args.scenarios:
            return

        if args.list:
            pass
        else:
            if args.simulate:
                self.simulate ()
                pool.join ()
            if args.simulate or args.postprocess:
                self.postprocess ()
                pool.join ()
            if args.graph:
                self.graph ()

    def graph (self):
        subprocess.call ("./graphs/%s.R" % self.name, shell=True)

class AttNdnsSimulation (Processor):
    def __init__ (self, caches, sizes, runs):
        self.name = "att"
        self.caches = caches
        self.sizes = sizes
        self.runs = runs

    def simulate (self):
        for cache in self.caches:
            for size in self.sizes:
                for run in self.runs:
                    cmdline = ["./scenario-att.py",
                               "--cache=%s" % cache,
                               "--size=%d" % size,
                               "--run=%d" % run,
                               ]
                    job = SimulationJob (cmdline)
                    pool.put (job)

    def postprocess (self):
        print "Convert data to sqlite and reduce data size"

        summary_db = "results/summary-att.db"
        
        # subprocess.call ("rm -f \"%s\"" % summary_db, shell=True)
        # cmd = "sqlite3 -cmd \"create table data (Run text, Cache text, Size text, Node text, Face text, Type text, Packets integer)\" \"%s\" </dev/null" % summary_db
        # subprocess.call (cmd, shell=True)
        
        for cache in self.caches:
            for size in self.sizes:
                for run in self.runs:
                    name = "results/att/packets-run-%d-cache-%s-size-%d" % (run, cache, size)
                    print "Converting %s" % name

                    src = "%s.txt" % name
                    try:
                        cmd = "bzip2 %s" % src
                        subprocess.call (cmd, shell=True)
                    except:
                        pass
                    
                    src = "%s.txt.bz2" % name
                    
                    cmd = "bzcat \"%s\" | tail -n +2 | awk -F\"\t\" '{if (NF == 9) {print $1\"|\"$2\"|\"$4\"|\"$5\"|\"$8}}' | sqlite3 -cmd \"create table data_tmp (Time int, Node text, Face text, Type text, Packets real)\" -cmd \".import /dev/stdin data_tmp\" \"%s\"" % (src, summary_db)
                    subprocess.call (cmd, shell=True)

                    cmd = "sqlite3 -cmd \"create table data_tmp2 as select Time,Node,Face,Type,Packets from data_tmp where Type in ('InInterests','OutInterests','InData','OutData')\" -cmd \"vacuum\" \"%s\"  </dev/null" % summary_db
                    subprocess.call (cmd, shell=True)

                    cmd = "sqlite3 -cmd \"insert into data select '%d','%s','%d',Node,Face,Type,sum(Packets) from data_tmp2 group by Node,Face,Type\" -cmd \"drop table data_tmp2\" -cmd \"drop table data_tmp\" -cmd \"vacuum\" \"%s\"  </dev/null" % (run, cache, size, summary_db)
                    subprocess.call (cmd, shell=True)
                    

        
        summary2_db = "results/summary-cache-att.db"

        subprocess.call ("rm -f \"%s\"" % summary2_db, shell=True)
        cmd = "sqlite3 -cmd \"create table data (Run text, Cache text, Size text, Node text, Type text, Packets integer)\" \"%s\" </dev/null" % summary2_db
        subprocess.call (cmd, shell=True)

        for cache in self.caches:
            for size in self.sizes:
                for run in self.runs:
                    name = "results/att/cache-run-%d-cache-%s-size-%d" % (run, cache, size)
                    print "Converting %s" % name
                    
                    src = "%s.txt" % name
                    try:
                        cmd = "bzip2 %s" % src
                        subprocess.call (cmd, shell=True)
                    except:
                        pass
                    
                    src = "%s.txt.bz2" % name

                    cmd = "bzcat \"%s\" | tail -n +2 | awk -F\"\t\" '{if (NF == 4) {print $1\"|\"$2\"|\"$3\"|\"$4}}' | sqlite3 -cmd \"create table data_tmp (Time int, Node text, Type text, Packets real)\" -cmd \".import /dev/stdin data_tmp\" \"%s\"" % (src, summary2_db)
                    subprocess.call (cmd, shell=True)
                    
                    cmd = "sqlite3 -cmd \"insert into data select '%d','%s','%d',Node,Type,sum(Packets) from data_tmp group by Node,Type\" -cmd \"drop table data_tmp\" -cmd \"vacuum\" \"%s\"  </dev/null" % (run, cache, size, summary2_db)
                    subprocess.call (cmd, shell=True)
        
    def graph (self):
        print "Building graphs"

        cmdline = ["./graphs/requests-to-com.R"]
        job = SimulationJob (cmdline)
        pool.put (job)
        
        cmdline = ["./graphs/cache-performance.R"]
        job = SimulationJob (cmdline)
        pool.put (job)

try:
    AttNdnsSimulation (caches = ["Lru", "Lfu", "Random"],
                       sizes = [10, 100, 1000, 10000, 100000, 1000000],
                       runs = [1, 2, 3, 4, 5]).run ()

finally:
    pool.join ()
    pool.shutdown ()
