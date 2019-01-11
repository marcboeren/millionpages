import yaml


def parse(pathname):
    config = {}
    with open(pathname, "r") as yamlfile:
        yamlcontent = yamlfile.read()
        config = yaml.safe_load(yamlcontent)
    return config
