import sys


def start():
    f = open(sys.argv[1])
    lines = []
    for line in f:
        lines.append(line)
    total_request = 0
    total_response = 0
    for i in range(0, len(lines), 3):
        start = int(lines[i].split(":")[0])
        get_request = int(lines[i + 1].split(":")[0])
        end = int(lines[i + 2].split(":")[0])
        total_request = total_request + (get_request - start)
        total_response = total_response + (end - get_request)
    print(f"Avg request time: {(total_request/1000)/1000000} ms")
    print(f"Avg response time: {(total_response/1000)/1000000} ms")


if __name__ == "__main__":
    start()
