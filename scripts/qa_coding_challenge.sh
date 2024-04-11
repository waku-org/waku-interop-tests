#!/bin/bash
printf "\nAssuming you already have a docker network called waku\n"
# if not something like this should create it: docker network create --driver bridge --subnet 172.18.0.0/16 --gateway 172.18.0.1 waku

printf "\nStarting containers\n"

container_id1=$(docker run -d -i -t \
    -p 21161:21161 \
    -p 21162:21162 \
    -p 21163:21163 \
    -p 21164:21164 \
    -p 21165:21165 \
    wakuorg/nwaku:v0.24.0 \
    --listen-address=0.0.0.0 \
    --rest=true \
    --rest-admin=true \
    --websocket-support=true \
    --log-level=TRACE \
    --rest-relay-cache-capacity=100 \
    --websocket-port=21163 \
    --rest-port=21161 \
    --tcp-port=21162 \
    --discv5-udp-port=21164 \
    --rest-address=0.0.0.0 \
    --nat=extip:172.18.111.226 \
    --peer-exchange=true \
    --discv5-discovery=true \
    --relay=true)

docker network connect --ip 172.18.111.226 waku $container_id1

printf "\nSleeping 2 seconds\n"
sleep 2

response=$(curl -X GET "http://127.0.0.1:21161/debug/v1/info" -H "accept: application/json")
enrUri=$(echo $response | jq -r '.enrUri')

container_id2=$(docker run -d -i -t \
    -p 22161:22161 \
    -p 22162:22162 \
    -p 22163:22163 \
    -p 22164:22164 \
    -p 22165:22165 \
    wakuorg/nwaku:v0.24.0 \
    --listen-address=0.0.0.0 \
    --rest=true \
    --rest-admin=true \
    --websocket-support=true \
    --log-level=TRACE \
    --rest-relay-cache-capacity=100 \
    --websocket-port=22163 \
    --rest-port=22161 \
    --tcp-port=22162 \
    --discv5-udp-port=22164 \
    --rest-address=0.0.0.0 \
    --nat=extip:172.18.111.227 \
    --peer-exchange=true \
    --discv5-discovery=true \
	--discv5-bootstrap-node=$enrUri \
    --relay=true)

docker network connect --ip 172.18.111.227 waku $container_id2

printf "\nSleeping 1 seconds\n"
sleep 1

printf "\nSubscribe\n"
curl -X POST "http://127.0.0.1:21161/relay/v1/auto/subscriptions" -H "accept: text/plain" -H "content-type: application/json" -d '["/my-app/2/chatroom-1/proto"]'
curl -X POST "http://127.0.0.1:22161/relay/v1/auto/subscriptions" -H "accept: text/plain" -H "content-type: application/json" -d '["/my-app/2/chatroom-1/proto"]'


printf "\nSleeping 60 seconds\n"
sleep 60

printf "\nRelay from NODE 1\n"                            
curl -X POST "http://127.0.0.1:21161/relay/v1/auto/messages" -H "content-type: application/json" -d '{"payload":"UmVsYXkgd29ya3MhIQ==","contentTopic":"/my-app/2/chatroom-1/proto","timestamp":0}'

printf "\nSleeping 1 seconds\n"
sleep 1

printf "\nCheck message in NODE 2\n"
response=$(curl -X GET "http://127.0.0.1:22161/relay/v1/auto/messages/%2Fmy-app%2F2%2Fchatroom-1%2Fproto" -H "Content-Type: application/json")

printf "\nResponse: $response\n"
if [ "$response" == "[]" ]; then
    echo "Error: NODE 2 didn't find the message"
    exit 1
else
    echo "Success: NODE 2 received the message"
fi