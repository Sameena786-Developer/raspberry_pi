import paho.mqtt.client as mqtt

broker = "broker.hivemq.com"
port = 1883
topic = "enerlytix/room1"

client = mqtt.Client()
client.connect(broker, port, 60)

client.publish(topic, "Hello from Python")

print("Message sent successfully!")

client.disconnect()