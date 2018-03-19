#bin/bash

ovs-ofctl add-flow "arp,priority=1,in_port=1,actions=2,3"
