import random

import numpy as np
import numpy.testing as npt
import pytest

from polygons import Grid, Panel, normalize

SEED = 42
random.seed(SEED)
np.random.seed(SEED)


@pytest.fixture
def panel():
    return Panel(width=10, height=8)


def test_random_seed():
    assert random.randint(0, 100) == 81
    assert np.random.randint(0, 100) == 51


def test_calculate_panel_dims_1():
    """Verfiy that panel dimensions are as expected with provided parameters"""

    grid = Grid(drawing_width=8.0, drawing_height=10.0, m_rows=4, n_columns=10)

    expected = (0.8, 2.5)

    result = grid.calculate_panel_dims()

    assert expected == result


def test_calculate_panel_dims_2():
    """Verfiy that panel dimensions are as expected with provided parameters"""

    grid = Grid(drawing_width=8.3333, drawing_height=10.125, m_rows=4, n_columns=5)

    expected = (
        np.round(grid.drawing_width / grid.n_columns, 6),
        np.round(grid.drawing_height / grid.m_rows, 6),
    )

    result = grid.calculate_panel_dims()

    assert expected == result


def test_setup_panels():
    """Verify np.array is correct length"""

    grid = Grid(drawing_width=10, drawing_height=8, m_rows=10, n_columns=8)

    assert isinstance(grid.panels, dict)
    assert len(grid.panels) == grid.m_rows * grid.n_columns


def test_calculate_polygon_points_1(panel):

    result = panel.calculate_polygon_points(width=4, height=4)

    expected = [(3.0, 3.0), (7.0, 3.0), (7.0, 7.0), (3.0, 7.0)]

    assert result == expected


def test_calculate_polygon_points_1(panel):

    result = panel.calculate_polygon_points(width=4, height=4)

    expected = [(3.0, 2.0), (7.0, 2.0), (7.0, 6.0), (3.0, 6.0)]

    assert result == expected


def test_calculate_polygon_points_2(panel):

    result = panel.calculate_polygon_points(width=2, height=3)

    expected = [(4.0, 2.5), (6.0, 2.5), (6.0, 5.5), (4.0, 5.5)]

    assert result == expected


def test_jitter_polygon_points_1(panel):

    points = [(4.0, 2.5), (6.0, 2.5), (6.0, 5.5), (4.0, 5.5)]

    width = points[1][0] - points[0][0]
    height = points[3][1] - points[0][1]
    assert width == 2.0
    assert height == 3.0

    result = panel.jitter_polygon_points(
        points, width, height, pct_jitter_vertices=0, rand_range=False
    )

    expected = points

    assert result == expected


def test_jitter_polygon_points_2(panel):

    points = [(4.0, 2.5), (6.0, 2.5), (6.0, 5.5), (4.0, 5.5)]

    width = points[1][0] - points[0][0]
    height = points[3][1] - points[0][1]

    pct_jitter_vertices = 0.03

    result = panel.jitter_polygon_points(
        points, width, height, pct_jitter_vertices=pct_jitter_vertices, rand_range=False
    )

    width_jitter = pct_jitter_vertices * width
    height_jitter = pct_jitter_vertices * height

    expected = [(x + width_jitter, y + height_jitter) for x, y in points]

    assert result == expected


def test_normalize_1():
    """Check that a number is normalized as expected"""

    result = normalize(50, r_min=0, r_max=100, t_min=50, t_max=100)

    assert result == 75


def test_normalize_2():
    """Check that a number is normalized as expected"""

    expected = np.array(
        [0.03, 0.127, 0.224, 0.321, 0.418, 0.515, 0.612, 0.709, 0.806, 0.903, 1.0]
    )

    result = []
    for i in range(11):
        result.append(normalize(i / 10.0, r_min=0, r_max=1.0, t_min=0.03, t_max=1.0))

    npt.assert_allclose(np.array(result), expected)
