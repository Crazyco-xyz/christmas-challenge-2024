@echo off

rem Script to generate SSL keys and start the application

set no_cert=false

for %%f in (cert.pem key.pem) do (
    if not exist "%%f" (
        set no_cert=true
        goto :break
    )
)
:break

if %no_cert%==true (
    echo No SSL certificate found. Generating...
    yes "" | openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes
    echo.
    echo Finished generating certificates
)

python src\main.py
