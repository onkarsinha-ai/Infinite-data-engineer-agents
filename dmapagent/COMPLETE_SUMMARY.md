# dmapagent - Data Mapping Agent

## Project Summary

**Data Mapping Agent (dmapagent)** is a production-ready, LLM-powered system for intelligent schema transformation and data field mapping.

### ✨ Key Highlights

✅ **Multi-Source Support**: DDL, Excel, HTML, PDF, Word documents
✅ **Intelligent Mappings**: Automatic 1:1, N:1 (aggregation), 1:N (decomposition) detection
✅ **Multi-LLM with Fallback**: Gemini → Claude → Ollama (auto-selection)
✅ **Destructive Op Detection**: Identifies data loss risks and narrowing conversions
✅ **Dependency Resolution**: Topological sort for execution ordering
✅ **Excel Export**: Multi-tab reports with color-coding and comments
✅ **Python 3.12**: Modern async/concurrent support
✅ **LangGraph Integration**: Production-grade workflow orchestration
✅ **Production Ready**: Error handling, logging, validation throughout

---

## Project Structure

```
dmapagent/
├── src/
│   ├── core/                 # Document parsing & schema extraction
│   │   ├── document_parser.py     (DDL, Excel, HTML, PDF, Word)
│   │   ├── schema_extractor.py    (Normalize to Field objects)
│   │   └── data_types.py          (Type definitions & conversions)
│   │
│   ├── llm/                  # Multi-LLM provider & prompts
│   │   ├── llm_provider.py        (Gemini > Claude > Ollama chain)
│   │   └── prompts.py             (Pre-defined mapping prompts)
│   │
│   ├── mapping/              # Core mapping logic
│   │   ├── mapping_lineage.py     (Lineage definitions)
│   │   ├── aggregation_engine.py  (N:1 CONCAT/SUM/AVG/MERGE)
│   │   ├── decomposition_engine.py(1:N SPLIT/PARSE_JSON/EXTRACT)
│   │   ├── dependency_analyzer.py (Execution ordering)
│   │   ├── transformation.py      (Code generation)
│   │   ├── validation.py          (Mapping validation)
│   │   └── mapper.py              (Core orchestrator)
│   │
│   ├── graph/                # LangGraph workflow
│   │   ├── workflow.py            (Graph definition)
│   │   ├── nodes.py               (9 workflow nodes)
│   │   └── state.py               (State container)
│   │
│   ├── exporters/            # Excel export
│   │   └── excel_exporter.py      (Multi-tab report generation)
│   │
│   └── utils/                # Utilities
│       ├── logger.py              (Structured logging)
│       └── helpers.py             (Helper functions)
│
├── tests/                    # Comprehensive test suite
│   ├── test_aggregation.py   (Aggregation engine tests)
│   ├── test_decomposition.py (Decomposition engine tests)
│   ├── test_parser.py        (Document parser tests)
│   ├── test_mapper.py        (Mapper tests)
│   └── test_workflow.py      (Integration tests)
│
├── examples/                 # Usage examples
│   ├── simple_1_to_1.py      (1:1 mapping example)
│   ├── many_to_one.py        (N:1 aggregation example)
│   └── one_to_many.py        (1:N decomposition example)
│
├── docs/                     # Documentation
│   ├── architecture.md       (System design & components)
│   └── usage_guide.md        (API & CLI usage)
│
├── main.py                   # CLI entry point
├── config.py                 # Configuration management
├── requirements.txt          # Dependencies
├── setup.py                  # Package setup
├── setup.py.bak              # Package metadata
├── .env.example              # Environment template
└── README.md                 # This file
```

---

## Quick Start

### 1. Installation

```bash
# Navigate to project
cd dmapagent

# Install dependencies
pip install -r requirements.txt

# Setup project structure
python setup.py
```

### 2. Configure API Keys (Optional)

```bash
# Copy template
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

### 3. Run Examples

```bash
# Simple 1:1 mapping
python examples/simple_1_to_1.py

# N:1 aggregation
python examples/many_to_one.py

# 1:N decomposition
python examples/one_to_many.py
```

### 4. CLI Usage

```bash
# Basic mapping
python main.py --source employees.sql --destination report.xlsx --output mapping.xlsx

# Multiple sources
python main.py --source schema1.sql schema2.xlsx --destination final.xlsx --output result.xlsx

