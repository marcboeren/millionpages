class Group:
    def __init__(self, path, by, config, pages):

        self.path = path
        self.by = by
        self.config = config
        self.groups = {}
        self.selected_group = None

        group = config["by"].split()
        groupby = group.pop(0)
        reverse = "desc" in group

        groups = {}
        for page in pages:
            if groupby in page.config:
                if isinstance(page.config[groupby], list):
                    for groupvalue in page.config[groupby]:
                        if groupvalue not in groups:
                            groups[groupvalue] = True
                else:
                    if page.config[groupby] not in groups:
                        groups[page.config[groupby]] = True
        groups = sorted(groups.keys(), reverse=reverse)

        # depend on insertion order stability
        if "by-order" in config:
            for group in config["by-order"]:
                if group == "...":
                    for pagegroup in groups:
                        if pagegroup not in config["by-order"]:
                            self.groups[pagegroup] = []
                else:
                    self.groups[group] = []
        else:
            for pagegroup in groups:
                self.groups[pagegroup] = []

        # re-order pages
        if "order" in config:
            order = config["order"].split()
            orderby = order.pop(0)
            reverse = "desc" in order
            default = "!!!!!!!!" if reverse else "zzzzzzzz"
            decorated = [
                (page.config.get(orderby, default) + page.path, page) for page in pages
            ]
            decorated.sort(reverse=reverse)
            pages = [entry[1] for entry in decorated]

        for page in pages:
            if groupby in page.config:
                if isinstance(page.config[groupby], list):
                    for groupvalue in page.config[groupby]:
                        if groupvalue in self.groups:
                            self.groups[groupvalue].append(page)
                else:
                    if page.config[groupby] in self.groups:
                        self.groups[page.config[groupby]].append(page)
