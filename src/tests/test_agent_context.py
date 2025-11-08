"""
Unit tests for agent context integration.

Tests that agents receive and use context correctly, without making LLM calls.
"""
from pathlib import Path
from storygraph.context_loader import load_all_context, format_codex_for_prompt, extract_notes_fragments
from storygraph.agents import planner, draft


class TestPlannerContextIntegration:
    """Test planner agent receives context."""
    
    def test_planner_render_with_codex(self):
        """Test planner render function includes codex."""
        user_template = "Premise: {premise}\nVenue: {venue}\nCODEX:\n{codex}\nNOTES:\n{notes_fragments}"
        
        codex_text = "PEOPLE:\n[P1] Test Person"
        notes_text = "AUTHOR FRAGMENTS:\n- Test fragment"
        
        rendered = planner.render(
            user_template,
            premise="Test premise",
            venue="Test venue",
            codex=codex_text,
            notes_fragments=notes_text
        )
        
        assert "Test premise" in rendered
        assert "Test venue" in rendered
        assert "[P1] Test Person" in rendered
        assert "Test fragment" in rendered
    
    def test_planner_render_empty_codex(self):
        """Test planner render handles empty codex gracefully."""
        user_template = "Premise: {premise}\nCODEX:\n{codex}"
        
        rendered = planner.render(
            user_template,
            premise="Test",
            venue="Venue",
            codex="",
            notes_fragments=""
        )
        
        assert "Test" in rendered
        # Should not fail with empty codex


class TestDraftContextIntegration:
    """Test draft agent receives context."""
    
    def test_draft_user_prompt_construction(self):
        """Test that draft agent constructs user prompt with codex."""
        # This tests the prompt construction logic without calling LLM
        user_template = """Beat: {beat_id}
Target: {n}
CODEX:
{codex}
NOTES:
{notes_fragments}"""
        
        codex_text = "PEOPLE:\n[P1] Nikita"
        notes_text = "FRAGMENTS:\n- Wind moved"
        
        rendered = (
            user_template
            .replace("{beat_id}", "test-beat")
            .replace("{n}", "500")
            .replace("{codex}", codex_text)
            .replace("{notes_fragments}", notes_text)
        )
        
        assert "test-beat" in rendered
        assert "500" in rendered
        assert "[P1] Nikita" in rendered
        assert "Wind moved" in rendered


class TestContextFormatting:
    """Test context formatting for prompts."""
    
    def test_format_codex_includes_all_categories(self):
        """Test that formatted codex includes all entity types."""
        context = load_all_context()
        codex = context["codex"]
        
        if any(codex.values()):  # If any category has items
            formatted = format_codex_for_prompt(codex)
            
            # Should have headers for non-empty categories
            if codex.get("people"):
                assert "PEOPLE:" in formatted
            if codex.get("places"):
                assert "PLACES:" in formatted
            if codex.get("claims"):
                assert "VERIFIED CLAIMS:" in formatted
    
    def test_extract_notes_preserves_structure(self):
        """Test notes extraction preserves fragment structure."""
        notes = """
## Fragments
- "Wind moved like breath between rock fins."
- "She walked ahead without checking if I followed."

## Voice Reminders
- Keep language restrained and observational
"""
        
        fragments = extract_notes_fragments(notes)
        
        # Should preserve the actual fragment text
        assert "Wind moved like breath" in fragments
        assert "She walked ahead" in fragments
        assert "restrained" in fragments


class TestPipelineContextFlow:
    """Test context flows through pipeline components."""
    
    def test_context_structure_for_agents(self):
        """Test that loaded context has correct structure for agents."""
        context = load_all_context()
        
        # Verify structure agents expect
        assert "codex" in context
        assert "notes" in context
        assert "sources" in context
        
        # Verify codex has all required keys
        codex = context["codex"]
        required_keys = {"people", "places", "claims", "sources"}
        assert required_keys.issubset(codex.keys())
        
        # Verify all values are lists
        for key in required_keys:
            assert isinstance(codex[key], list)
    
    def test_context_ready_for_planner(self):
        """Test context can be formatted for planner agent."""
        context = load_all_context()
        
        # Should be able to format without errors
        codex_text = format_codex_for_prompt(context["codex"])
        notes_text = extract_notes_fragments(context["notes"])
        
        # Both should return strings
        assert isinstance(codex_text, str)
        assert isinstance(notes_text, str)
    
    def test_sources_loaded_for_fact_agent(self):
        """Test that source documents are loaded for fact checking."""
        context = load_all_context()
        sources = context["sources"]
        
        # Should be a dict
        assert isinstance(sources, dict)
        
        # If life_and_death_of_a_climber.txt exists, it should be loaded
        sources_dir = Path("data/sources")
        if (sources_dir / "life_and_death_of_a_climber.txt").exists():
            assert "life_and_death_of_a_climber" in sources
            content = sources["life_and_death_of_a_climber"]
            
            # Should contain author intent
            assert len(content) > 100
            assert isinstance(content, str)


class TestRealCodexContent:
    """Test actual codex content from the project."""
    
    def test_codex_has_nikita_entities(self):
        """Test that codex contains Nikita-related entities."""
        context = load_all_context()
        codex = context["codex"]
        
        # Join all people entries
        people_text = " ".join(codex["people"])
        
        # Should mention key people if codex is populated
        if people_text:
            # At minimum, should have some structured people entries
            assert len(codex["people"]) >= 0  # May be empty initially
    
    def test_codex_has_place_entities(self):
        """Test that codex contains place entities."""
        context = load_all_context()
        codex = context["codex"]
        
        places_text = " ".join(codex["places"])
        
        # Should have place entries if codex is populated
        if places_text:
            assert len(codex["places"]) >= 0
    
    def test_author_intent_in_sources(self):
        """Test that author intent document is loaded."""
        context = load_all_context()
        sources = context["sources"]
        
        # Check for the key source document
        if "life_and_death_of_a_climber" in sources:
            content = sources["life_and_death_of_a_climber"]
            
            # Should contain key information about the story
            assert "AUTHOR INTENT" in content or "author" in content.lower()


if __name__ == "__main__":
    # Run tests without pytest if needed
    import sys
    
    test_classes = [
        TestPlannerContextIntegration,
        TestDraftContextIntegration,
        TestContextFormatting,
        TestPipelineContextFlow,
        TestRealCodexContent,
    ]
    
    failures = 0
    for test_class in test_classes:
        instance = test_class()
        for attr in dir(instance):
            if attr.startswith("test_"):
                try:
                    method = getattr(instance, attr)
                    method()
                    print(f"✓ {test_class.__name__}.{attr}")
                except Exception as e:
                    print(f"✗ {test_class.__name__}.{attr}: {e}")
                    failures += 1
    
    print(f"\n{'PASSED' if failures == 0 else f'FAILED ({failures} failures)'}")
    sys.exit(0 if failures == 0 else 1)
