## Setup

Spawn 2 VMs that have connectivity between them (can ping each other)
On the server side, generate a certificate with

```
openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes --addext 'subjectAltName=IP:172.45.0.2'
```

Also give the generated file to the client


