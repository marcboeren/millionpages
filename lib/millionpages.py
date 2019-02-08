import os
import time
import shutil
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .page import make_page
from .menu import make_menu, Menu
from .error import Error
from .group import Group
from .imageattrs import make_imageattrs


class MillionPages:
    def __init__(
        self, siteconfig, title, sitepath, themepath, templatesfolder, exportpath
    ):
        self.siteconfig = siteconfig
        self.title = title
        self.sitepath = sitepath
        self.themepath = themepath
        self.templatesfolder = templatesfolder
        self.exportpath = exportpath
        self.errors = []
        self.pages = {}  # path as key
        self.menu = {}
        self.menucount = 0
        self.output = {}
        self.jinja = Environment(
            loader=FileSystemLoader(os.path.join(self.themepath)),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.jinja.filters["imageattrs"] = make_imageattrs(self)

    def go(self):
        self.reset_generation()

        self.process_theme_folder()
        self.process_site_folder()

        self.build_menu(self.menu, self.pages.values())

        self.generate_site()

        self.cleanup_generated_site()

        self.print_report()

    def print_report(self):
        print()
        print(f"Pages  : {len(self.pages):4}")
        print(f"Indices: {self.menucount:4}")
        print(f"Output : {len(self.output):4}")
        if self.errors:
            print(f"Errors : {len(self.errors):4}")
            for error in self.errors:
                print(f"       : {error}")
        else:
            print("Success")
        # result = {0: " ", 1: "+", 2: "*"}
        # for output in sorted(self.output):
        #     path = output[len(self.exportpath) :]
        #     print(f"{result[self.output[output]]} {path}")

    def reset_generation(self):
        # shutil.rmtree(self.exportpath, ignore_errors=False)
        os.makedirs(self.exportpath, exist_ok=True)
        self.errors = []
        self.pages = {}
        self.menu = {}
        self.menucount = 0
        self.output = {}
        self.starttime = time.time()

    def cleanup_generated_site(self):
        # walk the upload-folder, compare with self.output
        # if not in self.output, remove
        # also clean up empty folders
        for root, dirs, files in os.walk(self.exportpath, topdown=False):
            for filename in files:
                pathname = os.path.join(root, filename)
                if pathname not in self.output:
                    os.remove(pathname)
            for dirname in dirs:
                pathname = os.path.join(root, dirname)
                try:
                    os.rmdir(pathname)
                except OSError:
                    pass  # not empty, don't remove

    def destination_needs_writing(self, destination, last_modified):
        if not os.path.isfile(destination):
            self.output[destination] = 2
            return True
        destinationtimestamp = os.path.getmtime(destination)
        if destinationtimestamp < last_modified:
            self.output[destination] = 1
            return True
        self.output[destination] = 0
        return False

    def process_theme_folder(self):
        # skip _ files and folders
        # copy rest to export folder
        for root, dirs, files in os.walk(self.themepath):
            path = root[len(self.themepath) :]
            for skipdir in filter(lambda d: d.startswith("_"), dirs):
                dirs.remove(skipdir)
            for skipfile in filter(lambda f: f.startswith("_"), files):
                files.remove(skipfile)
            for f in files:
                exportpath = os.path.join(
                    self.exportpath, path[1:] if path.startswith("/") else path
                )
                source, destination = os.path.join(root, f), os.path.join(exportpath, f)
                sourcetimestamp = os.path.getmtime(source)
                if self.destination_needs_writing(destination, sourcetimestamp):
                    os.makedirs(exportpath, exist_ok=True)
                    shutil.copyfile(source, destination)

    def process_site_folder(self):
        # read pages and start building menu (without grouping)
        # skip _ files and folders
        # copy rest to export folder
        menus = {}
        for root, dirs, files in os.walk(self.sitepath):
            path = root[len(self.sitepath) :]
            for skipdir in list(filter(lambda d: d.startswith("_"), dirs)):
                dirs.remove(skipdir)
            for f in files:
                if f == "__index__.yaml":
                    key = path
                    menu = make_menu(key, os.path.join(root, f))
                    keyparts = key.split("/")
                    keyparts.pop()
                    parentkey = "/".join(keyparts)
                    if parentkey in menus:
                        menus[parentkey].add_item(menu)
                    else:
                        self.menu = menu
                    menus[key] = menu
                elif f == "__index__.md" or f == "__index__.markdown":
                    key = os.path.join(path, f)
                    self.pages[key] = make_page(key, os.path.join(root, f))
            for skipfile in list(filter(lambda f: f.startswith("_"), files)):
                files.remove(skipfile)
            for f in files:
                if f.endswith((".md", ".markdown")):
                    key = os.path.join(path, f)
                    self.pages[key] = make_page(key, os.path.join(root, f))
                else:
                    exportpath = os.path.join(
                        self.exportpath, path[1:] if path.startswith("/") else path
                    )
                    source, destination = (
                        os.path.join(root, f),
                        os.path.join(exportpath, f),
                    )
                    sourcetimestamp = os.path.getmtime(source)
                    if self.destination_needs_writing(destination, sourcetimestamp):
                        os.makedirs(exportpath, exist_ok=True)
                        shutil.copyfile(
                            os.path.join(root, f), os.path.join(exportpath, f)
                        )
        self.menucount = len(menus)
        for page in self.pages.values():
            page.canonical = self.siteconfig["domain"] + page.path

    def build_menu(self, menu, pages):

        if "pages" in menu.config:
            if "filter" in menu.config["pages"]:
                filteredpages = []
                for page in pages:
                    match = True
                    for key, value in menu.config["pages"]["filter"].items():
                        if key not in page.config or page.config[key] != value:
                            match = False
                    if match:
                        filteredpages.append(page)
                pages = filteredpages
            if "order" in menu.config["pages"]:
                order = menu.config["pages"]["order"].split()
                orderby = order.pop(0)
                reverse = "desc" in order
                default = "!!!!!!!!" if reverse else "zzzzzzzz"
                decorated = [
                    (page.config.get(orderby, default) + page.path, page)
                    for page in pages
                ]
                decorated.sort(reverse=reverse)
                pages = [entry[1] for entry in decorated]

        menu.set_pages(pages)

        for item in menu.items:
            self.build_menu(item, pages)

        if "pages" in menu.config:
            if "groups" in menu.config["pages"]:
                for groupconfig in menu.config["pages"]["groups"]:
                    if "by" not in groupconfig:
                        self.errors.append(f"group config misses 'by': {menu.path}")
                        continue
                    group = groupconfig["by"].split()
                    groupby = group.pop(0)
                    group = Group(menu.path, groupby, groupconfig, pages)
                    for groupname, groupedpages in group.groups.items():
                        context = {"group": groupname}
                        config = group.config.copy()
                        for key in config:
                            if isinstance(config[key], str):
                                template = self.jinja.from_string(config[key])
                                try:
                                    config[key] = template.render(**context)
                                except Exception as e:
                                    self.errors.append(
                                        f"group config: {groupname}/{config[key]} - {str(e)}"
                                    )

                        item = Menu(os.path.join(menu.path, groupname), config)
                        item.set_pages(groupedpages)
                        menu.add_item(item)
                        # TODO: nesting

    def print_menu(self, menu, indent):
        print(indent + menu.path + f" ({len(menu.pages)})")
        for item in menu.items:
            self.print_menu(item, indent + "  ")

    def generate_site(self):
        for page in self.pages.values():
            self.write_page(page.path, page)
        self.generate_menu(self.menu)

    def generate_menu(self, menu):
        if menu._is_group:
            for page in menu.pages:
                path = "/".join([menu.path, page.name])
                self.write_page(path, page)
        self.write_index(menu)
        for item in menu.items:
            self.generate_menu(item)

    def write_page(self, path, page):
        print(".", end="", flush=True)
        # print(f"page  | {path:80}")

        exportpath = os.path.join(self.exportpath, path[1:])  # skip leading /
        os.makedirs(exportpath, exist_ok=True)
        filename = "index.html"

        page.url = path
        contentcontext = {
            "config": page.config,
            "menu": self.menu,
            "path": path,
            "site": self.siteconfig,
        }
        template = self.jinja.from_string(page.content)
        try:
            page.content = template.render(**contentcontext)
        except Exception as e:
            raise
            self.errors.append(f"page content: {path} - {str(e)}")

        context = {
            "page": page,
            "menu": self.menu,
            "path": path,
            "site": self.siteconfig,
        }

        destination = os.path.join(exportpath, filename)
        if self.destination_needs_writing(destination, self.starttime):
            with open(os.path.join(exportpath, filename), "w") as htmlfile:
                template = self.jinja.get_template(
                    "/".join((self.templatesfolder, "page.html"))
                )
                try:
                    html = template.render(**context)
                    htmlfile.write(html)
                except Exception as e:
                    raise
                    self.errors.append(f"page : {path} - {str(e)}")

    def write_index(self, menu):
        print("+", end="", flush=True)
        # print(f"index | {menu.path:80} ({len(menu.pages):-2})")

        exportpath = os.path.join(self.exportpath, menu.path[1:])  # skip leading /
        os.makedirs(exportpath, exist_ok=True)
        filename = "index.html"

        for page in menu.pages:
            if menu.path == "/":
                page.url = page.path
            else:
                page.url = "/".join([menu.path, page.name])
            self.write_page(page.url, page)

        context = {
            "index": menu,
            "menu": self.menu,
            "path": menu.path,
            "site": self.siteconfig,
        }

        destination = os.path.join(exportpath, filename)
        if self.destination_needs_writing(destination, self.starttime):
            with open(destination, "w") as htmlfile:
                template = self.jinja.get_template(
                    "/".join((self.templatesfolder, "index.html"))
                )
                try:
                    html = template.render(**context)
                    htmlfile.write(html)
                except Exception as e:
                    self.errors.append(f"index: {menu.path} - {str(e)}")
