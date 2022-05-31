import binascii
import importlib
import json
import logging
import traceback
from urllib.parse import urlencode
from enum import Enum

from robobrowser import RoboBrowser

from gateway import mysrp as srp
# from gateway.modal_221 import (
#     get_device_modal,
#     get_broadband_modal_old,
#     get_broadband_modal,
#     get_diagnostics_network_modal,
#     get_gateway_info_modal,
# )

_LOGGER = logging.getLogger(__name__)

__version__ = "0.1.1"

# enum for different versions
class TechnicolorVersion(Enum):
    VERSION_221 = 221
    VERSION_234 = 234

modal_module = {
    TechnicolorVersion.VERSION_221: "gateway.modal_221",
    TechnicolorVersion.VERSION_234: "gateway.modal_234",
}

endpoints = {
    TechnicolorVersion.VERSION_221: {
        "device": "device-modal.lp",
        "broadband": "broadband-modal.lp",
        "diagnostics_network": "diagnostics-network-modal.lp",
        "gateway_info": "gateway-modal.lp",
    },
    TechnicolorVersion.VERSION_234: {
        "device": "device-modal.lp",
        "broadband": "broadband-modal.lp",
        "diagnostics_network": "diagnostics-network-modal.lp",
        "gateway_info": "system-info-modal.lp",
    },
}

class TechnicolorGateway(object):
    def __init__(self, host, port, user, password, version=TechnicolorVersion.VERSION_234) -> None:
        self._host = host
        self._port = port
        self._uri = f"http://{host}:{port}"
        self._user = user
        self._password = password
        self._version = version
        self._br = RoboBrowser(history=True, parser="html.parser")
        self._modal = importlib.import_module(modal_module[self._version])
        self._endpoints = endpoints[self._version]

    # def __import_modal__(self):
    #     if self._version == TechnicolorVersion.VERSION_221:
    #         self.modal = importlib.import_module("gateway.modal_221")
    #     elif self._version == TechnicolorVersion.VERSION_234:
    #         self.modal = importlib.import_module("gateway.modal_234")

    def srp6authenticate(self):
        try:
            _LOGGER.info("Authenticating with SRP6 to %s as %s", self._uri, self._user)
            self._br.open(self._uri)
            token = self._br.find(
                lambda tag: tag.has_attr("name") and tag["name"] == "CSRFtoken"
            )["content"]
            _LOGGER.debug("Got CSRF token: %s", token)

            usr = srp.User(
                self._user, self._password, hash_alg=srp.SHA256, ng_type=srp.NG_2048
            )
            uname, A = usr.start_authentication()
            _LOGGER.debug("A value %s", binascii.hexlify(A))

            print("CSRFtoken: ",  token)
            print("I: ", uname)
            print("A: ", binascii.hexlify(A))

            self._br.open(
                f"{self._uri}/authenticate",
                method="post",
                data=urlencode(
                    {"CSRFtoken": token, "I": uname, "A": binascii.hexlify(A)}
                ),
            )
            _LOGGER.debug("br.response %s", self._br.response)
            j = json.decoder.JSONDecoder().decode(self._br.parsed.decode())
            _LOGGER.debug("Challenge received: %s", j)

            M = usr.process_challenge(
                binascii.unhexlify(j["s"]), binascii.unhexlify(j["B"])
            )

            print("s: ", [hex(b) for b in binascii.unhexlify(j["s"])])
            print("B: ", [hex(b) for b in binascii.unhexlify(j["B"])])
            print("M: ", [hex(b) for b in M])

            _LOGGER.debug("M value %s", binascii.hexlify(M))
            self._br.open(
                f"{self._uri}/authenticate",
                method="post",
                data=urlencode({"CSRFtoken": token, "M": binascii.hexlify(M)}),
            )
            _LOGGER.debug("br.response %s", self._br.response)
            j = json.decoder.JSONDecoder().decode(self._br.parsed.decode())
            _LOGGER.debug("Got response %s", j)

            if "error" in j:
                raise Exception("Unable to authenticate (check password?), message:", j)

            usr.verify_session(binascii.unhexlify(j["M"]))
            if not usr.authenticated():
                raise Exception("Unable to authenticate")

            _LOGGER.info("Authentication successful")

            return True

        except Exception as e:
            _LOGGER.error("Authentication failed. Exception: ", e)
            traceback.print_exc()
            raise

    def get_device_modal(self):
        r = self._br.session.get(f"{self._uri}/modals/{self._endpoints['device']}")
        self._br._update_state(r)
        content = r.content.decode()
        return self._modal.get_device_modal(content)

    def get_broadband_modal(self):
        r = self._br.session.get(f"{self._uri}/modals/{self._endpoints['broadband']}")
        self._br._update_state(r)
        content = r.content.decode()
        return self._modal.get_broadband_modal(content)

    def get_broadband_modal_old(self):
        r = self._br.session.get(f"{self._uri}/modals/{self._endpoints['broadband']}")
        self._br._update_state(r)
        content = r.content.decode()
        return self._modal.get_broadband_modal_old(content)

    def get_diagnostics_network_modal(self):
        r = self._br.session.get(f"{self._uri}/modals/{self._endpoints['diagnostics_network']}")
        self._br._update_state(r)
        content = r.content.decode()
        return self._modal.get_diagnostics_network_modal(content)

    def get_gateway_info_modal(self):
        r = self._br.session.get(f"{self._uri}/modals/{self._endpoints['gateway_info']}")
        self._br._update_state(r)
        content = r.content.decode()
        return self._modal.get_gateway_info_modal(content)
