import os.path
import yaml
import markdown
from .error import Error


def parse(pathname):
    pageconfig = {}
    pagehtml = ""
    with open(pathname, "r") as mdfile:
        mdcontent = mdfile.read()

        if mdcontent.startswith("---\n"):
            parts = mdcontent.split("---\n")
            parts.pop(0)
            if len(parts) > 1:
                configpart = parts.pop(0).strip()
                if configpart:
                    pageconfig = yaml.safe_load(configpart)
            mdpart = "---\n".join(parts).strip()
        else:
            mdpart = mdcontent

        if mdpart:
            pagehtml = markdown.markdown(mdpart)

    return pageconfig, pagehtml


def make_page(key, pathname):
    try:
        config, content = parse(pathname)
    except Exception as e:
        return Error(str(e))
    filename = os.path.basename(key)
    path = os.path.dirname(key)
    if not filename.startswith("__index__."):
        path = os.path.join(path, os.path.splitext(filename)[0])
    return Page(path, config, content)


class Page:
    def __init__(self, path, config, content):
        self.path = path
        if not path.startswith("/"):
            self.path = "/" + path
        pathlist = self.path.split("/")
        self.name = pathlist.pop()
        self.config = config
        self.content = content
