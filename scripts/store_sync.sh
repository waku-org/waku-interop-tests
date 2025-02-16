#!/bin/bash
printf "\nAssuming you already have a docker network called waku\n"
# if not something like this should create it: docker network create --driver bridge --subnet 172.18.0.0/16 --gateway 172.18.0.1 waku


cluster_id=3
pubsub_topic="/waku/2/rs/$cluster_id/0"
encoded_pubsub_topic=$(echo "$pubsub_topic" | sed 's:/:%2F:g')
content_topic="/test/1/store/proto"
encoded_content_topic=$(echo "$content_topic" | sed 's:/:%2F:g')
node_1=wakuorg/nwaku:latest
node_1_ip=172.18.64.13
node_1_rest=32261
node_1_tcp=32262
node_2=wakuorg/nwaku:latest
node_2_ip=172.18.64.14
node_2_rest=7588
node_3=wakuorg/nwaku:latest
node_3_ip=172.18.64.15
node_3_rest=8588


printf "\nStarting containers\n"

container_id1=$(docker run -d -i -t -p $node_1_rest:$node_1_rest -p $node_1_tcp:$node_1_tcp -p 32263:32263 -p 32264:32264 -p 32265:32265 $node_1              --listen-address=0.0.0.0 --rest=true --rest-admin=true --websocket-support=true --log-level=TRACE --rest-relay-cache-capacity=100 --websocket-port=32263 --rest-port=$node_1_rest --tcp-port=$node_1_tcp --discv5-udp-port=32264 --rest-address=0.0.0.0 --nat=extip:$node_1_ip    --peer-exchange=true --discv5-discovery=true --cluster-id=$cluster_id --nodekey=4fa0fd1b13b89ba45dd77037b6cac09bb5ccdc0df8fab44efeb066da2a378744 --shard=0 --metrics-server=true --metrics-server-address=0.0.0.0 --metrics-server-port=19552 --metrics-logging=true --store=true --store-sync=true --relay=true --lightpush=true)
docker network connect --ip $node_1_ip waku $container_id1

printf "\nSleeping 2 seconds\n"
sleep 2

response=$(curl -X GET "http://127.0.0.1:$node_1_rest/debug/v1/info" -H "accept: application/json")
enrUri=$(echo $response | jq -r '.enrUri')

# Extract the first non-WebSocket address
ws_address=$(echo $response | jq -r '.listenAddresses[] | select(contains("/ws") | not)')

# Check if we got an address, and construct the new address with it
if [[ $ws_address != "" ]]; then
    identifier=$(echo $ws_address | awk -F'/p2p/' '{print $2}')
    if [[ $identifier != "" ]]; then
        multiaddr_with_id="/ip4/${node_1_ip}/tcp/${node_1_tcp}/p2p/${identifier}"
        echo $multiaddr_with_id
    else
        echo "No identifier found in the address."
        exit 1
    fi
else
    echo "No non-WebSocket address found."
    exit 1
fi

container_id2=$(docker run -d -i -t -p $node_2_rest:$node_2_rest -p 4589:4589 -p 4590:4590 -p 4591:4591 -p 4592:4592 $node_2 --listen-address=0.0.0.0 --rest=true --rest-admin=true --websocket-support=true --log-level=TRACE --rest-relay-cache-capacity=100 --websocket-port=4590 --rest-port=$node_2_rest --tcp-port=4589 --discv5-udp-port=4591 --rest-address=0.0.0.0 --nat=extip:$node_2_ip --peer-exchange=true --discv5-discovery=true --cluster-id=$cluster_id --nodekey=0efae97aa2a5303aa77dc27d11d47bbbe0ddb8b55eeceaeb61de2ec5efe7e2a5 --shard=0 --metrics-server=true --metrics-server-address=0.0.0.0 --metrics-server-port=4592 --metrics-logging=true --store=true --store-sync=true --relay=false --lightpush=true --storenode=$multiaddr_with_id --discv5-bootstrap-node=$enrUri --lightpushnode=$multiaddr_with_id)

