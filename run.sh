#!/bin/bash

# Script to generate SSL keys and start the application

declare no_cert=false
declare -a files=("cert.pem" "key.pem")

for file in "${files[@]}"; do
    if [ ! -e "$file" ]; then
        declare no_cert=true
        break
    fi
done

if [ "$no_cert" = true ]; then
    echo "No SSL certificate found. Generating one..."
    yes "" | openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes
    echo ""
fi

python3.12 src/main.py