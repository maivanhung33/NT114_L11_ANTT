from datetime import datetime

from get_media.module.database import DB


def write_log(data, action, user=None):
    col = DB['log']
    data['time'] = int(datetime.now().timestamp())
    data['type'] = action
    data['user'] = user.__dict__ if user is not None and not isinstance(user, dict) else user
    col.insert_one(data)
