from google.cloud import logging as glogging

def create_logger():
    """
    Integrates the Cloud Logging handler with the python logging module
    """
    # Instantiates a cloud logging client
    client = glogging.Client()

    # Retrieves a Cloud Logging handler based on the environment
    # you're running in and integrates the handler with the
    # Python logging module
    client.get_default_handler()
    client.setup_logging()