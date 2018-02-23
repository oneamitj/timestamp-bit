#!/bin/bash
for (( wait=1; wait<=6; wait++ ))
do  
   sleep 10
   bitcoin-cli -datadir=/root/miner generate 3
   echo "Mine @ `date`"
done