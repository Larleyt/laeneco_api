import json
from uuid import UUID
from bson import ObjectId
from flask import current_app as app
from datetime import date, datetime


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (ObjectId, UUID)):
            return str(obj)

        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)
