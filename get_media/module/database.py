import os

from pymongo import MongoClient


def database() -> MongoClient:
    host = os.environ.get('MONGO_HOST') or ''

    port = os.environ.get('MONGO_PORT') or 27017

    max_pool_size = os.environ.get('MONGO_MAX_POOL_SIZE') or 100

    username = os.environ.get('MONGO_USER') or ''

    password = os.environ.get('MONGO_PASSWORD') or ''

    db = os.environ.get('MONGO_DB') or ''

    auth_source = os.environ.get('MONGO_AUTH_SOURCE') or ''

    auth_mechanism = os.environ.get('MONGO_AUTH_MECHANISM') or ''

    client = MongoClient(host=host, port=port, username=username, password=password, maxPoolSize=max_pool_size,
                         authMechanism=auth_mechanism, authSource=auth_source)[db]
    # client['user'].create_index([('phone', 1), ('type', 1)], unique=True)
    # client['user'].create_index([('type', 1), ('verified', 1), ('is_active', 1)])
    #
    # client['collection'].create_index([('owner_phone', 1), ('name', 1)], unique=True)
    #
    # client['collection_item'].create_index([('collection_id', 1), ('id', 1), ('owner_phone', 1)], unique=True)
    #
    # client['media'].create_index([('srcUrl', 1), ('limit', 1), ('first', 1)], unique=True)
    # client['media'].create_index('_expireAt', expireAfterSeconds=60)
    #
    # client['log'].create_index([('type', 1)])
    #
    # print('Done')
    return client


DB = database()
