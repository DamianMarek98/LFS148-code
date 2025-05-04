# pyright: reportMissingTypeStubs=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportAttributeAccessIssue=false

import time

import requests
from client import ChaosClient, FakerClient
from flask import Flask, make_response, request, Response

import logging
from metric_utils import create_meter, create_request_instruments, create_resource_instruments

# global variables
app = Flask(__name__)
meter = create_meter("app.py", "0.1")

@app.route("/users", methods=["GET"])
def get_user():
    user, status = db.get_user(123)
    data = {}
    if user is not None:
        data = {"id": user.id, "name": user.name, "address": user.address}
    response = make_response(data, status)
    return response


def do_stuff():
    time.sleep(0.1)
    url = "http://localhost:6000/"
    response = requests.get(url)
    return response


@app.route("/")
def index():
    # request_instruments['index_counter'].add(1, { "http.request.method": request.method })
    do_stuff()
    current_time = time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime())
    return f"Hello, World! It's currently {current_time}"


@app.before_request
def before_request_func():
    workload_instruments["traffic_volume"].add(
        1, attributes={"http.route": request.path}
    )
    request.environ["request_start"] = time.time_ns()


@app.after_request
def after_request_func(response: Response) -> Response:
    workload_instruments["request_latency"].record(
        amount=(time.time_ns() - request.environ["request_start"]) / 1_000_000_000,
        attributes={
            "http.request.method": request.method,
            "http.route": request.path,
            "http.response.status_code": response.status_code,
        },
    )
    return response

if __name__ == "__main__":
    # disable logs of builtin webserver for load test
    logging.getLogger("werkzeug").disabled = True
    request_instruments = create_request_instruments(meter)
    workload_instruments = create_request_instruments(meter)
    create_resource_instruments(meter)
    db = ChaosClient(client=FakerClient())
    app.run(host="0.0.0.0", debug=True)
