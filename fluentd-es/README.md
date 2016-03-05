To verify the working of log aggregation to elasticsearch, do
1) docker-compose up -d
2) docker exec -it <elasticsearch-container-id> /usr/share/elasticsearch/bin/plugin install mobz/elasticsearch-head
3) Hit the url http://192.168.99.100:49200/_plugin/head and check the es documents there
