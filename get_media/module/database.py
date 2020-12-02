import os

from pymongo import MongoClient


def database() -> MongoClient:
    host = os.environ.get('MONGO_HOST') or 'localhost'

    port = os.environ.get('MONGO_PORT') or 27017

    max_pool_size = os.environ.get('MONGO_MAX_POOL_SIZE') or 100

    username = os.environ.get('MONGO_USER') or 'meete'

    password = os.environ.get('MONGO_PASSWORD') or 'p4ssw0rd'

    db = os.environ.get('MONGO_DB') or 'do_an_chuyen_nganh'

    auth_source = os.environ.get('MONGO_AUTH_SOURCE') or 'mongo'

    auth_mechanism = os.environ.get('MONGO_AUTH_MECHANISM') or 'SCRAM-SHA-256'

    env = os.environ.get('ENV') or 'local'

    # For local
    if env == 'local':
        client = MongoClient(host=host, port=port, username=username, password=password, maxPoolSize=max_pool_size,
                             authMechanism=auth_mechanism, authSource=auth_source)[db]
        return client

    if env == 'pro':
        client = MongoClient("mongodb+srv://{}:{}@{}/{}?retryWrites=true&w=majority".format(username,
                                                                                            password,
                                                                                            host,
                                                                                            db))[db]
        return client
