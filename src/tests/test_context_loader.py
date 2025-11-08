"""
Unit tests for context_loader module.

Tests context loading without making LLM calls.
"""
import pytest
from pathlib import Path
from storygraph.context_loader import (
    load_codex,
    load_notes,
    load_sources,
    load_all_context,
    format_codex_for_prompt,
    extract_notes_fragments,
    _parse_codex_md,
)


class TestCodexParsing:
    """Test parsing of codex markdown files."""
    
    def test_parse_codex_md_people(self):
        """Test parsing people.md returns correct structure."""
        people_path = Path("docs/codex/people.md")
        if not people_path.exists():
            pytest.skip("people.md not found")
        
        items = _parse_codex_md(people_path)
        assert isinstance(items, list)
        if items:
            assert len(items[0]) == 2  # (id, text) tuple
            assert items[0][0].startswith("P")  # People IDs start with P
    
    def test_parse_codex_md_places(self):
        """Test parsing places.md returns correct structure."""
        places_path = Path("docs/codex/places.md")
        if not places_path.exists():
            pytest.skip("places.md not found")
        
        items = _parse_codex_md(places_path)
        assert isinstance(items, list)
        if items:
            assert len(items[0]) == 2
            # Places can have IDs like PL1, C1, etc.
    
    def test_parse_codex_md_claims(self):
        """Test parsing claims.md returns correct structure."""
        claims_path = Path("docs/codex/claims.md")
        if not claims_path.exists():
            pytest.skip("claims.md not found")
        
        items = _parse_codex_md(claims_path)
        assert isinstance(items, list)
        if items:
            assert len(items[0]) == 2
            assert items[0][0].startswith("CL")  # Claims IDs start with CL
    
    def test_parse_codex_md_empty_file(self, tmp_path):
        """Test parsing empty file returns empty list."""
        empty_file = tmp_path / "empty.md"
        empty_file.write_text("", encoding="utf-8")
        
        items = _parse_codex_md(empty_file)
        assert items == []
    
    def test_parse_codex_md_nonexistent_file(self):
        """Test parsing nonexistent file returns empty list."""
        items = _parse_codex_md(Path("nonexistent.md"))
        assert items == []


class TestLoadCodex:
    """Test loading complete codex."""
    
    def test_load_codex_structure(self):
        """Test load_codex returns correct dict structure."""
        codex = load_codex()
        
        assert isinstance(codex, dict)
        assert "people" in codex
        assert "places" in codex
        assert "claims" in codex
        assert "sources" in codex
        
        assert isinstance(codex["people"], list)
        assert isinstance(codex["places"], list)
        assert isinstance(codex["claims"], list)
        assert isinstance(codex["sources"], list)
    
    def test_load_codex_formatted_items(self):
        """Test that codex items are properly formatted."""
        codex = load_codex()
        
        # Check people formatting
        if codex["people"]:
            item = codex["people"][0]
            assert item.startswith("[")
            assert "]" in item
        
        # Check places formatting
        if codex["places"]:
            item = codex["places"][0]
            assert item.startswith("[")
            assert "]" in item


class TestLoadNotes:
    """Test loading notes.md."""
    
    def test_load_notes_returns_string(self):
        """Test load_notes returns string."""
        notes = load_notes()
        assert isinstance(notes, str)
    
    def test_load_notes_content(self):
        """Test load_notes contains expected sections if file exists."""
        notes_path = Path("docs/notes.md")
        if not notes_path.exists():
            pytest.skip("notes.md not found")
        
        notes = load_notes()
        # Should contain at least some markdown headers
        assert len(notes) > 0


class TestLoadSources:
    """Test loading source documents."""
    
    def test_load_sources_structure(self):
        """Test load_sources returns dict."""
        sources = load_sources()
        assert isinstance(sources, dict)
    
    def test_load_sources_content(self):
        """Test source files are loaded with correct keys."""
        sources = load_sources()
        
        # Check if life_and_death_of_a_climber.txt exists
        sources_dir = Path("data/sources")
        if (sources_dir / "life_and_death_of_a_climber.txt").exists():
            assert "life_and_death_of_a_climber" in sources
            assert isinstance(sources["life_and_death_of_a_climber"], str)
            assert len(sources["life_and_death_of_a_climber"]) > 0


