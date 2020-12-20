import argparse
from datetime import datetime
import itertools
from pathlib import Path
import random
from typing import List

import numpy as np
import svgwrite
from svgwrite.shapes import Polygon
from svgwrite.extensions import Inkscape

from utils.colors import COLORS

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR.joinpath("output")


def normalize(m, r_min=0.0, r_max=1.0, t_min=0.02, t_max=1.0):
    """Based on https://stats.stackexchange.com/questions/281162/scale-a-number-between-a-range"""

    return (m - r_min) / (r_max - r_min) * (t_max - t_min) + t_min


def get_color_codes(n_colors, colors):
    """Get random set of n_colors"""

    palettes = []

    for _, colors in colors.items():
        if len(colors) >= n_colors:
            palettes.append(colors)

    return random.choices(random.choice(palettes), k=n_colors)


class Grid:
    """A collection of Panels within a Drawing"""

    def __init__(
        self,
        drawing_width,
        drawing_height,
        m_rows=10,
        n_columns=None,
        n_polygons_per_panel=10,
        colors=None,
        panels=None,
        pct_jitter_vertices=0.0,
    ):
        self.drawing_width = drawing_width
        self.drawing_height = drawing_height
        self.m_rows = m_rows
        self.n_columns = n_columns or m_rows
        self.n_polygons_per_panel = n_polygons_per_panel
        self.colors = colors
        self.panel_dims = self.calculate_panel_dims()
        self.panels = panels or self.setup_panels()
        self.pct_jitter_vertices = pct_jitter_vertices

    def __repr__(self):
        return (
            f"{self.__class__.__name__} W: {self.drawing_width}, H: {self.drawing_height}, ROWS: {self.m_rows}"
            f"COLS: {self.n_columns}, COLORS: {self.colors}, JITTER: {self.pct_jitter_vertices}"
        )

    def setup_panels(self):
        """Set up a (x, y) 2-tuple keyed dictionary for panels"""
        return {
            (x, y): None
            for x, y in itertools.product(range(self.m_rows), range(self.n_columns))
        }

    def calculate_panel_dims(self, digits=8):
        """Determine dimensions of each panel. Returns 2-tuple of (width, height)"""

        panel_width = np.round(self.drawing_width / float(self.n_columns), digits)
        panel_height = np.round(self.drawing_height / float(self.m_rows), digits)

        return (panel_width, panel_height)

    def make_panels(self):
        """Make individual panels"""

        # iterate through panel coordinates, making panel for each
        panel_width, panel_height = self.panel_dims
        for i, j in self.panels.keys():

            top_left_point = (panel_width * j, panel_height * i)
            panel = Panel(
                panel_width,
                panel_height,
                insert=top_left_point,
                n_polygons=self.n_polygons_per_panel,
            )

            self.panels[(i, j)] = panel


class Panel:
    """A section of a grid with random number of rectangular-ish polygons."""

    def __init__(
        self,
        width,
        height,
        insert=(0, 0),
        n_polygons: int = 10,
    ):
        self.width = round(width, 4)
        self.height = round(height, 4)
        self.insert = (
            round(insert[0], 4),
            round(insert[1], 4),
        )  # (x, y) top-left insertion point
        self.n_polygons = n_polygons
        self.polygons = []

    def __repr__(self):
        return f"{self.__class__.__name__} W: {self.width}, H: {self.height}, N_polygons: {self.n_polygons}"

    def calculate_polygon_points(
        self,
        width: float,
        height: float,
    ):
        """Based on size of panel and size of polygon, calculate points of polygon relative to panel insert"""
        panel_half_width = round(self.width / 2.0, 4)
        panel_half_height = round(self.height / 2.0, 4)
        polygon_half_width = round(width / 2.0, 4)
        polygon_half_height = round(height / 2.0, 4)

        top_left_x = panel_half_width - polygon_half_width
        top_left_y = panel_half_height - polygon_half_height
        top_right_x = top_left_x + width
        top_right_y = top_left_y
        bottom_right_x = top_right_x
        bottom_right_y = top_left_y + height
        bottom_left_x = top_left_x
        bottom_left_y = bottom_right_y

        return [
            (top_left_x, top_left_y),
            (top_right_x, top_right_y),
            (bottom_right_x, bottom_right_y),
            (bottom_left_x, bottom_left_y),
        ]

    def jitter_polygon_points(
        self,
        points: List,
        width: float,
        height: float,
        pct_jitter_vertices: float,
        rand_range=True,
    ):
        """ "Jitter (x, y) points of polygon by pct_jitter_vertices. If rand_range, jitter by random
        percentage between (-pct_jitter_vertices, pct_jitter_vertices)"""

        def get_jitter_factor(pct_jitter_vertices, rand_range):
            if not rand_range:
                return pct_jitter_vertices

            else:
                MULTIPLIER = 1e6
                low_high = int(pct_jitter_vertices * MULTIPLIER)

                return random.randrange(-low_high, low_high + 1) / MULTIPLIER

        new_points = [
            (
                x
                + (
                    width
                    * get_jitter_factor(pct_jitter_vertices, rand_range=rand_range)
                ),
                y
                + (
                    height
                    * get_jitter_factor(pct_jitter_vertices, rand_range=rand_range)
                ),
            )
            for x, y in points
        ]

        return new_points

    def make_polygon(
        self,
        width: float,
        height: float,
        pct_jitter_vertices: float,
        rand_range=True,
        color=None,
    ):
        """Make an individual polygon with points offset from panel.insert"""

        points = self.calculate_polygon_points(width, height)

        if pct_jitter_vertices:
            points = self.jitter_polygon_points(
                points, width, height, pct_jitter_vertices, rand_range=rand_range
            )

        offset_points = [(x + self.insert[0], y + self.insert[1]) for x, y in points]

        shape = Polygon(
            points=offset_points,
            stroke=color or "black",
            fill_opacity=0.0,
            stroke_width=1,
        )

        return shape

    def make_polygons(self, colors, pct_jitter_vertices):
        """Fill panel with randomly sized self.n_polygons count of rectangle-ish polygons"""

        for i in range(self.n_polygons):

            color = random.choice(colors) if len(colors) > 1 else colors[0]

            rand_size_multipler = normalize(
                m=random.random(), r_min=0.0, r_max=1.0, t_min=0.02, t_max=1.0
            )
            polygon = self.make_polygon(
                width=rand_size_multipler * self.width,
                height=rand_size_multipler * self.height,
                color=color,
                pct_jitter_vertices=pct_jitter_vertices,
            )

            self.polygons.append(polygon)

        return self.polygons


