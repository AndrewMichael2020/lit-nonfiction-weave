# Lit-Nonfiction-Weave

**Computational tools for literary nonfiction craft—exploring systematic approaches to narrative structure, editorial judgment, and collaborative writing with AI systems.**

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Dev Container](https://img.shields.io/badge/dev--container-ready-brightgreen)](https://code.visualstudio.com/docs/remote/containers)

---

## 📖 **Project Intent**

This is an experimental approach to computational literary craft—an attempt to encode some of the structural and stylistic principles that make literary nonfiction work, then see what happens when you apply them systematically through AI agents.

**The Challenge:** Literary nonfiction sits at the intersection of reporting, storytelling, and personal reflection. Getting the balance right—between scene and summary, between showing and telling, between structure and organic flow—is notoriously difficult. Even experienced writers struggle with pacing, fact integration, and maintaining voice consistency across longer pieces.

**The Approach:** Rather than trying to automate creativity, this project focuses on automating editorial judgment. It attempts to formalize some of the implicit knowledge that editors carry: how story beats should progress, what constitutes sufficient concrete detail, how to balance personal narrative with reported material, when claims need factual support.

**The Experiment:** Can we create reproducible workflows that honor literary craft while leveraging AI's capacity for systematic analysis and generation? The pipeline here represents one attempt—using structured templates, quality metrics, and iterative refinement to maintain editorial rigor while exploring new collaborative possibilities between human writers and AI systems.

---

## 🎯 **What This Does**

### **Structural Support**
- **Template-Based Planning:** Applies proven narrative structures (braided narratives, dual timelines, mosaic fragments) to help organize complex material
- **Beat-Level Development:** Breaks stories into purposeful scenes with specific word targets and narrative functions
- **Fact-Source Integration:** Maintains connections between claims and source materials throughout the writing process

### **Editorial Assistance**
- **Voice Consistency:** Tracks stylistic patterns and flags deviations from established tone
- **Concrete Detail Density:** Measures and enforces specificity thresholds that literary editors expect
- **Structural Integrity:** Ensures proper pacing and proportion within established narrative frameworks

### **Collaborative Potential**
This isn't designed to replace human editorial judgment, but to make certain aspects of that judgment more systematic and accessible. The goal is to create tools that writers can use to maintain craft standards while exploring what's possible when computational systems help manage the complexity of longer narrative works.

---

## 🛠 **Technical Architecture**

### **Pipeline Overview**
```mermaid
graph LR
    A[Premise + Venue] --> B[Planner Agent]
    B --> C[Draft Agent]  
    C --> D[Fact Agent]
    D --> E[Revision Agent]
    E --> F[Publication-Ready Story]
    F --> G[Export & Persistence]
    G --> H[Claim Graph with Metrics]
```

### **Core Components**
- **Planner Agent:** Story structure and beat planning using literary templates
- **Draft Agent:** Scene-by-scene content generation with voice consistency
- **Fact Agent:** Structured claim extraction + verification against source documents; promotes fallback keys to maintain schema integrity
- **Revision Agent:** Style refinement and editorial standards enforcement (voice, pacing, specificity)
- **Research Agent:** Source material preprocessing, evidence surfacing, claim grounding seeds
- **Claim Graph:** Aggregated scene‑level claims (substantiated/needs review) with evidence linkage for downstream editorial passes
- **Persistence Layer:** Exports `story_output.json` (structured state with meta) and Markdown with  intended "venue" guidelines labeling 

### **Supported Models**
- **OpenAI:** `openai/gpt-5` (+ experimental reasoning variants `o1`, `o3` via Responses API) — configurable per stage
- **Anthropic:** `anthropic/claude-opus-4-1`, `anthropic/claude-sonnet-4-5-20250929`, `anthropic/claude-haiku-4-5` (date/version pinned for reproducibility)
- **Profile-Driven:** No hard‑coded defaults; all stage models resolved via `config/llm_profiles.yaml` or environment overrides
- **Extensible:** Simple adapter pattern allows adding providers with a small backend wrapper

### **Current Progress Snapshot**
| Area | Status |
|------|--------|
| Centralized LLM configuration | Implemented (`config/llm_profiles.yaml`) |
| Per‑stage model overrides | Implemented (env `LLM_*` vars) |
| JSON output sanitation | Hardened (fence stripping + brace extraction) |
| Fact claim extraction | Stable (~100 claims in sample run) |
| Evidence loading | Basic text source ingestion working |

---

## 🚀 **Exploring the System**

### **GitHub Codespaces (Easiest)**
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/AndrewMichael2020/lit-nonfiction-weave)

