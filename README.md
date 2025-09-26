# gibMavericks
Python rework of the mavericksforever.com/get.sh script.

***

Original thread found [here](https://forums.macrumors.com/threads/can-we-download-mavericks-directly-from-apples-servers.2444350/).

Original script found [here](https://mavericksforever.com/get.sh).

***

```
usage: gibMavericks [-h] [-r] [-e ENDPOINTS] [-o OUTPUT_FOLDER] [-i]

gibMavericks - a py script to retrieve Mavericks related files from Apple's servers.

options:
  -h, --help            show this help message and exit
  -r, --re-download     download all files anew instead of the default behavior of resuming downloaded files.
  -e, --endpoints ENDPOINTS
                        comma delimited list of endpoints to query - options are Distribution, RecoveryImage, and
                        OSInstaller. e.g. -e RecoveryImage,OSInstaller - defaults to all available.
  -o, --output-folder OUTPUT_FOLDER
                        path to the folder you'd like to save the downloaded files in - will be created if it doesn't
                        exist. Defaults to a Results folder next to this script.
  -i, --no-interaction  exit the script on completion instead of waiting for user input - Windows only.
```