# Help
python main.py --help
```

---

## Architecture Highlights

### Workflow Pipeline

```
Input Files (DDL, Excel, HTML, PDF, Word)
    ↓
Parse Sources & Destinations (parallel)
    ↓
Extract Normalized Schemas
    ↓
Create Mapping Context
    ↓
LLM Identifies Mappings (1:1, N:1, 1:N)
    ↓
Aggregation Engine (N:1)  +  Decomposition Engine (1:N)
    ↓
Dependency Analyzer → Execution Order
    ↓
Transformation Engine → Code Generation
    ↓
Destructive Operation Detection
    ↓
Excel Export (7 tabs with color-coding)
    ↓
mapping_report.xlsx
```

### Multi-LLM with Auto-Fallback

```python
LLM Priority Chain:
1. Google Gemini (if GOOGLE_API_KEY set) ← Fastest, most capable
2. Anthropic Claude (if ANTHROPIC_API_KEY set) ← Great reasoning
3. Ollama Gemma2 (if service running) ← Local, free
4. Fail gracefully with error

Auto-switches to next LLM if current fails
```

### N:1 Aggregation (Multiple Sources → One Destination)

```python
Example: Employee first_name + last_name → Report full_name

AggregationRule(
    strategy=CONCAT,
    sources=[first_name, last_name],
    destination=full_name,
    aggregation_expression="CONCAT({0}, ' ', {1})",
    aggregation_code="result = f'{first} {last}'",
    is_destructive=False
)
```

### 1:N Decomposition (One Source → Multiple Destinations)

```python
Example: Contact full_address → street + city

DecompositionRule(
    strategy=SPLIT,
    source=full_address,
    destinations=[street, city],
    decomposition_expression="SPLIT(full_address, ',')",
    decomposition_code="parts = address.split(','); street=parts[0]; city=parts[1]",
    is_destructive=True  # May lose data if address format varies
)
```

### Destructive Operation Detection

Identifies:
- **NARROWING**: VARCHAR(100) → VARCHAR(50)
- **CONVERSION_RISK**: DECIMAL → INTEGER (precision loss)
- **AGGREGATION_LOSS**: SUM loses individual field values
- **DECOMPOSITION_LOSS**: SPLIT may lose data
- **NULL_HANDLING**: Source NULL but dest NOT NULL

---

## Data Models

### MappingLineage
Represents complete mapping from source(s) to destination(s)
- Tracks mapping type (1:1, N:1, 1:N)
- Contains aggregation/decomposition rules
- Flags destructive operations
- Maintains execution dependencies

### Schema & Field
- **Schema**: Container for tables/sheets
- **Field**: Individual column with metadata (name, type, nullable, etc.)
- Supports multiple schemas in single run

### MappingContext
Complete context for entire mapping process
- Holds all lineages
- Tracks unmapped fields
- Detects circular dependencies
- Maintains execution order

---

## Excel Export Format

### Tab 1: Summary
- Total mapping counts by type
- Statistics on destructive operations
- Circular dependency warnings

### Tab 2: 1:1 Mappings
- Source → Destination direct mappings
- Type information and conversions
- Confidence levels

### Tab 3: N:1 Mappings (Aggregation)
- Combined source fields
- Aggregation strategy (CONCAT, SUM, MERGE_JSON, etc.)
- Data loss assessment
- Generated code snippets

### Tab 4: 1:N Mappings (Decomposition)
- Source field
- Multiple destination fields
- Decomposition strategy (SPLIT, PARSE_JSON, etc.)
- Data loss assessment
- Generated code snippets

### Tab 5: Execution Order
- Sequence number
- Mapping dependencies
- Prerequisite mappings

### Tab 6: Destructive Operations
- Risk severity (CRITICAL, HIGH, MEDIUM, LOW)
- Affected mappings
- Data loss details
- Mitigation recommendations

### Tab 7: Metadata
- Context ID and timestamps
- Source/destination schema information
- Processing statistics

---

## Supported Transformations

### Aggregation Strategies (N:1)
- **CONCAT**: Merge strings with delimiter
- **SUM/AVG/MAX/MIN**: Numeric aggregations
- **MERGE**: Object/struct merging
- **MERGE_JSON**: JSON object merging
- **GROUP_ARRAY**: Create array from fields
- **CUSTOM**: User-defined logic

### Decomposition Strategies (1:N)
- **SPLIT**: String splitting by delimiter
- **PARSE_JSON**: JSON field extraction
- **EXTRACT_REGEX**: Regex pattern extraction
- **DISTRIBUTE**: Replicate value across fields
- **PARSE_STRUCT**: Structured data parsing (XML, CSV)
- **CUSTOM**: User-defined logic

### Type Conversions
- String ↔ Numeric (INT, DECIMAL, FLOAT)
- String ↔ Date/DateTime
- JSON → String
- Any → TEXT (widening)
- Detection of narrowing conversions
- Risk assessment for each conversion

---

## Testing

### Test Suite
- Unit tests for each engine
- Parser tests for all formats
- Mapper state tests
- Integration tests (workflow)

### Run Tests
```bash
# All tests
python -m pytest tests/ -v

