from .tools import parse
from .error import Error


def make_menu(path, pathname):
    try:
        config = parse(pathname)
    except Exception as e:
        return Error(str(e))
    return Menu(path, config)


class Menu:
    def __init__(self, path, config):
        self._parent = None
        self._is_group = "by" in config
        self.path = path
        if not path.startswith("/"):
            self.path = "/" + path
        self.pathlist = self.path.split("/")
        self.pathlist.pop(0)
        self.name = self.pathlist[-1]
        self.config = config
        self.items = []
        self.pages = []

    def _reorder_items(self):
        if "menu-order" in self.config:
            items = {}
            for itemname in self.config["menu-order"]:
                if itemname == "...":
                    for item in self.items:
                        if item.name not in self.config["menu-order"]:
                            items[item.name] = True
                else:
                    items[itemname] = True
            for item in self.items:
                items[item.name] = item
            self.items = [item for item in items.values() if item != True]

    def add_item(self, menuitem):
        menuitem._parent = self
        self.items.append(menuitem)
        self._reorder_items()

    def set_pages(self, pages):
        self.pages = pages
