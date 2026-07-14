import json

import pytest

from plotprofile.cli import main

ENERGIES = {"Pathway A": [0.0, -2.0, 10.2, 1.4], "Pathway B": [None, -2.0, 6.2, 4.3]}


@pytest.fixture
def files(tmp_path):
    def write(name, obj):
        path = tmp_path / name
        path.write_text(json.dumps(obj))
        return str(path)

    return write


def test_plots_a_profile(tmp_path, files, capsys):
    out = tmp_path / "p"
    assert main([files("e.json", ENERGIES), "-o", str(out)]) == 0
    assert out.with_suffix(".png").stat().st_size > 0
    assert "wrote" in capsys.readouterr().out


def test_config_carries_the_styling(tmp_path, files):
    # The config keys are the Python API keys.
    config = files("c.json", {"curviness": 0.0, "labels": False, "legend": {"loc": "lower right"}})
    out = tmp_path / "p"
    assert main([files("e.json", ENERGIES), "--config", config, "-o", str(out), "-f", "svg"]) == 0
    assert out.with_suffix(".svg").stat().st_size > 0


def test_annotations_are_drawn(tmp_path, files):
    # --annotations must reach plot(), which is what draws them.
    ann = files("a.json", {"Step 1": [0, 2]})
    out = tmp_path / "p"
    main([files("e.json", ENERGIES), "--annotations", ann, "-o", str(out), "-f", "svg"])
    assert "Step 1" in out.with_suffix(".svg").read_text()


def test_secondary_and_x(tmp_path, files):
    out = tmp_path / "p"
    argv = [
        files("e.json", ENERGIES),
        "--secondary",
        files("s.json", {"C-O": [1.4, 1.6, 2.1, 2.9]}),
        "--x",
        files("x.json", [1.5, 1.8, 2.4, 3.5]),
        "--config",
        files("c.json", {"y2": {"label": "r"}}),
        "-o",
        str(out),
    ]
    assert main(argv) == 0
    assert out.with_suffix(".png").stat().st_size > 0


def test_missing_file_is_a_message_not_a_traceback():
    with pytest.raises(SystemExit, match="input file not found"):
        main(["nope.json"])


def test_bad_json_is_reported(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"a": [0,1')
    with pytest.raises(SystemExit, match="not valid JSON"):
        main([str(bad)])


def test_config_typo_is_rejected(tmp_path, files):
    # An unknown config key must be rejected, not dropped.
    config = files("c.json", {"colour": "viridis"})
    with pytest.raises(SystemExit, match="Unknown style key"):
        main([files("e.json", ENERGIES), "--config", config, "-o", str(tmp_path / "p")])
