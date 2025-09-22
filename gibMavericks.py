import binascii, hashlib, os
from Scripts import downloader

try:
    from secrets import randbits
    basestring = str
    from urllib.request import urlopen, Request
except ImportError:
    from random import SystemRandom
    _sysrand = SystemRandom()
    randbits = _sysrand.getrandbits
    import urllib2
    from urllib2 import urlopen, Request

BOARD_SERIAL_NUMBER="C0243070168G3M91F"
BOARD_ID="Mac-3CBD00234E554E41"
ROM="003EE1E6AC14"

class gibMavericks:

    def __init__(self):
        self.d = downloader.Downloader()

    def get_client_id(self):
        # Return 8-bytes of random hex data
        return hex(randbits(8*8))[2:].upper().rstrip("L").rjust(16,"0")

    def get_server_id(self):
        # Get the server ID from Apple by reading the cookie data set
        try:
            response = self.d.open_url("http://osrecovery.apple.com/")
            return response.headers["Set-Cookie"].split("session=")[1].split(";")[0]
        except Exception as e:
            print(" - Failed: {}".format(e))
            exit(1)

    def main(self):
        # Walk through the steps to gather info, and document what we're doing
        # along the way
        print("Generating client ID...")
        client_id = self.get_client_id()
        print("Getting server ID from http://osrecovery.apple.com...")
        server_id = self.get_server_id()
        print("Building payload...")
        # We need to build binary representations of a handful of hex values
        payload  = binascii.unhexlify(client_id)
        payload += binascii.unhexlify(server_id.split("~")[1])
        payload += binascii.unhexlify(ROM)
        # Get the sha256 hash of the board serial + board id
        hash_target = (BOARD_SERIAL_NUMBER+BOARD_ID).encode()
        hashersha256 = hashlib.sha256()
        hashersha256.update(hash_target)
        payload += binascii.unhexlify(hashersha256.hexdigest())
        # Append 0xCC * 10
        payload += binascii.unhexlify("CC"*10)
        # Get the digest of the resulting information
        hasherkey = hashlib.sha256()
        hasherkey.update(payload)
        key = hasherkey.hexdigest().upper()
        # Retrieve the installation payload which contains the asset token needed
        headers = {
            "Content-Type": "text/plain",
            "Cookie": "session={}".format(server_id)
        }
        data = "cid={}\nsn={}\nbid={}\nk={}".format(
            client_id,
            BOARD_SERIAL_NUMBER,
            BOARD_ID,
            key
        )
        req = Request(
            "http://osrecovery.apple.com/InstallationPayload/OSInstaller",
            data=data.encode(),
            headers=headers
        )
        print("Sending request...")
        try:
            resp = urlopen(req)
            response = resp.read().decode()
            # Get the asset url and token
            asset_url = response.split("\nAU: ")[1].split("\n")[0]
            asset_token = response.split("\nAT: ")[1].split("\n")[0]
        except Exception as e:
            print(" - Failed: {}".format(e))
            exit(1)
        # Ensure we actually got the Mavericks download URL
        if asset_url != "http://oscdn.apple.com/content/downloads/33/62/031-10295/gho4r94w66f5v4ujm0sz7k1m0hua68i6oo/OSInstaller/InstallESD.dmg":
            print(" - Invalid response!")
            exit(1)
        print("Downloading InstallESD.dmg...")
        headers = {
            "Cookie": "AssetToken={}".format(asset_token)
        }
        out_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),"InstallESD.dmg")
        try:
            saved_to = self.d.stream_to_file(
                asset_url,
                out_file,
                headers=headers,
                allow_resume=True
            )
        except Exception as e:
            print(" - Failed: {}".format(e))
        if not saved_to:
            print(" - Failed")
            exit(1)
        print("Saved to: {}".format(saved_to))

if __name__ == "__main__":
    g = gibMavericks()
    g.main()
