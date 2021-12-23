# This is the file that implements a flask server to do inferences. It's the file that you will modify to
# implement the scoring for your own algorithm.

from __future__ import print_function

import io, os
import flask
import numpy as np
import tensorflow as tf
from glob import glob
import json

# model の配置場所の設定、固定で 1.h5。model.tar.gzを解凍したもの
model_path = "/opt/ml/model"

saved_model_path = glob(f'{model_path}/**/**/saved_model.pb', recursive=True)[0].replace('saved_model.pb','')
tf.keras.models.load_model(saved_model_path)

class ScoringService(object):
    model = None  # Where we keep the model when it's loaded

    @classmethod
    def get_model(cls):
        """Get the model object for this instance, loading it if it's not already loaded."""
        if cls.model == None:
            cls.model = tf.keras.models.load_model(saved_model_path)
        return cls.model

    @classmethod
    def predict(cls, image_list):
        clf = cls.get_model()
        
        return clf.predict(image_list)


# The flask app for serving predictions
app = flask.Flask(__name__)


@app.route("/ping", methods=["GET"])
def ping():
    """Determine if the container is working and healthy. In this sample container, we declare
    it healthy if we can load the model successfully."""
    health = ScoringService.get_model() is not None  # You can insert a health check here

    status = 200 if health else 404
    return flask.Response(response="\n", status=status, mimetype="application/json")


@app.route("/invocations", methods=["POST"])
def transformation():
    data = None

    # Convert from CSV to pandas
    if flask.request.content_type == "application/json":
        data = flask.request.data.decode("utf-8")
        data = json.loads(data)['instances']
        print(data)
    else:
        return flask.Response(
            response=f"This predictor only supports csv data. Your request is {flask.request.content_type}", status=415, mimetype="text/plain"
        )
    
    pred_img_array = ScoringService.predict(data)
    result = json.dumps({'predictions':pred_img_array.tolist()})
    
    return flask.Response(response=result, status=200, mimetype="text/csv")
