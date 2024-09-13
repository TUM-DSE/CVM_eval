import datetime
import os
import sys
import uuid
from bottle import route, run, request
from pathlib import Path


@route("/alive", method="POST")
def alive():
    env = request.POST

    path = Path(env.CODE_LOCATION)
    for part in path.parts:
        if part == "cache":
            relative_path = Path(*path.parts[path.parts.index(part) :])
            break
    code_location = Path("/share/benchmarks/sebs/serverless-benchmarks") / relative_path

    sys.path.append(os.path.join(code_location))
    sys.path.append(os.path.join(code_location, ".python_packages/lib/site-packages/"))

    os.environ["MINIO_ADDRESS"] = env.MINIO_ADDRESS
    os.environ["MINIO_ACCESS_KEY"] = env.MINIO_ACCESS_KEY
    os.environ["MINIO_SECRET_KEY"] = env.MINIO_SECRET_KEY

    return {"result:" "ok"}


@route("/", method="POST")
def process_request():
    begin = datetime.datetime.now()
    from function import function

    ret = function.handler(request.json)
    end = datetime.datetime.now()

    return {
        "begin": begin.strftime("%s.%f"),
        "end": end.strftime("%s.%f"),
        "request_id": str(uuid.uuid4()),
        "is_cold": False,
        "result": {"output": ret},
    }


run(host="0.0.0.0", port=int(sys.argv[1]), debug=True)
