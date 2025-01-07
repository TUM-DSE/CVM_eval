from http_client import https_client

size = 2097152

for i in range(20):
    https_client(size)
