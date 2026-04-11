"""Tests for the FSC scouting data client."""

import pandas as pd
import pytest

from frc_data_281.fsc_scouting.client import (
    get_fsc_event_id,
    _normalize_dataframe,
    _parse_html_table,
    TBA_TO_FSC_EVENT,
)


class TestEventMapping:
    def test_known_events_map_correctly(self):
        assert get_fsc_event_id("2026sccmp") == 5
        assert get_fsc_event_id("2026sccha") == 2
        assert get_fsc_event_id("2026schop") == 3
        assert get_fsc_event_id("2026schar") == 4
        assert get_fsc_event_id("2026week0") == 1

    def test_unknown_event_returns_none(self):
        assert get_fsc_event_id("2026unknown") is None
        assert get_fsc_event_id("2025sccmp") is None
        assert get_fsc_event_id("") is None

    def test_all_district_events_have_mapping(self):
        district_events = ['2026sccmp', '2026schop', '2026sccha', '2026schar']
        for event in district_events:
            assert get_fsc_event_id(event) is not None, f"Missing FSC mapping for {event}"


class TestNormalizeDataframe:
    def test_column_name_normalization(self):
        df = pd.DataFrame({"Match Number": [1], "Team Number": [281]})
        result = _normalize_dataframe(df)
        assert "match_number" in result.columns
        assert "team_number" in result.columns

    def test_boolean_conversion(self):
        df = pd.DataFrame({
            "auto_climb_try": ["True", "False", "True"],
            "match_tipped": ["False", "False", "True"],
        })
        result = _normalize_dataframe(df)
        assert result["auto_climb_try"].tolist() == [True, False, True]
        assert result["match_tipped"].tolist() == [False, False, True]

    def test_numeric_conversion(self):
        df = pd.DataFrame({
            "match_number": ["1", "2", "3"],
            "team_number": ["281", "342", "4451"],
            "auto_fuel_score": ["0", "15", "25"],
            "teleop_fuel_score": ["50", "70", "124"],
        })
        result = _normalize_dataframe(df)
        assert result["match_number"].dtype in [int, float, "int64", "float64"]
        assert result["auto_fuel_score"].iloc[1] == 15

    def test_whitespace_stripping(self):
        df = pd.DataFrame({
            "auto_climbed": ["  None  ", " Level1 "],
            "endgame_climb_level": ["None", "  Level1  "],
        })
        result = _normalize_dataframe(df)
        assert result["auto_climbed"].iloc[0] == "None"
        assert result["endgame_climb_level"].iloc[1] == "Level1"

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = _normalize_dataframe(df)
        assert result.empty


class TestParseHtmlTable:
    def test_parses_basic_table(self):
        html = """
        <table>
        <thead><tr><th>Match</th><th>Team</th></tr></thead>
        <tr><td>1</td><td>281</td></tr>
        <tr><td>2</td><td>342</td></tr>
        </table>
        """
        headers, rows = _parse_html_table(html)
        assert headers == ["Match", "Team"]
        assert len(rows) == 2
        assert rows[0] == ["1", "281"]
        assert rows[1] == ["2", "342"]

    def test_handles_no_thead(self):
        html = "<table><tr><td>1</td></tr></table>"
        headers, rows = _parse_html_table(html)
        assert headers == []
        assert rows == []

    def test_handles_empty_table(self):
        html = "<table><thead><tr><th>A</th></tr></thead></table>"
        headers, rows = _parse_html_table(html)
        assert headers == ["A"]
        assert rows == []

    def test_strips_whitespace_from_cells(self):
        html = """
        <table>
        <thead><tr><th>A</th></tr></thead>
        <tr><td>  hello  </td></tr>
        </table>
        """
        headers, rows = _parse_html_table(html)
        assert rows[0] == ["hello"]

    def test_trims_extra_cells_to_header_count(self):
        html = """
        <table>
        <thead><tr><th>A</th><th>B</th></tr></thead>
        <tr><td>1</td><td>2</td><td>extra</td></tr>
        </table>
        """
        headers, rows = _parse_html_table(html)
        assert len(headers) == 2
        assert rows[0] == ["1", "2"]
