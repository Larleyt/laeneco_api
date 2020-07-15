import os
from flask import current_app as app
from flask import Blueprint
from flask import request, jsonify, abort, send_file, make_response
from werkzeug.utils import secure_filename
from gridfs.errors import NoFile
from bson import ObjectId
import uuid

from pkg.cnn_lung.model import load_and_predict
from pkg import utils


bp = Blueprint("api", __name__)


@bp.route("/api/cases", methods=["POST"])
def create_case():
    if request.method == "POST":
        if "file" not in request.files:
            abort(make_response(jsonify(error="No file provided in the request."), 400))

        file = request.files["file"]
        if file.filename == "":
            abort(make_response(jsonify(error="Empty filename."), 400))

        if not utils.allowed_file(file.filename):
            abort(make_response(jsonify(error="The file extension is not allowed."), 400))

        filename = secure_filename(file.filename)
        try:
            # incoming_file_id, user_id, side = os.path.splitext(filename)[0].split("_", 2)
            user_id, side = os.path.splitext(filename)[0].split("_", 1)
        except ValueError:
            unique_filename = "_".join([filename, str(uuid.uuid1())])
            file.save(os.path.join(
                app.config["PROJECT_ROOT"],
                app.config["DIR_UPLOAD_FAILED"],
                unique_filename
            ))
            abort(400, "Unable to parse user_id and side from the file name. Check the filename.")

        predict_result = load_and_predict(file)

        # Delete if exists
        # if app.config["fs"].exists(filename=filename):
        #     for grid_out in app.config["fs"].find(
        #             {"filename": filename},
        #             no_cursor_timeout=True):
        #         app.config["fs"].delete(grid_out._id)

        file_ob = app.config["fs"].put(
            file,
            filename=filename,
            content_type=file.content_type
        )
        upload_date = app.config["fs"].get(file_ob).upload_date
        case = {
            "user_id": user_id,
            "file_id": file_ob,
            "side": side,
            "filename": filename,
            "upload_date": upload_date,
            "result": str(predict_result) + "\n"
        }

        ret = app.config["db"].cases.insert_one(case)
        return utils.JSONEncoder().encode(case), 201


@bp.route("/api/users/<user_id>", methods=["GET"])
def get_measures_list_by_user(user_id):
    cases = [case for case in app.config["db"].cases.find({"user_id": user_id})]

    return utils.JSONEncoder().encode(cases), 200


@bp.route("/api/files/<file_id>", methods=["GET"])
def get_file_by_filename(file_id):
    try:
        grid_out = app.config["fs"].get(ObjectId(file_id))
    except NoFile:
        abort(make_response(jsonify(error="No such file."), 404))

    return send_file(
        grid_out,
        mimetype=grid_out.content_type,
        as_attachment=True,
        attachment_filename=grid_out.name
    )
