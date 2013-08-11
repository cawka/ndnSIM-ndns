#!/usr/bin/env python
# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */

import gzip
import re
import sys
import json
import dns.name

print "Disabled"
exit (1)

f = gzip.open ("time-name-type.trace.gz")
qout = gzip.open ("time-name-type-sanitized.trace.gz", "wt")

# limit = 0

domains = {}

for line in f:
    time, domain, rrtype, not_used = re.split("\s+", line)

    dns_domain = dns.name.from_text (domain.lower ())
    if len (dns_domain) < 2 or len (dns_domain) > 4:
        continue

    if (dns_domain[-2] != "com"):
        continue

    try:
        for d in dns_domain[:-1]:
            tmp = unicode (d)
    except UnicodeDecodeError:
        print "Error with: [%s]" % dns_domain
        continue
        
    # limit += 1

    # if limit > 10000:
    #     break

    qout.write ("%s\t%s\t%s\n" % (time, domain, rrtype))
    
    record = domains
    for d in reversed (dns_domain[:-1]):
        try:
            record = record[unicode(d)]
            record['__count__'] += 1
        except KeyError:
            record[d] = {"__count__": 1}
            record = record[unicode(d)]

outf = gzip.open ("domain-map.json.gz", "w")

json.dump (domains, outf, indent=1, sort_keys=True)
