import os


HTTP_VERSION = "HTTP/1.1"
HTTP_PORT = 80
HTTPS_PORT = 443

SRC = os.path.dirname(__file__)
ROOT = os.path.join(SRC, "..")
WEB = os.path.join(ROOT, "web")
FILES = os.path.join(ROOT, "files")
