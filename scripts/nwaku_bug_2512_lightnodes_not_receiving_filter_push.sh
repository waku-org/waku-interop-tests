#!/bin/bash
echo "Assuming you already have a docker network called waku"
# if not something like this should create it: docker network create --driver bridge --subnet 172.18.0.0/16 --gateway 172.18.0.1 waku

echo "Starting containers"

container_id1=$(docker run -d -i -t -p 41717:41717 -p 41718:41718 -p 41719:41719 -p 41720:41720 -p 41721:41721 wakuorg/nwaku:latest --listen-address=0.0.0.0 --rest=true --rest-admin=true --websocket-support=true --log-level=TRACE --rest-relay-cache-capacity=100 --websocket-port=41719 --rest-port=41717 --tcp-port=41718 --discv5-udp-port=41720 --rest-address=0.0.0.0 --nat=extip:172.18.223.170 --peer-exchange=true --discv5-discovery=true --cluster-id=0 --metrics-server=true --metrics-server-address=0.0.0.0 --metrics-server-port=41721 --metrics-logging=true --relay=true --filter=true --nodekey=30348dd51465150e04a5d9d932c72864c8967f806cce60b5d26afeca1e77eb68)
docker network connect --ip 172.18.223.170 waku $container_id1

container_id2=$(docker run -d -i -t -p 10628:10628 -p 10629:10629 -p 10630:10630 -p 10631:10631 -p 10632:10632 wakuorg/nwaku:latest --listen-address=0.0.0.0 --rest=true --rest-admin=true --websocket-support=true --log-level=TRACE --rest-relay-cache-capacity=100 --websocket-port=10630 --rest-port=10628 --tcp-port=10629 --discv5-udp-port=10631 --rest-address=0.0.0.0 --nat=extip:172.18.249.98 --peer-exchange=true --discv5-discovery=true --cluster-id=0 --metrics-server=true --metrics-server-address=0.0.0.0 --metrics-server-port=10632 --metrics-logging=true --relay=false --filter=true --discv5-bootstrap-node=enr:-Kq4QEXWJfpPEPrBCJlgXGla9FJiEzYKM6P8DuVyQbGyl_-POLWKvQgMQEZDF3tDPTIdUKqCI8i2GG0MW2FsOkAtoW0BgmlkgnY0gmlwhKwS36qKbXVsdGlhZGRyc4wACgSsEt-qBqL33QOJc2VjcDI1NmsxoQM3Tqpf5eFn4Jztm4gB0Y0JVSJyxyZsW8QR-QU5DZb-PYN0Y3CCovaDdWRwgqL4hXdha3UyBQ --filternode=/ip4/172.18.223.170/tcp/41718/p2p/16Uiu2HAmGNtM2rQ8abySFNhqPDFY4cmfAEpfo9Z9fD3NekoFR2ip)
docker network connect --ip 172.18.249.98 waku $container_id2

container_id3=$(docker run -d -i -t -p 12108:12108 -p 12109:12109 -p 12110:12110 -p 12111:12111 -p 12112:12112 wakuorg/go-waku:latest --listen-address=0.0.0.0 --rest=true --rest-admin=true --websocket-support=true --log-level=DEBUG --rest-relay-cache-capacity=100 --websocket-port=12110 --rest-port=12108 --tcp-port=12109 --discv5-udp-port=12111 --rest-address=0.0.0.0 --nat=extip:172.18.102.113 --peer-exchange=true --discv5-discovery=true --cluster-id=0 --min-relay-peers-to-publish=1 --rest-filter-cache-capacity=50 --relay=false --filter=true --discv5-bootstrap-node=enr:-Kq4QEXWJfpPEPrBCJlgXGla9FJiEzYKM6P8DuVyQbGyl_-POLWKvQgMQEZDF3tDPTIdUKqCI8i2GG0MW2FsOkAtoW0BgmlkgnY0gmlwhKwS36qKbXVsdGlhZGRyc4wACgSsEt-qBqL33QOJc2VjcDI1NmsxoQM3Tqpf5eFn4Jztm4gB0Y0JVSJyxyZsW8QR-QU5DZb-PYN0Y3CCovaDdWRwgqL4hXdha3UyBQ --filternode=/ip4/172.18.223.170/tcp/41718/p2p/16Uiu2HAmGNtM2rQ8abySFNhqPDFY4cmfAEpfo9Z9fD3NekoFR2ip)
docker network connect --ip 172.18.102.113 waku $container_id3

container_id4=$(docker run -d -i -t -p 6707:6707 -p 6708:6708 -p 6709:6709 -p 6710:6710 -p 6711:6711 wakuorg/go-waku:latest --listen-address=0.0.0.0 --rest=true --rest-admin=true --websocket-support=true --log-level=DEBUG --rest-relay-cache-capacity=100 --websocket-port=6709 --rest-port=6707 --tcp-port=6708 --discv5-udp-port=6710 --rest-address=0.0.0.0 --nat=extip:172.18.156.205 --peer-exchange=true --discv5-discovery=true --cluster-id=0 --min-relay-peers-to-publish=1 --rest-filter-cache-capacity=50 --relay=false --filter=true --discv5-bootstrap-node=enr:-Kq4QEXWJfpPEPrBCJlgXGla9FJiEzYKM6P8DuVyQbGyl_-POLWKvQgMQEZDF3tDPTIdUKqCI8i2GG0MW2FsOkAtoW0BgmlkgnY0gmlwhKwS36qKbXVsdGlhZGRyc4wACgSsEt-qBqL33QOJc2VjcDI1NmsxoQM3Tqpf5eFn4Jztm4gB0Y0JVSJyxyZsW8QR-QU5DZb-PYN0Y3CCovaDdWRwgqL4hXdha3UyBQ --filternode=/ip4/172.18.223.170/tcp/41718/p2p/16Uiu2HAmGNtM2rQ8abySFNhqPDFY4cmfAEpfo9Z9fD3NekoFR2ip)
docker network connect --ip 172.18.156.205 waku $container_id4

