import os
import sys
import yaml

from sanic import Sanic
from sanic import response
from urllib.parse import unquote
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from lib.tools import parse
from lib.millionpages import MillionPages

basedir = os.getcwd()
siteconfigpath = os.path.join(basedir, "__site__.yaml")
try:
    siteconfig = parse(siteconfigpath)
except FileNotFoundError:
    print(
        "\nRun mmillionpages from the root-folder containing the `__site__.yaml` file.\n"
    )
    sys.exit(1)
except Exception as e:
    print(f"\nError in `__site__.yaml` file:\n\n{e}")
    sys.exit(1)
title = siteconfig["title"] if "title" in siteconfig else MillionPages
sitepath = os.path.abspath(
    os.path.join(basedir, siteconfig["site"])
    if "site" in siteconfig
    else os.path.join(basedir, "site")
)
themepath = os.path.abspath(
    os.path.join(basedir, siteconfig["theme"])
    if "theme" in siteconfig
    else os.path.join(basedir, "theme")
)
templatesfolder = siteconfig["templates"] if "templates" in siteconfig else "_templates"
exportpath = os.path.abspath(
    os.path.join(basedir, siteconfig["generated-static-site"])
    if "generated-static-site" in siteconfig
    else os.path.join(basedir, "upload-generated-site")
)
# make sure somebody doesn't enter '/' as the generated-static-site folder
# because it gets wiped later...
if not exportpath.startswith(basedir):
    exportpath = os.path.join(basedir, "upload-generated-site")

millionpages = MillionPages(
    siteconfig, title, sitepath, themepath, templatesfolder, exportpath
)


class MillionPagesFileSystemEventHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        print(event.src_path)
        millionpages.go()


event_handler = MillionPagesFileSystemEventHandler()
observer = Observer()
observer.schedule(event_handler, sitepath, recursive=True)
observer.schedule(event_handler, themepath, recursive=True)


app = Sanic()


@app.middleware("request")
async def static(request):
    fullpath = os.path.join(exportpath, unquote(request.path[1:]))
    if os.path.isdir(fullpath):
        fullpath = os.path.join(fullpath, "index.html")
    if os.path.isfile(fullpath):
        return await response.file(fullpath)


if __name__ == "__main__":
    millionpages.go()
    observer.start()
    app.run(host="0.0.0.0", port=10002)
    observer.stop()
    observer.join()