The development container includes all dependencies. You'll need API keys for the language models:
```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
python src/run_pipeline.py  # See a complete pipeline run
```

### **Local Setup**
```bash
git clone https://github.com/AndrewMichael2020/lit-nonfiction-weave.git
cd lit-nonfiction-weave
pip install -r requirements.txt
```

### **Interactive Exploration**
The Jupyter notebooks show the pipeline step-by-step:
```bash
make lab  # Opens Jupyter Lab
# Then open notebooks/01_minimal_path.ipynb
```

This lets you see how the agents work individually and experiment with different premises, source materials, and structural approaches.

---

## 📚 **Usage Examples**

### **Basic Story Generation**
```python
from storygraph.router import Pipeline
from storygraph.state import StoryState

# Initialize pipeline
pipe = Pipeline(seed=137)

# Generate story
state = pipe.run_minimal(
    premise="A son drives to a hospital in winter to sign papers he does not want to read",
    venue="The New Yorker"
)

print(f"Generated {state.metrics['word_count_v2']} words")
print(f"Within target range: {state.metrics['within_band']}")
```

### **With Source Material**
```python
# Add research sources
# 1. Drop .txt files into data/sources/
# 2. Run research agent

from storygraph.agents import research
state = research.run(state, sources_dir="data/sources")

# Fact-checking will now verify against these sources
```

### **Custom Configuration**
```python
# Override model selection
state = pipe.run_minimal(
    premise="Your story premise",
    venue="The Atlantic"
)

# Access structured output
outline = state.outline  # Story beats and structure
drafts = state.drafts    # Scene-by-scene content
metrics = state.metrics  # Quality measurements
```

---

## 📊 **Quality Metrics & Standards**

### **Narrative Structure**
- ✅ **Word Band Enforcement:** 3,000-7,500 words total
- ✅ **Beat Targeting:** Individual scenes within ±15% of target length
- ✅ **Template Adherence:** Structured using proven narrative frameworks

### **Editorial Standards**
- ✅ **Grit Metrics:** Obstacle count, choice declaration, cost mention
- ✅ **Specificity:** ≥25% sentences with concrete details
- ✅ **Voice Consistency:** Passive ratio ≤25%, controlled adverb density
- ✅ **Fact Verification:** Claims linked to sources or flagged for review

### **Publication Readiness**
- ✅ **Venue Targeting:** Style adapted for specific publications
- ✅ **Flag System:** Automatic marking of areas needing editorial attention
- ✅ **Revision Tracking:** Version control with change rationale

---

## 🏗 **Project Structure**

```
lit-nonfiction-weave/
├── src/storygraph/           # Core pipeline components
│   ├── agents/              # Individual AI agents
│   ├── llm.py              # Model interface layer  
│   ├── state.py            # Data structures
│   └── router.py           # Pipeline orchestration
├── notebooks/              # Interactive exploration
├── src/prompts/           # Agent instruction templates
├── data/
│   ├── sources/           # Research material (.txt files)
│   └── runs/              # Output snapshots
├── tests/                 # Unit tests
└── .devcontainer/         # Development environment
```

---

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Required API Keys
OPENAI_API_KEY=your-openai-key          # For GPT-5/o1 models
ANTHROPIC_API_KEY=your-anthropic-key    # For Claude models

