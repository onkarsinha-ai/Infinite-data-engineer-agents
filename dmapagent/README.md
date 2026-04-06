"""README for Data Mapping Agent (dmapagent)."""

# Data Mapping Agent (dmapagent)

A sophisticated LLM-powered agent for schema transformation and intelligent data field mapping. Maps fields from multiple source formats (DDL, Excel, HTML, PDF, Word) to Excel destinations with automatic detection of 1:1, N:1, and 1:N mappings.

## Features

### 🎯 Mapping Types
- **1:1 Mappings**: Direct source-to-destination field mapping
- **N:1 Mappings (Aggregation)**: Multiple source fields merged into single destination
- **1:N Mappings (Decomposition)**: Single source field split into multiple destinations

### 📄 Source Format Support
- SQL DDL statements (.sql, .ddl)
- Excel workbooks (.xlsx, .xls)
- HTML tables (.html, .htm)
- PDF documents (.pdf)
- Word documents (.docx, .doc)

### 🤖 Multi-LLM Support with Fallback
1. **Google Gemini** (if GOOGLE_API_KEY available)
2. **Anthropic Claude** (if ANTHROPIC_API_KEY available)
3. **Ollama Gemma2** (if local service running)

Auto-fallback chain ensures operations continue if primary LLM unavailable.

### 🔍 Intelligent Detection
- **Aggregation Strategies**: CONCAT, SUM, AVG, MAX, MIN, MERGE_JSON, etc.
- **Decomposition Strategies**: SPLIT, PARSE_JSON, EXTRACT_REGEX, DISTRIBUTE, etc.
- **Type Conversion**: Automatic detection and risk assessment
- **Destructive Operations**: Identifies data loss risks (narrowing, conversion loss, NULL handling)

### 📊 Comprehensive Excel Export
- Summary tab with mapping statistics
- Separate tabs for 1:1, N:1, and 1:N mappings
- Execution order with dependency tracking
- Destructive operations assessment
- Color-coded risk indicators (red=critical, yellow=warning)
- Metadata and lineage tracking

## Installation

```bash
# Clone or download the project
cd dmapagent

# Install dependencies
pip install -r requirements.txt

# Create .env file with API keys (optional)
echo "GOOGLE_API_KEY=your_key_here" > .env
echo "ANTHROPIC_API_KEY=your_key_here" >> .env
```

## Quick Start

### CLI Usage

```bash
# Basic usage
python main.py --source employees.sql --destination report_template.xlsx --output mapping.xlsx

# Multiple sources
python main.py \
  --source employee.sql department.sql \
  --destination sales_report.xlsx billing.xlsx \
  --output mapping_report.xlsx

# From various formats
python main.py \
  --source schema.sql data_mapping.xlsx employee_list.pdf \
  --destination report.xlsx \
  --output complete_mapping.xlsx
```

### Python API

```python
from src.graph.workflow import run_mapping_workflow
from src.exporters.excel_exporter import ExcelExporter

# Run mapping workflow
state = run_mapping_workflow(
    source_files=["source.sql"],
    destination_files=["template.xlsx"]
)

# Export results
exporter = ExcelExporter("mapping_report.xlsx")
exporter.export(state.mapping_context)
```

## Project Structure

```
dmapagent/
├── src/
│   ├── core/                 # Document parsing & schema extraction
│   │   ├── document_parser.py
│   │   ├── schema_extractor.py
│   │   └── data_types.py
│   ├── llm/                  # Multi-LLM provider & prompts
│   │   ├── llm_provider.py
│   │   └── prompts.py
│   ├── mapping/              # Core mapping logic
│   │   ├── mapping_lineage.py      # Lineage definitions
│   │   ├── aggregation_engine.py   # N:1 handling
│   │   ├── decomposition_engine.py # 1:N handling
│   │   ├── dependency_analyzer.py  # Execution ordering
│   │   ├── transformation.py       # Code generation
│   │   ├── validation.py
│   │   └── mapper.py
│   ├── graph/                # LangGraph workflow
│   │   ├── workflow.py
│   │   ├── nodes.py
│   │   └── state.py
│   ├── exporters/            # Excel export
│   │   └── excel_exporter.py
│   └── utils/                # Utilities
│       ├── logger.py
│       └── helpers.py
├── tests/                    # Unit tests
├── examples/                 # Usage examples
├── docs/                     # Documentation
├── main.py                   # CLI entry point
├── config.py                 # Configuration
├── requirements.txt
└── README.md
```

