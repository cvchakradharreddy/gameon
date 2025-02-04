from google.cloud import storage

bucket_name = "talkgame"

def get_storage_client():
    return storage.Client()

def get_bucket():
    return get_storage_client().bucket(bucket_name)