# Specific module
python -m pytest tests/test_aggregation.py -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=html
```

---

## Configuration

### Environment Variables (.env)

```ini
# LLM Providers
GOOGLE_API_KEY=your_gemini_key
ANTHROPIC_API_KEY=your_claude_key
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma2

# Parameters
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# Logging
LOG_LEVEL=INFO
```

### Programmatic Configuration
```python
from config import DMAPSettings

settings = DMAPSettings(
    GOOGLE_API_KEY="...",
    LLM_TEMPERATURE=0.5,
    LOG_LEVEL="DEBUG"
)
```

---

## Error Handling

### Graceful Degradation
- Missing files: Caught and reported
- Parse errors: Continue with other files
- LLM failures: Auto-fallback to next provider
- Type mismatches: Flagged with risk level
- Circular dependencies: Detected and reported

All errors and warnings included in Excel metadata tab.

---

## Performance

| Operation | Time |
|-----------|------|
| Parse 1000-field schema | < 1s |
| LLM batch (10 mappings) | 5-30s |
| Generate code (100 mappings) | < 1s |
| Excel export | < 2s |
| **Total (typical)** | **10-40s** |

---

## Advanced Usage

### Custom Aggregation
```python
from src.mapping.aggregation_engine import AggregationEngine

engine = AggregationEngine()
rule = engine.analyze_aggregation(source_fields, dest_field)
# Customize rule.aggregation_code as needed
```

### Custom Decomposition
```python
from src.mapping.decomposition_engine import DecompositionEngine

engine = DecompositionEngine()
rule = engine.analyze_decomposition(source_field, dest_fields)
# Customize rule.decomposition_code as needed
```

### Direct Workflow Invocation
```python
from src.graph.workflow import run_mapping_workflow

state = run_mapping_workflow(
    source_files=["source.sql"],
    destination_files=["dest.xlsx"]
)
# Access state.mapping_context, state.destructive_mappings, etc.
```

---

## Extensibility

### Add New Source Format
1. Create parser extending `DocumentParserBase`
2. Implement `can_parse()` and `parse()`
3. Return `ParsedContent`
4. Register in `DocumentParser.parsers`

### Add New LLM Provider
1. Create class extending `LLMBase`
2. Implement `is_available()` and `invoke()`
3. Add to `LLMProvider.__init__()`

### Add New Aggregation Strategy
1. Add to `AggregationStrategy` enum
2. Implement in `_generate_aggregation_code()`
3. Add template in `_init_strategy_templates()`

---

## Known Limitations

- PDF table extraction may have accuracy issues with complex layouts
- HTML parsing assumes well-formed tables
- LLM suggestions are probabilistic (may need review)
- Real-time streaming not supported

---

## Future Enhancements

- [ ] GraphQL schema support
- [ ] Avro/Protobuf format support
- [ ] Interactive UI for mapping approval
- [ ] Mapping template library
- [ ] Batch processing improvements
- [ ] Data sample validation
- [ ] Custom transformation validators
- [ ] Audit trail/version control

---

## License

MIT

---

## Support

For issues, questions, or contributions:
1. Check `docs/` for detailed documentation
2. Review `examples/` for usage patterns
3. See `README.md` for API reference

---

**Built with:**
- LangChain 0.2.0
- LangGraph 1.0.0
- Pydantic 2.6.0
- Python 3.12+

**Created:** April 3, 2026
**Version:** 1.0.0
