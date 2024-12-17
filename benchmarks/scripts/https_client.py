import http.client
import ssl
import urllib
import json
from ctypes import *

try:
    d = "a" * 4096
    # data = urllib.parse.urlencode(d).encode('utf-8')
    # print(f'Data: {data}')
    foo = {"text": f"{d}"}
    headers = {"Content-Length": "4096"}
    my_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    my_context.load_verify_locations("/root/server.pem")
    my_outb_so = CDLL("/root/libmy_outb.so")
    my_outb_so.my_outb(245)
    connection = http.client.HTTPSConnection("172.45.0.2:4443", context=my_context)
    # connection = http.client.HTTPConnection("172.45.0.2:4443")
    # connection.request("GET", "/")
    connection.request("POST", "/", json.dumps(foo), headers)
    response = connection.getresponse()
    # print("Status: {} and reason: {}".format(response.status, response.reason))

    connection.close()
    my_outb_so.my_outb(246)
except Exception as e:
    print("An exception occured: ", e)