docker network connect --ip $node_2_ip waku $container_id2

printf "\nSleeping 1 seconds\n"
sleep 1

printf "\nConnect peers\n"
curl -X POST "http://127.0.0.1:$node_2_rest/admin/v1/peers" -H "Content-Type: application/json" -d "[\"$multiaddr_with_id\"]"

container_id3=$(docker run -d -i -t -p $node_3_rest:$node_3_rest -p 5589:5589 -p 5590:5590 -p 5591:5591 -p 5592:5592 $node_3 --listen-address=0.0.0.0 --rest=true --rest-admin=true --websocket-support=true --log-level=TRACE --rest-relay-cache-capacity=100 --websocket-port=5590 --rest-port=$node_3_rest --tcp-port=5589 --discv5-udp-port=5591 --rest-address=0.0.0.0 --nat=extip:$node_3_ip --peer-exchange=true --discv5-discovery=true --cluster-id=$cluster_id --nodekey=0efae97aa2a5303aa77dc27d11d47bbbe0ddb8b55eeceaeb61de2ec5efe7e2a8 --shard=0 --metrics-server=true --metrics-server-address=0.0.0.0 --metrics-server-port=5592 --metrics-logging=true --store=true --store-sync=true --relay=true --storenode=$multiaddr_with_id --discv5-bootstrap-node=$enrUri)
docker network connect --ip $node_3_ip waku $container_id3

printf "\nSleeping 1 seconds\n"
sleep 1

printf "\nConnect peers\n"
curl -X POST "http://127.0.0.1:$node_3_rest/admin/v1/peers" -H "Content-Type: application/json" -d "[\"$multiaddr_with_id\"]"

printf "\nSubscribe\n"
curl -X POST "http://127.0.0.1:$node_1_rest/relay/v1/subscriptions" -H "Content-Type: application/json" -d "[\"$pubsub_topic\"]"
curl -X POST "http://127.0.0.1:$node_3_rest/relay/v1/subscriptions" -H "Content-Type: application/json" -d "[\"$pubsub_topic\"]"


printf "\nSleeping 1 seconds\n"
sleep 1

printf "\nRelay from NODE 3\n"
curl -X POST "http://127.0.0.1:$node_3_rest/relay/v1/messages/$encoded_pubsub_topic" \
-H "Content-Type: application/json" \
-d '{"payload": "UmVsYXkgd29ya3MhIQ==", "contentTopic": "'"$content_topic"'", "timestamp": '$(date +%s%N)'}'

printf "\nLightpush from NODE 2\n"                           
curl -v -X POST "http://127.0.0.1:$node_2_rest/lightpush/v1/message" -H "Content-Type: application/json" -d '{"pubsubTopic": "'"$pubsub_topic"'", "message": {"payload": "TGlnaHQgcHVzaCB3b3JrcyEh", "contentTopic": "'"$content_topic"'", "timestamp": '$(date +%s%N)'}}'


printf "\nSleeping 1 seconds\n"
sleep 1


printf "\nCheck message was stored in NODE 1 (relay) with v1 API\n"
response=$(curl -X GET "http://127.0.0.1:$node_1_rest/store/v1/messages?contentTopics=$encoded_content_topic&pageSize=5&ascending=true")
printf "\nResponse: $response\n"

printf "\nCheck message was stored in NODE 3 (relay) with v1 API\n"
response=$(curl -X GET "http://127.0.0.1:$node_3_rest/store/v1/messages?contentTopics=$encoded_content_topic&pageSize=5&ascending=true")
printf "\nResponse: $response\n"

printf "\nSleeping 10 seconds\n"
sleep 10

printf "\nCheck message was stored in NODE 2 (lightpush) with v3 API\n"
response=$(curl -X GET "http://127.0.0.1:$node_2_rest/store/v3/messages?contentTopics=$encoded_content_topic&pageSize=5&ascending=true")
printf "\nResponse: $response\n"