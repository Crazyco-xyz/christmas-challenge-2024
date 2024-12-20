#!/bin/bash

declare no_cert=false
declare -a files=("cert.pem" "key.pem")

# Check if the SSL certificates exist
for file in "${files[@]}"; do
    if [ ! -e "$file" ]; then
        declare no_cert=true
        break
    fi
done

# Generate SSL certificates if they don't exist
if [ "$no_cert" = true ]; then
    echo "No SSL certificate found. Generating one..."
    yes "" | openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes
    echo ""
    echo "Finished generating certificates"
fi

python3.12 src/main.py || python3 src/main.py
