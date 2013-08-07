#!/usr/bin/env python
# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */

import gzip
import json

import sys
sys.path = ["/usr/local/lib/ndns"] + sys.path

import os
from clint.textui import progress  

import ndns
import ndns.tools.create_zone
import ndns.tools.add
import ndns.tools.zone_info

class params (object):
    def __init__ (self, **kwargs):
        for param in kwargs:
            self.__setattr__ (param, kwargs.get (param))

    def __getattr__ (self, name):
        return None

# TOTAL servers:
# 1 (root)
# 13 (.com)
# 1 (all SLDs)

# ROOT SERVER (just one)
# .
# NS ns.root.
# ns.root. FH 0 0 /

os.mkdir ("root-ns")

ndns.tools.create_zone.create_zone (params (data_dir="root-ns", 
                                            default_ksk=True, 
                                            mname="ns", rname="root", ttl=3600,
                                            ksk_id="/DNS-ROOT/%00%01", zone="/"))

ndns.tools.add.add (params (data_dir="root-ns", zone="/", rr=".        IN NS ns.root."))
ndns.tools.add.add (params (data_dir="root-ns", zone="/", rr="ns.root. IN FH 0 0 /"))

# 13 COM server (the same config dir)
# .com
# NS ns1.com.
# NS ns2.com.
# NS ns3.com.
# NS ns4.com.
# NS ns5.com.
# NS ns6.com.
# NS ns7.com.
# NS ns8.com.
# NS ns9.com.
# NS ns10.com.
# NS ns11.com.
# NS ns12.com.
# NS ns13.com.

# ns1.com.  FH 0 0 /
# ns2.com.  FH 0 0 /
# ns3.com.  FH 0 0 /
# ns4.com.  FH 0 0 /
# ns5.com.  FH 0 0 /
# ns6.com.  FH 0 0 /
# ns7.com.  FH 0 0 /
# ns8.com.  FH 0 0 /
# ns9.com.  FH 0 0 /
# ns10.com.  FH 0 0 /
# ns11.com.  FH 0 0 /
# ns12.com.  FH 0 0 /
# ns13.com.  FH 0 0 /

os.mkdir ("com-ns")

ndns.tools.create_zone.create_zone (params (data_dir="com-ns", ksk_id="1", zsk_id="1", zone="/com", 
                                            mname="ns", rname="root", ttl=3600))

ndns.tools.add.add (params (data_dir="root-ns", zone="/",
                            rr=ndns.tools.zone_info.zone_info (params (data_dir="com-ns", ksk=True, zone="/com"))))

for i in xrange (1,14):
    ndns.tools.add.add (params (data_dir="root-ns", zone="/",    rr="com. IN NS ns%d.com." % i))
    ndns.tools.add.add (params (data_dir="com-ns",  zone="/com", rr="com. IN NS ns%d.com." % i))

# 1 "server" for all SLDs
#
# for sld in com:

#     sld + com

#     NS ns1 + sld + com

#     ns1 + sld + com  FH  /sld-ns   (separate route to an SLD-NS server, need extra route)
    
domains = json.load (gzip.open ('domain-map.json.gz'))
os.mkdir ("slds-ns");


pbar = progress.bar(range(len(domains['com'])))

count = 0

for sld,sub in domains['com'].iteritems ():
    if (sld == "__count__"):
        pbar.next ()
        continue
    
    if sub['__count__'] < 5:
        pbar.next ()
        continue
    
    sys.stdout.write('.')
    try:
        dns_domain = str("%s.com" % sld)
        ndn_domain = str("/com/%s" % sld)

        ndns.tools.create_zone.create_zone (params (commit=False, 
                                                    data_dir="slds-ns", ksk_id="1", zsk_id="1", 
                                                    zone=ndn_domain,
                                                    mname="ns", rname="root", ttl=3600))
        
        ndns.tools.add.add (params (commit=False, 
                                    data_dir="com-ns", zone="/com",
                                    rr=ndns.tools.zone_info.zone_info (params (data_dir="slds-ns", ksk=True, zone=ndn_domain))))
        
        ndns.tools.add.add (params (commit=False, 
                                    data_dir="com-ns",  zone="/com",     rr="%s. IN NS ns1.%s." % (dns_domain, dns_domain)))
        ndns.tools.add.add (params (commit=False, 
                                    data_dir="slds-ns", zone=ndn_domain, rr="@ IN NS ns1\n"
                                                                            "ns1 IN FH 0 0 /sld-ns"))
        
        
        if count > 500:
            ndns.ndns_session ("com-ns").commit ()
            ndns.ndns_session ("slds-ns").commit ()
            count = 0
        
        count += 1
        pbar.next ()

    except:
        pbar.next ()
        continue
