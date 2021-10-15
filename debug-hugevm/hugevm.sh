#!/bin/bash

bin=~/git/qemu/bin/x86_64-softmmu/qemu-system-x86_64
sudo $bin -M q35 -accel kvm -msg timestamp=on \
     -global migration.x-max-bandwidth=1000000000 \
     -global migration.x-downtime-limit=0 \
     -m 130G,slots=2,maxmem=160G \
     -object memory-backend-ram,size=2G,id=m0 \
     -object memory-backend-ram,size=128G,id=m1,reserve=no \
     -numa node,nodeid=0,memdev=m0 \
     -numa node,nodeid=1,memdev=m1 \
     -smp 2,sockets=2 \
     -trace enable="migration_bitmap_sync*" \
     -trace enable="memory_region_sync*" \
     -name peter-vm,debug-threads=on \
     -monitor stdio \
     -netdev user,id=net0,hostfwd=tcp::5555-:22 $@ \
     -device virtio-net-pci,netdev=net0 \
     -netdev tap,id=net1,script=no,downscript=no,vhostforce=on \
     -device virtio-net-pci,netdev=net1 \
     -drive file=/home/images/default.qcow2,if=none,cache=none,id=drive0 \
     -device virtio-blk,drive=drive0
