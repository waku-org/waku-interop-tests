#!/bin/bash
printf "\nAssuming you already have a docker network called waku\n"
# if not something like this should create it: docker network create --driver bridge --subnet 172.18.0.0/16 --gateway 172.18.0.1 waku


cluster_id=2
pubsub_topic="/waku/2/rs/$cluster_id/0"
node_1=harbor.status.im/wakuorg/nwaku:latest
node_2=harbor.status.im/wakuorg/nwaku:latest
ext_ip="172.18.204.9"
tcp_port="37344"

printf "\nStarting containers\n"

container_id1=$(docker run -d -i -t -p 37343:37343 -p $tcp_port:$tcp_port -p 37345:37345 -p 37346:37346 -p 37347:37347 $node_1 --listen-address=0.0.0.0 --rest=true --rest-admin=true --websocket-support=true --log-level=TRACE --rest-relay-cache-capacity=100 --websocket-port=37345 --rest-port=37343 --tcp-port=$tcp_port --discv5-udp-port=37346 --rest-address=0.0.0.0 --nat=extip:$ext_ip --peer-exchange=true --discv5-discovery=true --cluster-id=$cluster_id --metrics-server=true --metrics-server-address=0.0.0.0 --metrics-server-port=37347 --metrics-logging=true --pubsub-topic=/waku/2/rs/2/0 --lightpush=true --relay=true)
docker network connect --ip $ext_ip waku $container_id1

printf "\nSleeping 2 seconds\n"
sleep 2

response=$(curl -X GET "http://127.0.0.1:37343/debug/v1/info" -H "accept: application/json")
enrUri=$(echo $response | jq -r '.enrUri')

# Extract the first non-WebSocket address
ws_address=$(echo $response | jq -r '.listenAddresses[] | select(contains("/ws") | not)')

# Check if we got an address, and construct the new address with it
if [[ $ws_address != "" ]]; then
    identifier=$(echo $ws_address | awk -F'/p2p/' '{print $2}')
    if [[ $identifier != "" ]]; then
        multiaddr_with_id="/ip4/${ext_ip}/tcp/${tcp_port}/p2p/${identifier}"
        echo $multiaddr_with_id
    else
        echo "No identifier found in the address."
        exit 1
    fi
else
    echo "No non-WebSocket address found."
    exit 1
fi

container_id2=$(docker run -d -i -t -p 25908:25908 -p 25909:25909 -p 25910:25910 -p 25911:25911 -p 25912:25912 $node_2 --listen-address=0.0.0.0 --rest=true --rest-admin=true --websocket-support=true --log-level=DEBUG --rest-relay-cache-capacity=100 --websocket-port=25910 --rest-port=25908 --tcp-port=25909 --discv5-udp-port=25911 --rest-address=0.0.0.0 --nat=extip:172.18.141.214 --peer-exchange=true --discv5-discovery=true --cluster-id=$cluster_id --min-relay-peers-to-publish=1 --rest-filter-cache-capacity=50 --pubsub-topic=/waku/2/rs/2/0 --lightpush=true --relay=false --discv5-bootstrap-node=$enrUri --lightpushnode=$multiaddr_with_id)

docker network connect --ip 172.18.141.214 waku $container_id2

printf "\nSleeping 10 seconds\n"
sleep 10

printf "\nSubscribe\n"
curl -v -X POST "http://127.0.0.1:37343/relay/v1/subscriptions" -H "Content-Type: application/json" -d '["/waku/2/rs/2/0"]'


printf "\nSleeping 2 seconds\n"
sleep 2

printf "\nLightpush message on subscribed pubusub topic\n"                            
curl -v -X POST "http://127.0.0.1:25908/lightpush/v1/message" -H "Content-Type: application/json" -d '{"pubsubTopic": "/waku/2/rs/2/0", "message": {"payload": "TGlnaHQgcHVzaCB3b3JrcyEh", "contentTopic": "/myapp/1/latest/proto", "timestamp": 1712149720320589312}}'
printf "\nLightpush message on non subscribed pubusub topic\n"                            
curl -v -X POST "http://127.0.0.1:25908/lightpush/v1/message" -H "Content-Type: application/json" -d '{"pubsubTopic": "/waku/2/rs/2/1", "message": {"payload": "TGlnaHQgcHVzaCB3b3JrcyEh", "contentTopic": "/myapp/1/latest/proto", "timestamp": 1712149720320589312}}'