def main_func(
    drawing_width,
    drawing_height,
    m_rows,
    n_columns,
    n_polygons_per_panel,
    output_filebasename,
    colors=None,
    n_colors=None,
    pct_jitter_vertices=0,
    random_seed=None,
    append_datetime=False,
):

    if colors is None and n_colors is not None:
        colors = get_color_codes(n_colors, COLORS)
    elif colors:
        pass
    else:
        colors = ["#000000"]

    out_path_base = (
        f"{output_filebasename}_{len(colors)}_colors_{n_polygons_per_panel}_perpanel"
        f"_jitter_{pct_jitter_vertices}_polygons_{random_seed or 'none'}"
    )
    if append_datetime:
        d = datetime.utcnow()
        out_path_base = out_path_base + "_" + d.strftime("%s%f")
    out_path = out_path_base + ".svg"

    dwg = svgwrite.Drawing(
        OUTPUT_DIR.joinpath(out_path),
        profile="full",
        size=(drawing_width, drawing_height),
    )

    inkscape = Inkscape(dwg)

    inkscape_layers = []
    for c in colors:
        layer = inkscape.layer(label=f"Layer {c}", locked=False)
        inkscape_layers.append(layer)
        dwg.add(layer)

    # set random seeds
    if random_seed is not None:
        random.seed(random_seed)
        np.random.seed(random_seed)

    grid = Grid(
        drawing_width,
        drawing_height,
        m_rows=m_rows,
        n_columns=n_columns,
        n_polygons_per_panel=n_polygons_per_panel,
        colors=colors,
    )

    grid.make_panels()

    # add grid objects to drawing
    for coords, panel in grid.panels.items():
        panel.make_polygons(colors=colors, pct_jitter_vertices=pct_jitter_vertices)
        for polygon in panel.polygons:
            layer_index = 0
            if len(inkscape_layers) > 1:
                layer_index = colors.index(polygon.attribs["stroke"])
            inkscape_layers[layer_index].add(polygon)

    dwg.save()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--width", default=800, help="drawing width in pixels")
    parser.add_argument("--height", default=1000, help="drawing height in pixels")
    parser.add_argument("-m", "--m_rows", default=10, help="count of rows")
    parser.add_argument("-n", "--n_cols", default=8, help="count of columns")
    parser.add_argument("--n_colors", type=int, help="number of colors to use"),
    parser.add_argument(
        "--colors",
        type=str,
        nargs="+",
        default=None,
        help="list of hex colors e.g., #00FF00 #0000FF #FFFF00 #FF0000. Overrides n_colors.",
    )
    parser.add_argument(
        "--n_polygons", default=10, type=int, help="Count of polygons per panel"
    )
    parser.add_argument(
        "-j",
        "--pct_jitter_vertices",
        default=0.0,
        type=float,
        help="max amount of polygon vertices to jitter as percentage of polygon height/width e.g., 0.01",
    )
    parser.add_argument(
        "-r", "--random_seed", default=None, help="Seed for random generators"
    )
    parser.add_argument(
        "-o", "--output_file_basename", default="polygons", help="Output file basename"
    )
    parser.add_argument(
        "--append_datetime",
        action="store_true",
        default=False,
        help="append unix timestamp to filename",
    )

    args = parser.parse_args()

    random_seed = int(args.random_seed) if args.random_seed is not None else None

    main_func(
        drawing_width=args.width,
        drawing_height=args.height,
        m_rows=args.m_rows,
        n_columns=args.n_cols,
        n_polygons_per_panel=args.n_polygons,
        colors=args.colors,
        n_colors=args.n_colors,
        pct_jitter_vertices=args.pct_jitter_vertices,
        random_seed=random_seed,
        output_filebasename=args.output_file_basename,
        append_datetime=args.append_datetime,
    )
