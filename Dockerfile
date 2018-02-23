FROM ubuntu:16.04

# add bitcoind from the official PPA
RUN sed -i 's|http://archive|http://np.archive|g' /etc/apt/sources.list
# RUN cat /etc/apt/sources.list
RUN apt-get update
# RUN apt-get install --yes software-properties-common
# RUN add-apt-repository --yes ppa:bitcoin/bitcoin
# RUN apt-get update

# install bitcoind (from PPA) and make
# RUN apt-get install --yes bitcoind make

RUN apt-get install --yes software-properties-common
RUN add-apt-repository --yes ppa:bitcoin/bitcoin
RUN apt-get update
RUN apt-get install --yes python3 python3-pip
RUN apt-get install --yes git
RUN apt-get install --yes bitcoind bitcoin-tx
RUN apt-get install cron

# OTS Server
RUN mkdir -p /root/.otsd/calendar/
RUN echo "http://127.0.0.1:14788" > /root/.otsd/calendar/uri
WORKDIR /root/.otsd/calendar/
RUN dd if=/dev/random of=/root/.otsd/calendar/hmac-key bs=32 count=1

WORKDIR /root
RUN git clone https://github.com/opentimestamps/opentimestamps-server.git
RUN pip3 install -r opentimestamps-server/requirements.txt

# OTS Client
RUN pip3 install opentimestamps opentimestamps-client
# RUN git clone https://github.com/opentimestamps/opentimestamps-client.git
# RUN pip3 install -r opentimestamps-client/requirements.txt
# RUN git clone https://github.com/opentimestamps/python-opentimestamps.git

RUN mkdir -p /root/.bitcoin/regtest
RUN mkdir -p /root/miner/regtest
COPY ./regtest /root/.bitcoin/regtest
COPY ./regtest /root/miner/regtest
COPY ./bitcoin_admin.conf /root/.bitcoin/bitcoin.conf
COPY ./bitcoin_miner.conf /root/miner/bitcoin.conf

# Flask App
COPY ./webapp /root/webapp
RUN pip3 install -r /root/webapp/requirements.txt

# Miner CRON Job
COPY ./miner.sh /miner.sh
ADD crontab /etc/cron.d/miner
RUN chmod 0644 /etc/cron.d/miner
RUN chmod +x /miner.sh
RUN touch /var/log/cron.log

COPY ./startup.sh /root/startup.sh
RUN chmod +x /root/startup.sh
EXPOSE 8080

# CMD ["bitcoind"]
CMD ["bash", "startup.sh"]