class TestLoadAllContext:
    """Test unified context loader."""
    
    def test_load_all_context_structure(self):
        """Test load_all_context returns complete structure."""
        context = load_all_context()
        
        assert isinstance(context, dict)
        assert "codex" in context
        assert "notes" in context
        assert "sources" in context
        
        assert isinstance(context["codex"], dict)
        assert isinstance(context["notes"], str)
        assert isinstance(context["sources"], dict)
    
    def test_load_all_context_codex_complete(self):
        """Test codex in unified context has all categories."""
        context = load_all_context()
        codex = context["codex"]
        
        assert "people" in codex
        assert "places" in codex
        assert "claims" in codex
        assert "sources" in codex


class TestFormatCodexForPrompt:
    """Test prompt formatting helpers."""
    
    def test_format_codex_for_prompt_basic(self):
        """Test basic codex formatting."""
        codex = {
            "people": ["[P1] Test Person"],
            "places": ["[PL1] Test Place"],
            "claims": ["[CL1] Test Claim"],
            "sources": ["[S1] Test Source"],
        }
        
        formatted = format_codex_for_prompt(codex)
        
        assert "PEOPLE:" in formatted
        assert "[P1] Test Person" in formatted
        assert "PLACES:" in formatted
        assert "[PL1] Test Place" in formatted
        assert "VERIFIED CLAIMS:" in formatted
        assert "[CL1] Test Claim" in formatted
        assert "SOURCES:" in formatted
        assert "[S1] Test Source" in formatted
    
    def test_format_codex_for_prompt_empty(self):
        """Test formatting empty codex."""
        codex = {
            "people": [],
            "places": [],
            "claims": [],
            "sources": [],
        }
        
        formatted = format_codex_for_prompt(codex)
        assert formatted == ""
    
    def test_format_codex_for_prompt_max_items(self):
        """Test max_items_per_category limit."""
        codex = {
            "people": [f"[P{i}] Person {i}" for i in range(30)],
            "places": [],
            "claims": [],
            "sources": [],
        }
        
        formatted = format_codex_for_prompt(codex, max_items_per_category=5)
        
        # Should only include first 5 people
        assert "[P0] Person 0" in formatted
        assert "[P4] Person 4" in formatted
        assert "[P5] Person 5" not in formatted


class TestExtractNotesFragments:
    """Test notes fragment extraction."""
    
    def test_extract_notes_fragments_basic(self):
        """Test basic fragment extraction."""
        notes = """
# Working Notes

## Fragments
- "Wind moved like breath"
- "She walked ahead"

## Voice Reminders
- Keep language restrained
- Avoid explaining motives
"""
        
        fragments = extract_notes_fragments(notes)
        
        assert "AUTHOR FRAGMENTS:" in fragments
        assert "Wind moved like breath" in fragments
        assert "VOICE GUIDANCE:" in fragments
        assert "Keep language restrained" in fragments
    
    def test_extract_notes_fragments_empty(self):
        """Test extraction from empty notes."""
        fragments = extract_notes_fragments("")
        assert fragments == ""
    
    def test_extract_notes_fragments_max_chars(self):
        """Test max_chars truncation."""
        notes = "## Fragments\n" + "\n".join([f"- Fragment {i}" * 50 for i in range(100)])
        
        fragments = extract_notes_fragments(notes, max_chars=200)
        
        assert len(fragments) <= 203  # 200 + "..."
        if len(fragments) > 200:
            assert fragments.endswith("...")


class TestContextIntegration:
    """Integration tests for context loading."""
    
    def test_context_has_nikita_entities(self):
        """Test that actual project codex contains expected Nikita entities."""
        context = load_all_context()
        codex = context["codex"]
        
        # Check for expected people
        people_text = " ".join(codex["people"])
        if people_text:
            # Should have some people defined
            assert len(codex["people"]) > 0
        
        # Check for expected places
        places_text = " ".join(codex["places"])
        if places_text:
            # Should have some places defined
            assert len(codex["places"]) > 0
    
    def test_context_loader_idempotent(self):
        """Test that loading context multiple times gives same result."""
        context1 = load_all_context()
        context2 = load_all_context()
        
        assert context1.keys() == context2.keys()
        assert context1["codex"].keys() == context2["codex"].keys()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
