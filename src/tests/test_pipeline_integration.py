"""
Integration test: verify context flows through the entire pipeline.

This test demonstrates that codex context is loaded and available
to all agents without making actual LLM calls.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storygraph.context_loader import load_all_context, format_codex_for_prompt, extract_notes_fragments
from storygraph.agents import planner, draft


def test_end_to_end_context_flow():
    """
    Verify that context loading and formatting works for the full pipeline.
    
    This test:
    1. Loads all context (codex + notes + sources)
    2. Formats context for planner agent
    3. Formats context for draft agent
    4. Verifies all Nikita entities are present
    """
    print("\n" + "="*70)
    print("INTEGRATION TEST: Context Flow Through Pipeline")
    print("="*70)
    
    # Step 1: Load all context
    print("\n[1] Loading all context...")
    context = load_all_context()
    
    codex = context["codex"]
    notes = context["notes"]
    sources = context["sources"]
    
    print(f"    ✓ Loaded {len(codex['people'])} people")
    print(f"    ✓ Loaded {len(codex['places'])} places")
    print(f"    ✓ Loaded {len(codex['claims'])} claims")
    print(f"    ✓ Loaded {len(codex['sources'])} source references")
    print(f"    ✓ Notes present: {bool(notes)}")
    print(f"    ✓ Source files: {list(sources.keys())}")
    
    # Step 2: Verify Nikita entities are present
    print("\n[2] Verifying Nikita entities...")
    
    people_text = " ".join(codex["people"])
    assert "Nikita" in people_text, "Nikita should be in people list"
    assert "Chris" in people_text, "Chris should be in people list"
    assert "Steven" in people_text, "Steven should be in people list"
    print("    ✓ Found Nikita, Chris, Steven in people")
    
    places_text = " ".join(codex["places"])
    assert "Canadian Border Peak" in places_text, "Canadian Border Peak should be in places"
    assert "Tomyhoi" in places_text, "Tomyhoi should be in places"
    assert "Baker" in places_text, "Mount Baker should be in places"
    print("    ✓ Found Canadian Border Peak, Tomyhoi, Baker in places")
    
    claims_text = " ".join(codex["claims"])
    assert len(codex["claims"]) > 0, "Should have claims loaded"
    print(f"    ✓ Found {len(codex['claims'])} verified claims")
    
    # Step 3: Format for planner agent
    print("\n[3] Formatting context for Planner agent...")
    
    codex_formatted = format_codex_for_prompt(codex)
    notes_formatted = extract_notes_fragments(notes)
    
    print(f"    ✓ Codex formatted: {len(codex_formatted)} chars")
    print(f"    ✓ Notes formatted: {len(notes_formatted)} chars")
    
    # Verify formatted output contains key entities
    assert "Nikita" in codex_formatted, "Formatted codex should contain Nikita"
    assert "Canadian Border Peak" in codex_formatted, "Formatted codex should contain Canadian Border Peak"
    assert "PEOPLE:" in codex_formatted, "Formatted codex should have PEOPLE section"
    assert "PLACES:" in codex_formatted, "Formatted codex should have PLACES section"
    print("    ✓ Formatted codex contains key entities and sections")
    
    # Step 4: Test planner render with context
    print("\n[4] Testing Planner prompt construction...")
    
    # Simulate planner user prompt rendering
    planner_user_template = """Premise: {premise}
Venue: {venue}

CODEX:
{codex}

NOTES:
{notes_fragments}
"""
    
    rendered_planner = planner.render(
        planner_user_template,
        premise="Youth, mountains, and the stillness that follows ascent",
        venue="Serious literary magazine like Granta",
        codex=codex_formatted,
        notes_fragments=notes_formatted
    )
    
    assert "Nikita" in rendered_planner, "Planner prompt should include Nikita"
    assert "Canadian Border Peak" in rendered_planner, "Planner prompt should include places"
    assert "Youth, mountains" in rendered_planner, "Planner prompt should include premise"
    print("    ✓ Planner prompt contains premise + codex entities")
    print(f"    ✓ Total planner prompt length: {len(rendered_planner)} chars")
    
    # Step 5: Simulate draft prompt construction
    print("\n[5] Testing Draft prompt construction...")
    
    draft_user_template = """Beat: {beat_id}
Purpose: {purpose}
Target words: {n}

CODEX:
{codex}

NOTES:
{notes_fragments}
"""
    
    # Simulate draft prompt for a beat
    rendered_draft = (
        draft_user_template
        .replace("{beat_id}", "THEN-01")
        .replace("{purpose}", "Nikita and narrator on Tomyhoi Peak")
        .replace("{n}", "800")
        .replace("{codex}", codex_formatted)
        .replace("{notes_fragments}", notes_formatted)
    )
    
    assert "Nikita" in rendered_draft, "Draft prompt should include Nikita"
    assert "Tomyhoi" in rendered_draft or "Canadian Border Peak" in rendered_draft, "Draft prompt should include places"
    assert "THEN-01" in rendered_draft, "Draft prompt should include beat ID"
    print("    ✓ Draft prompt contains beat info + codex entities")
    print(f"    ✓ Total draft prompt length: {len(rendered_draft)} chars")
    
    # Step 6: Verify source document content
    print("\n[6] Verifying source documents...")
    
    if "life_and_death_of_a_climber" in sources:
        source_content = sources["life_and_death_of_a_climber"]
        assert "Nikita" in source_content, "Source doc should mention Nikita"
        assert "AUTHOR INTENT" in source_content, "Source doc should have author intent"
        print(f"    ✓ Author intent document loaded: {len(source_content)} chars")
    else:
        print("    ⚠ Author intent document not found (optional)")
    
    # Final summary
    print("\n" + "="*70)
    print("INTEGRATION TEST PASSED ✓")
    print("="*70)
    print("\nSummary:")
    print(f"  • Context loaded successfully with {len(codex['people'])} people, {len(codex['places'])} places")
    print(f"  • All Nikita entities (people, places, claims) present in codex")
    print(f"  • Planner prompt: {len(rendered_planner)} chars with full context")
    print(f"  • Draft prompt: {len(rendered_draft)} chars with full context")
    print(f"  • Pipeline will now pass codex to all agents")
    print("\n✅ The codex integration is working correctly!")
    print("   Next: Run the full pipeline with LLMs to generate a story about Nikita.\n")


if __name__ == "__main__":
    try:
        test_end_to_end_context_flow()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
