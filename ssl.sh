#!/bin/bash

# Script to generate the private key and
# certificate used for the TLS part of HTTPS

openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes