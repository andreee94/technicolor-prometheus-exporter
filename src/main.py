import os
import time
import logging
from prometheus_client.core import *
from prometheus_client import start_http_server

from exporter.collector import TechnicolorCollector
from gateway import TechnicolorGateway


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    address = os.getenv("ADDRESS", "0.0.0.0")
    port = int(os.environ.get("PORT", "9182"))

    logging.info("Starting exporter at %s:%d", address, port)

    start_http_server(port, addr=address)

    technicolor_ip = os.environ.get("TECHNICOLOR_IP", "192.168.1.1")
    technicolor_port = os.environ.get("TECHNICOLOR_PORT", "80")
    technicolor_username = os.environ.get("TECHNICOLOR_USERNAME", "admin")
    technicolor_password = os.environ.get("TECHNICOLOR_PASSWORD", None)

    if technicolor_password is None:
        raise Exception("TECHNICOLOR_PASSWORD environment variable is not set")

    gateway = TechnicolorGateway(
        technicolor_ip, technicolor_port, technicolor_username, technicolor_password
    )

    REGISTRY.register(TechnicolorCollector(gateway))

    while True:
        time.sleep(5)
