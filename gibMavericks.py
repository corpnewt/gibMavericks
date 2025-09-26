import binascii, hashlib, os, argparse
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

# Filthy python 2 detection
if 2/3==0: input = raw_input

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

    def get_endpoint(self, client_id=None, endpoint="OSInstaller", output_folder=None, resume_incomplete=True):
        if client_id is None:
            print("Generating client ID...")
            client_id = self.get_client_id()
        print("Requesting server ID from http://osrecovery.apple.com...")
        server_id = self.get_server_id()
        print("Building payload for {}...".format(endpoint))
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
            "http://osrecovery.apple.com/InstallationPayload/{}".format(
                endpoint
            ),
            data=data.encode(),
            headers=headers
        )
        assets = []
        try:
            resp = urlopen(req)
            response = resp.read().decode()
            # Check for chunklists first to avoid timing out
            if "\nCU: " in response:
                assets.append((
                    response.split("\nCU: ")[1].split("\n")[0], # chunklist url
                    response.split("\nCT: ")[1].split("\n")[0]  # chunklist token
                ))
            # Get the asset url and token
            assets.append((
                response.split("\nAU: ")[1].split("\n")[0], # asset url
                response.split("\nAT: ")[1].split("\n")[0]  # asset token
            ))
        except Exception as e:
            print(" - Failed: {}".format(e))
            exit(1)
        if not assets:
            print(" - No assets found at endpoint")
            exit(1)
        if output_folder is None:
            # Set it to the Results folder next to this script
            output_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)),"Results")
        if os.path.isfile(output_folder):
            print("{} already exists, and is a file.".format(outupt_folder))
            exit(1)
        elif not os.path.isdir(output_folder):
            print("Creating {} folder...".format(os.path.basename(output_folder)))
            try:
                os.makedirs(output_folder)
            except Exception as e:
                print(" - Failed: {}".format(e))
                exit(1)
        for asset in assets:
            asset_url,asset_token = asset
            asset_name = os.path.basename(asset_url)
            print("Downloading {}...".format(asset_name))
            headers = {
                "Cookie": "AssetToken={}".format(asset_token)
            }
            out_file = os.path.join(output_folder,asset_name)
            try:
                saved_to = self.d.stream_to_file(
                    asset_url,
                    out_file,
                    headers=headers,
                    allow_resume=resume_incomplete
                )
            except Exception as e:
                print(" - Failed: {}".format(e))
            if not saved_to:
                print(" - Failed")
                exit(1)
            print("Saved to: {}".format(saved_to))

    def main(self, endpoints=None, output_folder=None, resume_incomplete=True, no_interaction=False):
        # Walk through the steps to gather info, and document what we're doing
        # along the way
        if endpoints is None:
            endpoints = ("Distribution","RecoveryImage","OSInstaller")
        print("Generating client ID...")
        client_id = self.get_client_id()
        for endpoint in endpoints:
            self.get_endpoint(
                client_id=client_id,
                endpoint=endpoint,
                output_folder=output_folder,
                resume_incomplete=resume_incomplete
            )
        if os.name == "nt" and not no_interaction:
            input("Press [enter] to exit...")

if __name__ == "__main__":
    # Setup the cli args
    parser = argparse.ArgumentParser(prog="gibMavericks", description="gibMavericks - a py script to retrieve Mavericks related files from Apple's servers.")
    parser.add_argument(
        "-r",
        "--re-download",
        help="download all files anew instead of the default behavior of resuming downloaded files.",
        action="store_true"
    )
    parser.add_argument(
        "-e",
        "--endpoints",
        help=(
            "comma delimited list of endpoints to query - options are Distribution, RecoveryImage, and OSInstaller. "
            "e.g. -e RecoveryImage,OSInstaller - defaults to all available."
        )
    )
    parser.add_argument(
        "-o",
        "--output-folder",
        help=(
            "path to the folder you'd like to save the downloaded files in - will be created if it doesn't exist. "
            "Defaults to a Results folder next to this script."
        )
    )
    parser.add_argument(
        "-i",
        "--no-interaction",
        help="exit the script on completion instead of waiting for user input - Windows only.",
        action="store_true"
    )

    args = parser.parse_args()

    endpoint_list = None
    if args.endpoints:
        endpoint_list = []
        valid = ("Distribution","RecoveryImage","OSInstaller")
        for e in args.endpoints.split(","):
            resolved_endpoint = next((x for x in valid if x.lower() == e.lower()),None)
            if not resolved_endpoint:
                print("Invalid endpoint passed.  Can only accept the following values:")
                print(",".join(valid))
                exit(1)
            endpoint_list.append(resolved_endpoint)

    g = gibMavericks()
    g.main(
        endpoints=endpoint_list,
        output_folder=args.output_folder,
        resume_incomplete=not args.re_download,
        no_interaction=args.no_interaction
    )