container_id5=$(docker run -d -i -t -p 30889:30889 -p 30890:30890 -p 30891:30891 -p 30892:30892 -p 30893:30893 wakuorg/go-waku:latest --listen-address=0.0.0.0 --rest=true --rest-admin=true --websocket-support=true --log-level=DEBUG --rest-relay-cache-capacity=100 --websocket-port=30891 --rest-port=30889 --tcp-port=30890 --discv5-udp-port=30892 --rest-address=0.0.0.0 --nat=extip:172.18.161.78 --peer-exchange=true --discv5-discovery=true --cluster-id=0 --min-relay-peers-to-publish=1 --rest-filter-cache-capacity=50 --relay=false --filter=true --discv5-bootstrap-node=enr:-Kq4QEXWJfpPEPrBCJlgXGla9FJiEzYKM6P8DuVyQbGyl_-POLWKvQgMQEZDF3tDPTIdUKqCI8i2GG0MW2FsOkAtoW0BgmlkgnY0gmlwhKwS36qKbXVsdGlhZGRyc4wACgSsEt-qBqL33QOJc2VjcDI1NmsxoQM3Tqpf5eFn4Jztm4gB0Y0JVSJyxyZsW8QR-QU5DZb-PYN0Y3CCovaDdWRwgqL4hXdha3UyBQ --filternode=/ip4/172.18.223.170/tcp/41718/p2p/16Uiu2HAmGNtM2rQ8abySFNhqPDFY4cmfAEpfo9Z9fD3NekoFR2ip)
docker network connect --ip 172.18.161.78 waku $container_id5

echo "Sleeping 20 seconds"
sleep 20

echo "Subscribe"
curl -v -X POST "http://127.0.0.1:41717/relay/v1/subscriptions" -H "Content-Type: application/json" -d '["/waku/2/rs/3/1"]'
curl -v -X POST "http://127.0.0.1:10628/filter/v2/subscriptions" -H "Content-Type: application/json" -d '{"requestId": "aa7ae897-e14b-494a-b1c5-a5c69488ced0", "contentFilters": ["/test/1/waku-filter/proto"], "pubsubTopic": "/waku/2/rs/3/1"}'
curl -v -X POST "http://127.0.0.1:12108/filter/v2/subscriptions" -H "Content-Type: application/json" -d '{"requestId": "497fb697-4e1c-443b-b681-7c90f7e406bb", "contentFilters": ["/test/1/waku-filter/proto"], "pubsubTopic": "/waku/2/rs/3/1"}'
curl -v -X POST "http://127.0.0.1:6707/filter/v2/subscriptions" -H "Content-Type: application/json" -d '{"requestId": "bb2137a4-3d63-4afd-bc40-78eba0af4167", "contentFilters": ["/test/1/waku-filter/proto"], "pubsubTopic": "/waku/2/rs/3/1"}'
curl -v -X POST "http://127.0.0.1:30889/filter/v2/subscriptions" -H "Content-Type: application/json" -d '{"requestId": "cbd1d59a-8989-4dc3-83a4-b6859e08cadf", "contentFilters": ["/test/1/waku-filter/proto"], "pubsubTopic": "/waku/2/rs/3/1"}'

echo "Sleeping 5 seconds"
sleep 5

echo "Relay from NODE 1"
curl -v -X POST "http://127.0.0.1:41717/relay/v1/messages/%2Fwaku%2F2%2Frs%2F0%2F1" -H "Content-Type: application/json" -d '{"payload": "RmlsdGVyIHdvcmtzISE=", "contentTopic": "/test/1/waku-filter/proto", "timestamp": '$(date +%s%N)'}'

echo "Sleeping 2 seconds"
sleep 2

echo "Check message in NODE 2"
response=$(curl -v -X GET "http://127.0.0.1:10628/filter/v2/messages/%2Ftest%2F1%2Fwaku-filter%2Fproto" -H "Content-Type: application/json")

if [ "$response" == "[]" ]; then
    echo "Error: NODE 2 didn't find the message"
    exit 1
else
    echo "Success: NODE 2 received the message"
fi

echo "Check message in NODE 3"
response=$(curl -v -X GET "http://127.0.0.1:12108/filter/v2/messages/%2Fwaku%2F2%2Frs%2F0%2F1/%2Ftest%2F1%2Fwaku-filter%2Fproto" -H "Content-Type: application/json")

if [ "$response" == "[]" ]; then
    echo "Error: NODE 3 didn't find the message"
    exit 1
else
    echo "Success: NODE 3 received the message"
fi

echo "Check message in NODE 4"
response=$(curl -v -X GET "http://127.0.0.1:6707/filter/v2/messages/%2Fwaku%2F2%2Frs%2F0%2F1/%2Ftest%2F1%2Fwaku-filter%2Fproto" -H "Content-Type: application/json")

if [ "$response" == "[]" ]; then
    echo "Error: NODE 4 didn't find the message"
    exit 1
else
    echo "Success: NODE 4 received the message"
fi

echo "Check message in NODE 5"
response=$(curl -v -X GET "http://127.0.0.1:30889/filter/v2/messages/%2Fwaku%2F2%2Frs%2F0%2F1/%2Ftest%2F1%2Fwaku-filter%2Fproto" -H "Content-Type: application/json")

if [ "$response" == "[]" ]; then
    echo "Error: NODE 5 didn't find the message"
    exit 1
else
    echo "Success: NODE 5 received the message"
fi