# Optional Model Overrides
PLANNER_MODEL=openai/gpt-5              # Story planning
DRAFT_MODEL=anthropic/claude-opus-4-1-20250805   # Content generation
FACT_MODEL=openai/gpt-5                 # Fact checking
REVISION_MODEL=anthropic/claude-sonnet-4-5-20250929  # Style refinement
```

### **Pipeline Settings**
- **Seed:** `137` (default, ensures reproducible outputs)
- **Word Targets:** 3,000-7,500 words (configurable)
- **Beat Tolerance:** ±15% of target length per scene
- **Temperature:** 0.2 (balanced creativity/consistency)

---

## 🧪 **Testing & Quality Assurance**

```bash
# Run test suite
make test

# Check individual components
pytest tests/test_validators.py     # Quality metrics
pytest tests/test_agents.py        # Agent functionality
```

### **Continuous Integration**
- Automated testing on push/PR
- Model output validation
- Quality metric enforcement
- Publication standard compliance

---

## 📈 **Potential Applications**

### **For Writers**
- **Structural Scaffolding:** Experiment with narrative frameworks when tackling complex, multi-layered material
- **Editorial Consistency:** Get systematic feedback on voice, pacing, and fact integration
- **Source Management:** Track relationships between claims and research materials as you write
- **Draft Development:** See how different structural approaches might serve the same material

### **For Educators**
- **Craft Instruction:** Demonstrate structural principles through systematic application
- **Workshop Support:** Provide consistent analytical frameworks for discussing student work
- **Genre Exploration:** Help students understand how different templates serve different narrative purposes

### **For Researchers**
- **Computational Literary Analysis:** Explore how editorial principles can be formalized and measured
- **Writing Process Studies:** Examine relationships between structure, revision, and final quality
- **Human-AI Collaboration:** Investigate new models for augmented creative work

---

## 🤝 **Collaboration & Development**

This project works best as a collaborative exploration of computational literary craft. Rather than presenting a finished solution, it's designed to be a platform for experimentation and shared learning about how AI systems can support sophisticated editorial work.

### **Areas of Active Interest**
- **Narrative Templates:** Developing more nuanced structural frameworks beyond the current four
- **Quality Metrics:** Refining measurements that correlate with editorial judgment  
- **Fact Integration:** Better methods for maintaining source relationships throughout revision
- **Voice Analysis:** More sophisticated approaches to consistency and style adaptation
- **Collaborative Workflows:** UI/UX patterns that support human-AI editorial partnerships

### **Contributing Approaches**
- **Template Development:** Contribute new narrative structures with clear beat definitions
- **Metric Refinement:** Propose better measurements for editorial qualities (grit, specificity, voice)
- **Agent Enhancement:** Improve individual pipeline components
- **Case Studies:** Share experiments with different materials and structural approaches
- **Interface Design:** Explore better ways to surface editorial insights to writers

The most valuable contributions tend to come from people with editorial experience who can help bridge computational approaches with real literary craft knowledge.

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙋 **Support & Contact**

- **Issues:** [GitHub Issues](https://github.com/AndrewMichael2020/lit-nonfiction-weave/issues)
- **Discussions:** [GitHub Discussions](https://github.com/AndrewMichael2020/lit-nonfiction-weave/discussions)
- **Documentation:** See `docs/` directory for detailed specifications

---

## 🎖 **Acknowledgments**

Built with:
- [LangGraph](https://github.com/langchain-ai/langgraph) for agent orchestration
- [Pydantic](https://pydantic.dev/) for data validation
- [OpenAI](https://openai.com/) and [Anthropic](https://anthropic.com/) for language models
- [Jupyter](https://jupyter.org/) for interactive development

---

**Interested in exploring computational approaches to literary craft? The [notebooks](notebooks/) show the system in action, and the [Codespaces environment](https://codespaces.new/AndrewMichael2020/lit-nonfiction-weave) makes it easy to experiment with your own material.**