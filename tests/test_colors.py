
from utils.colors import hexify_colors

def test_mixed_prefix():

    colors = ["#69D2E7", "A7DBD8", "#E0E4CC", "F38630", "#FA6900"]

    expected = ["#69D2E7", "#A7DBD8", "#E0E4CC", "#F38630", "#FA6900"]

    result = hexify_colors(colors)

    assert expected == result
    

