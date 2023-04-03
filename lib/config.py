from configparser import ConfigParser

from .color import Color


population_threshold: int
extinction_dead_zone: int

edge_margin: int
diagram_line_color: Color
diagram_line_thickness: int
node_padding: int
node_min_radius: int
species_margin: int
species_min_width: int
generation_margin: int
generation_min_height: int
generation_lines_enabled: bool
generation_line_color: Color
generation_line_thickness: int

clade_start: int
clade_end: int
clade_split_interval: int

file_type: str


config = ConfigParser()


def update(path):
    config.read(path)

    for _, section in config.items():
        for key in section.keys():
            item_type = __annotations__[key]
            if item_type is int:
                value = section.getint(key)
            elif item_type is float:
                value = section.getfloat(key)
            elif item_type is bool:
                value = section.getboolean(key)
            elif item_type is Color:
                value = Color(section.get(key))
            elif item_type is str:
                value = section.get(key)
            else:
                raise NotImplementedError()

            globals()[key] = value


update("config.ini")
