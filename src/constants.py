import os


HTTP_VERSION = "HTTP/1.1"
HTTP_PORT = 80
HTTPS_PORT = 443
SERVER_NAME = "PxNode/1.0"

BUFFERED_CHUNK_SIZE = 4096

MIME_FALLBACK = "application/octet-stream"

DAV_NAME = "PxDAV"
DAV_REALM = "PxLogin"

SRC = os.path.dirname(__file__)
ROOT = os.path.join(SRC, "..")
WEB = os.path.join(ROOT, "web")
FILES = os.path.join(ROOT, "files")
