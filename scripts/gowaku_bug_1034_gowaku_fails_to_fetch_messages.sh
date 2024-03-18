#!/bin/bash
printf "\nAssuming you already have a docker network called waku\n"
# if not something like this should create it: docker network create --driver bridge --subnet 172.18.0.0/16 --gateway 172.18.0.1 waku


cluster_id=4
pubsub_topic="/waku/2/rs/$cluster_id/0"
encoded_pubsub_topic=$(echo "$pubsub_topic" | sed 's:/:%2F:g')
node_1=harbor.status.im/wakuorg/nwaku:latest
node_2=harbor.status.im/wakuorg/go-waku:latest

printf "\nStarting containers\n"

container_id1=$(docker run -d -i -t -p 12297:12297 -p 12298:12298 -p 12299:12299 -p 12300:12300 -p 12301:12301 $node_1 --listen-address=0.0.0.0 --rest=true --rest-admin=true --websocket-support=true --log-level=DEBUG --rest-relay-cache-capacity=100 --websocket-port=12299 --rest-port=12297 --tcp-port=12298 --discv5-udp-port=12300 --rest-address=0.0.0.0 --nat=extip:172.18.45.95 --peer-exchange=true --discv5-discovery=true --cluster-id=$cluster_id --relay=true --nodekey=30348dd51465150e04a5d9d932c72864c8967f806cce60b5d26afeca1e77eb68)
docker network connect --ip 172.18.45.95 waku $container_id1

printf "\nSleeping 2 seconds\n"
sleep 2

response=$(curl -X GET "http://127.0.0.1:12297/debug/v1/info" -H "accept: application/json")
enrUri=$(echo $response | jq -r '.enrUri')

container_id2=$(docker run -d -i -t -p 8158:8158 -p 8159:8159 -p 8160:8160 -p 8161:8161 -p 8162:8162 $node_2 --listen-address=0.0.0.0 --rest=true --rest-admin=true --websocket-support=true --log-level=DEBUG --rest-relay-cache-capacity=100 --websocket-port=8160 --rest-port=8158 --tcp-port=8159 --discv5-udp-port=8161 --rest-address=0.0.0.0 --nat=extip:172.18.207.159 --peer-exchange=true --discv5-discovery=true --cluster-id=$cluster_id --relay=true --discv5-bootstrap-node=$enrUri)

docker network connect --ip 172.18.207.159 waku $container_id2

printf "\nSleeping 1 seconds\n"
sleep 1

printf "\nSubscribe\n"
curl -X POST "http://127.0.0.1:12297/relay/v1/subscriptions" -H "Content-Type: application/json" -d "[\"$pubsub_topic\"]"
curl -X POST "http://127.0.0.1:8158/relay/v1/subscriptions" -H "Content-Type: application/json" -d "[\"$pubsub_topic\"]"


printf "\nSleeping 70 seconds\n"
sleep 70

printf "\nRelay from NODE 1\n"                            
curl -X POST "http://127.0.0.1:12297/relay/v1/messages/$encoded_pubsub_topic" -H "Content-Type: application/json" -d '{"payload": "UmVsYXkgd29ya3MhIQ==", "contentTopic": "/test/1/waku-relay/proto", "timestamp": '$(date +%s%N)'}'

printf "\nSleeping 1 seconds\n"
sleep 1

printf "\nCheck message in NODE 2\n"
response=$(curl -X GET "http://127.0.0.1:8158/relay/v1/messages/$encoded_pubsub_topic" -H "Content-Type: application/json")

printf "\nResponse: $response\n"

if [ "$response" == "no subscription found for pubsubTopic" ] || [ "$response" == "[]" ] || [ -z "$response" ] || [ "$response" == "null" ]; then
    printf "\nError: NODE 2 didn't find the message, the response is null, or the response contains the text 'null'\n"
    exit 1
else
    printf "\nSuccess: NODE 2 received the message\n"
fi

printf "\nUn-Subscribe NODE 2\n"
curl -X DELETE "http://127.0.0.1:8158/relay/v1/subscriptions" -H "Content-Type: application/json" -d "[\"$pubsub_topic\"]"

printf "\nSleeping 1 seconds\n"
sleep 1

printf "\nRelay from NODE 1\n"
curl -X POST "http://127.0.0.1:12297/relay/v1/messages/$encoded_pubsub_topic" -H "Content-Type: application/json" -d '{"payload": "UmVsYXkgd29ya3MhIQ==", "contentTopic": "/test/1/waku-relay/proto", "timestamp": '$(date +%s%N)'}'


printf "\nSleeping 1 seconds\n"
sleep 1

printf "\nCheck message in NODE 2\n"
response=$(curl -X GET "http://127.0.0.1:8158/relay/v1/messages/$encoded_pubsub_topic" -H "Content-Type: application/json")

printf "\nResponse: $response\n"

if [ "$response" == "no subscription found for pubsubTopic" ] || [ "$response" == "[]" ] || [ -z "$response" ] || [ "$response" == "null" ]; then
    printf "\nSuccess: NODE 2 didn't find the message\n"
else
    printf "\nError: NODE 2 received the message\n"
    exit 1
fi
