from google.cloud import pubsub_v1
import json

def publish_message(finding_type, mode, resource_id, project_id, message_info, topic_id):
    """
    Publishes message to Pub/Sub topic for integration into alerting system.
    """

    # Create Pub/Sub Client
    pub_client = pubsub_v1.PublisherClient()

    message = {
        "finding": finding_type,
        "mode": mode,
		"resourceId": resource_id,
		"project_id": project_id,
		"message": message_info
    }

    message_json = json.dumps(message)

    # Create topic object
    topic = pub_client.topic_path(project_id, topic_id)

    # Pub/Sub messages must be a bytestring
    data = message_json.encode("utf-8")
    
    # Publish message
    pub_client.publish(topic, data)
