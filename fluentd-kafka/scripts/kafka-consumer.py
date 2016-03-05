from kafka import KafkaConsumer

# To consume latest messages and auto-commit offsets
consumer = KafkaConsumer('log',
                         group_id='my-group',
                         auto_offset_reset='smallest',
                         bootstrap_servers=['192.168.99.100:9092'])
for message in consumer:
    # message value and key are raw bytes -- decode if necessary!
    # e.g., for unicode: `message.value.decode('utf-8')`
    print("%s:%d:%d: key=%s value=%s" %
          (message.topic, message.partition, message.offset,
           message.key.decode('utf-8'), message.value.decode('utf-8')))
