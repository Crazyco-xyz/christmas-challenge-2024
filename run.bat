@echo off

set no_cert=false

rem Check if the SSL certificates exist
for %%f in (cert.pem key.pem) do (
    if not exist "%%f" (
        set no_cert=true
        goto :break
    )
)
:break

rem Generate SSL certificates if they don't exist
if %no_cert%==true (
    echo No SSL certificate found. Generating...
    yes "" | openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes
    echo.
    echo Finished generating certificates
)

python src\main.py
