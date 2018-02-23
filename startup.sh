echo "Start bitcoin server. CMD: bitcoind -daemon"
bitcoind -daemon
echo "Start bitcoin miner server. CMD: bitcoind -datadir=/root/miner -daemon"
bitcoind -datadir=/root/miner -daemon
echo "Wait for bitcoin to start. CMD: sleep 9"
sleep 9
echo "Generate 50 BTC for server node. CMD: bitcoin-cli generate 1"
bitcoin-cli generate 1
echo "Generate 103 Block by miner. CMD: bitcoin-cli -datadir=/root/miner generate 103"
bitcoin-cli -datadir=/root/miner generate 103
echo "Start miner CRON. CMD: cron"
cron
echo "Pre-setting up Flask helper. CMD: cd /root/webapp && export LC_ALL=C.UTF-8 && export LANG=C.UTF-8"
cd /root/webapp
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
echo "Check if poc.db exist. CMD: if [[ ! -f 'poc.db' ]]"
# if [[ ! -f "poc.db" ]]; then 
    echo "Check for poc.db & initdb. CMD: FLASK_APP=server.py flask initdb"
    FLASK_APP=server.py flask initdb
# fi
echo "Start Flask server in background @0.0.0.0:8080. CMD: python3 server.py &> /var/log/flask.log &"
python3 server.py &> /var/log/flask.log &
echo "Start OTS server. CMD: /root/opentimestamps-server/./otsd --btc-regtest --btc-min-confirmations 3 --btc-min-tx-interval 60"
/root/opentimestamps-server/./otsd --btc-regtest --btc-min-confirmations 3 --btc-min-tx-interval 60