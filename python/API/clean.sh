#!/bin/bash

input="/home/shengliu/Workspace/mininet/causalSDN/in.txt"
ps aux | grep ovs-vswitchd | grep root | awk '{print $2}'>"$input"
ps aux | grep ovsdb-server | grep root | awk '{print $2}'>>"$input"
while IFS= read -r var; do sudo kill -9 $var; done < "$input"

