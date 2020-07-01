import os
from flask import Flask
from pkg.config import Config
from flask_pymongo import PyMongo
# from pkg.cnn_lung.model import load_model
import gridfs


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config.from_envvar("LAENECO_SETTINGS")
    from .resources import bp
    app.register_blueprint(bp)

    # Init db
    mongo = PyMongo(app)
    fs = gridfs.GridFS(mongo.db, collection="fs")
    app.config["db"] = mongo.db
    app.config["fs"] = fs

    # # Init model
    # model_path = os.path.join(app.config["PROJECT_ROOT"], "pkg/cnn_lung/vclf.pkl")
    # app.config["model"] = load_model(model_path)
    return app
