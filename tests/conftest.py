import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

mpl.use("Agg")


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")
