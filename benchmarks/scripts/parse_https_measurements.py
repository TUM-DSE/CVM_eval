import sys
import numpy as np


def parse(file):
    f = open(file)
    lines = []
    for line in f:
        lines.append(line)
    lines = lines[1:-4]

    request = [0] * (len(lines) // 3)
    response = [0] * (len(lines) // 3)
    for i in range(0, len(lines), 3):
        start = int(lines[i].split(":")[0])
        get_request = int(lines[i + 1].split(":")[0])
        end = int(lines[i + 2].split(":")[0])
        curr_request = get_request - start
        curr_response = end - get_request
        request[i // 3] = curr_request
        response[i // 3] = curr_response
    return np.array(request), np.array(response)


if __name__ == "__main__":
    two_mb = 2 * 1024 * 1024

    # VM Measurements
    size = 64
    while size <= two_mb:
        filename = "VM_https_" + f"{size}.txt"
        req, resp = parse(filename)
        print(f"VM {size} bytes:")
        print(
            f"    Request: avg: {np.mean(req)/1000000} ms, std: {np.std(req)/1000000} ms"
        )
        size = size * 2

    # CVM Measurements
    size = 64
    while size <= two_mb:
        filename = "CVM_https_" + f"{size}.txt"
        req, resp = parse(filename)
        print(f"CVM {size} bytes:")
        print(
            f"    Request: avg: {np.mean(req)/1000000} ms, std: {np.std(req)/1000000} ms"
        )
        size = size * 2
