#!/usr/bin/env python3

import sys
import re

def parse_time(s):
    res = re.match(".*@([0-9]+\.[0-9]+):.*", s)
    return float(res[1])

fname = "qemu.log"
alldata = open(fname, "r").read().split("\n")
alldata = list(filter(lambda x: x, alldata))
entries = 5
output = "output.txt"
fd = open(output, "w")
# { "kvm": xxx, "vhost": xxx, "total": xxx, ... }
stat = { "copy_bitmap": 0, "total": 0 }
count = 0

while alldata:
    data = alldata[0:5]
    alldata = alldata[5:]
    start = parse_time(data[0])
    end = parse_time(data[-1])
    lines = data[1:-1]
    last = start

    for line in lines:
        try:
            result = re.match(".*@([0-9]+\.[0-9]+):.*listener '(.*)' synced.*", line)
            name = result[2]
            time = float(result[1])
        except Exception as e:
            print("ERROR line: %s" % line)
            exit(1)
        us = ((time - last) * 1000000)
        fd.write("%d\t" % us)
        if name not in stat:
            stat[name] = 0
        stat[name] += us
        #print("Sync process %15s took: \t%d usec." % (name, us))
        last = time

    us = ((end - last) * 1000000)
    fd.write("%d\t" % us)
    stat["copy_bitmap"] += us
    #print("Sync migration dirty bitmap took: \t%d usec." % us)
    us = ((end - start) * 1000000)
    fd.write("%d\n" % us)
    stat["total"] += us
    #print("Total time used to sync took: \t\t%d usec." % us)
    count += 1

for key in stat.keys():
    stat[key] = int(stat[key] / count)

print("summary: %s" % stat)
print("output.txt written.")
fd.close()
