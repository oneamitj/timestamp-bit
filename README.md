Timestamp any item info in a bitcoin (regtest) node and track timestamp info with data integrity.
System implemented in python3 & flask and deployed via docker.

Hosted bitcoin regtest with default node and miner node.
On docker deploy:

- Start bitcoin regtest default node
- Start bitcoin regtest miner node at /root/miner
- Generates 1 Block by default node to get 50BTC
- Generates 103 Blocks so that bitcoin distributes mined BTC
- Start cron job that mines 3 Block every 10sec
- Init db and Create flask app @ 0.0.0.0:8080
- Start OpenTimeStamps server

# OTS Usage

- Start container with bitcoin daemon

        docker run -d --name otscontainer ots

- Access otscontainer bash

        docker exec -it otscontainer bash

- All task is done within container
- Open multiple otscontainer bash instance each for `OTSserver`, `OTSclient` and `bitcoin-cli`

- Start miner daemon

        bitcoind -datadir=/root/miner -daemon

- Accumulate some coins in admin node

        bitcoin-cli generate 101

- Start OTS local server on one bash (inside )
    
        ./otsd --btc-regtest --btc-min-confirmations 3 --btc-min-tx-interval 60

- TimeStamp FILE in another bash
    
        ots --wait --verbose stamp -c http://localhost:14788 -m 1 FILE

- Generate Blocks for timestamp in third bash using miner account
    
        bitcoin-cli -datadir=/root/miner generate 3

- Upgrade if --wait is not used (sync bitcoin chain)
    
        ots --btc-regtest -l http://127.0.0.1:14788 upgrade FILE.ots 

- Verify Timestamp
    
        ots --btc-regtest -l http://127.0.0.1:14788 verify FILE.ots