## Configuration

Create `.env` file in project root:

```ini
# LLM API Keys
GOOGLE_API_KEY=your_gemini_key
ANTHROPIC_API_KEY=your_claude_key

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma2

# LLM Parameters
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# Logging
LOG_LEVEL=INFO
```

## Core Concepts

### MappingLineage
Represents a complete mapping from source(s) to destination(s):
- **source_fields**: List of source Field objects
- **destination_field(s)**: Destination Field object(s)
- **aggregation_rule**: For N:1 mappings
- **decomposition_rule**: For 1:N mappings
- **is_destructive**: Flag for data-loss operations
- **depends_on**: List of other mapping IDs

### AggregationRule (N:1)
```python
AggregationRule(
    strategy=AggregationStrategy.CONCAT,
    source_fields=[Field1, Field2],
    destination_field=Field3,
    aggregation_expression="CONCAT({0}, ' ', {1})",
    aggregation_code="result = ', '.join([field1, field2])"
)
```

### DecompositionRule (1:N)
```python
DecompositionRule(
    strategy=DecompositionStrategy.SPLIT,
    source_field=FullName,
    destination_fields=[FirstName, LastName],
    decomposition_expression="SPLIT(FullName, ' ')",
    decomposition_code="parts = full_name.split(); first = parts[0]; last = parts[1]"
)
```

### Destructive Operations
Detected categories:
- **NARROWING**: Reducing field size (VARCHAR(100) → VARCHAR(50))
- **CONVERSION_RISK**: Unsafe type conversion
- **AGGREGATION_LOSS**: Information loss in aggregation
- **DECOMPOSITION_LOSS**: Incomplete decomposition
- **NULL_HANDLING**: NULL behavior changes

## Examples

### Example 1: Simple 1:1 Mapping

```
Source: employees.sql
  - employee_id (INTEGER)
  - first_name (VARCHAR)
  - last_name (VARCHAR)

Destination: report.xlsx
  - EmployeeID
  - FirstName
  - LastName

Result: 3 direct 1:1 mappings (HIGH confidence)
```

### Example 2: Aggregation (N:1)

```
Sources: 
  - employee.first_name
  - employee.last_name

Destination:
  - report.full_name

Mapping: Aggregation via CONCAT
  - Rule: CONCAT(first_name, ' ', last_name) → full_name
  - Destructive: No
  - Risk: LOW
```

### Example 3: Decomposition (1:N)

```
Source:
  - product_details (VARCHAR containing "Color:Red;Size:Large;Weight:5kg")

Destinations:
  - product_color
  - product_size
  - product_weight

Mapping: Decomposition via SPLIT
  - Strategy: PARSE_STRUCT (key-value pairs)
  - Destructive: Yes (may lose unexpected fields)
  - Risk: MEDIUM
```

## Error Handling

The agent gracefully handles:
- Missing files
- Unparseable documents
- LLM provider failures (auto-fallback)
- Type incompatibilities
- Circular dependencies

All errors and warnings are logged and included in Excel output.

## Testing

```bash
# Run tests
python -m pytest tests/

# Run with verbose output
python -m pytest tests/ -v

# Test specific module
python -m pytest tests/test_aggregation_engine.py -v
```

## Performance

- Parses large schemas (1000+ fields) in seconds
- LLM inference takes 5-30s per mapping batch (depends on provider)
- Excel export completes instantly
- Memory efficient (suitable for large mappings)

## Limitations

- PDF table extraction may have accuracy issues with complex layouts
- HTML parsing assumes well-formed tables
- LLM suggestions are probabilistic (may require review)
- Real-time streaming not supported

## Future Enhancements

- [ ] GraphQL schema support
- [ ] Avro/Protobuf format support
- [ ] Interactive UI for mapping approval
- [ ] Mapping template library
- [ ] Batch processing of multiple transformations
- [ ] Data sample validation
- [ ] Custom transformation validators
- [ ] Audit trail and version control

## License

MIT

## Support

For issues and questions, check the `docs/` folder for detailed documentation and examples.

---

**Built with LangChain, LangGraph, and multi-LLM support**
