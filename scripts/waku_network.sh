#!/bin/bash
printf "\nAssuming you already have a docker network called waku\n"
# if not something like this should create it: docker network create --driver bridge --subnet 172.18.0.0/16 --gateway 172.18.0.1 waku

cluster_id=4
pubsub_topic="/waku/2/rs/$cluster_id/0"
encoded_pubsub_topic=$(echo "$pubsub_topic" | sed 's:/:%2F:g')
node_1=wakuorg/go-waku:latest
node_2=wakuorg/go-waku:latest
node_1_ip=172.18.45.95

printf "\nStarting Bootstrap Node\n"
container_id1=$(docker run -d -i -t -p 12297:12297 -p 12298:12298 -p 12299:12299 -p 12300:12300 -p 12301:12301 $node_1 --listen-address=0.0.0.0 --rest=true --rest-admin=true --websocket-support=true --log-level=DEBUG --rest-relay-cache-capacity=100 --websocket-port=12299 --rest-port=12297 --tcp-port=12298 --discv5-udp-port=12300 --rest-address=0.0.0.0 --nat=extip:$node_1_ip --peer-exchange=true --discv5-discovery=true --cluster-id=$cluster_id --relay=true --store=true --nodekey=30348dd51465150e04a5d9d932c72864c8967f806cce60b5d26afeca1e77eb68)
docker network connect --ip $node_1_ip waku $container_id1
sleep 1

info1=$(curl -X GET "http://127.0.0.1:12297/debug/v1/info" -H "accept: application/json")
enrUri=$(echo $info1 | jq -r '.enrUri')

printf "\nStarting Second Node\n"
container_id2=$(docker run -d -i -t -p 8158:8158 -p 8159:8159 -p 8160:8160 -p 8161:8161 -p 8162:8162 $node_2 --listen-address=0.0.0.0 --rest=true --rest-admin=true --websocket-support=true --log-level=DEBUG --rest-relay-cache-capacity=100 --websocket-port=8160 --rest-port=8158 --tcp-port=8159 --discv5-udp-port=8161 --rest-address=0.0.0.0 --nat=extip:172.18.207.159 --peer-exchange=true --discv5-discovery=true --cluster-id=$cluster_id --relay=true --discv5-bootstrap-node=$enrUri)
docker network connect --ip 172.18.207.159 waku $container_id2
sleep 1

printf "\nSubscribe\n"
curl -X POST "http://127.0.0.1:12297/relay/v1/subscriptions" -H "Content-Type: application/json" -d "[\"$pubsub_topic\"]"
curl -X POST "http://127.0.0.1:8158/relay/v1/subscriptions" -H "Content-Type: application/json" -d "[\"$pubsub_topic\"]"
sleep 0.1

printf "\nRelay from NODE1\n"                            
curl -X POST "http://127.0.0.1:12297/relay/v1/messages/$encoded_pubsub_topic" -H "Content-Type: application/json" -d '{"payload": "UmVsYXkgd29ya3MhIQ==", "contentTopic": "/test/1/waku-relay/proto", "timestamp": '$(date +%s%N)'}'
sleep 0.1

printf "\nCheck message in NODE2\n"
response=$(curl -X GET "http://127.0.0.1:8158/relay/v1/messages/$encoded_pubsub_topic" -H "Content-Type: application/json")

printf "\nResponse: $response\n\n"

printf "NODE1 INFO: $info1\n\n"

printf "NODE1 ENR: $enrUri\n\n"

# Extract the first non-WebSocket address
ws_address=$(echo $info1 | jq -r '.listenAddresses[] | select(contains("/ws") | not)')

# Check if we got an address, and construct the new address with it
if [[ $ws_address != "" ]]; then
    identifier=$(echo $ws_address | awk -F'/p2p/' '{print $2}')
    if [[ $identifier != "" ]]; then
        multiaddr_with_id="/ip4/${node_1_ip}/tcp/${node_1_tcp}/p2p/${identifier}"
        printf "NODE1 MULTIADDRESS: $multiaddr_with_id\n\n"
        enrUri=$(echo $info1 | jq -r '.enrUri')
    else
        echo "No identifier found in the address."
        exit 1
    fi
else
    echo "No non-WebSocket address found."
    exit 1
fi

