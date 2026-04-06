# Architecture Documentation

## System Overview

The Data Mapping Agent (dmapagent) is a LLM-powered system for intelligent schema transformation. It uses LangGraph to orchestrate a multi-stage mapping workflow.

## High-Level Architecture

```
Input (Multiple Formats)
    ↓
[Document Parser] → Normalized Schemas
    ↓
[Schema Extractor] → Field-level Metadata
    ↓
[LLM-based Mapper] → Mapping Lineages
    ├── 1:1 Mappings (Identity)
    ├── N:1 Mappings (Aggregation)
    └── 1:N Mappings (Decomposition)
    ↓
[Engines]
├── Aggregation Engine → Merge Logic
├── Decomposition Engine → Split Logic
├── Dependency Analyzer → Execution Order
└── Transformation Engine → Code Generation
    ↓
[Validators] → Destructive Op Detection
    ↓
[Excel Exporter] → Multi-tab Report
    ↓
Output (mapping_report.xlsx)
```

## Core Components

### 1. Document Parser Layer (src/core/)

**DocumentParser** - Router that delegates to specific parsers:
- DDLParser: SQL CREATE TABLE statements
- ExcelParser: XLSX/XLS workbooks
- HTMLParser: HTML table extraction
- WordParser: DOCX documents
- PDFParser: PDF table extraction

**Output**: ParsedContent with normalized table/column definitions

### 2. Schema Extraction (src/core/schema_extractor.py)

**SchemaExtractor**:
- Parses document content into Schema objects
- Creates Field objects with type information
- Normalizes names and types
- Supports multiple schemas in single run

**Data Structures**:
- `Schema`: Container for tables
- `Field`: Represents a column with metadata
- `TypeInfo`: Type definition with precision/scale

### 3. Multi-LLM Provider (src/llm/)

**LLMProvider** with fallback chain:
1. Google Gemini (if GOOGLE_API_KEY set)
2. Anthropic Claude (if ANTHROPIC_API_KEY set)
3. Ollama Gemma2 (if service running at localhost:11434)

**MappingPrompts**: Pre-defined prompts for LLM tasks:
- identify_one_to_one_mappings
- identify_aggregation_mappings
- identify_decomposition_mappings
- suggest_type_conversion
- detect_destructive_operations
- generate_aggregation_code
- generate_decomposition_code

### 4. Mapping Core (src/mapping/)

#### 4.1 Mapping Lineage
Represents a complete mapping path:
```
MappingLineage
├── mapping_type: MappingType (1:1, N:1, 1:N, N:N)
├── source_fields: List[Field]
├── destination_field(s): Field(s)
├── aggregation_rule: AggregationRule (N:1 only)
├── decomposition_rule: DecompositionRule (1:N only)
├── transformation_pipeline: List[FieldMapping]
├── is_destructive: bool
├── destruction_type: str
└── depends_on: List[mapping_ids]
```

#### 4.2 Aggregation Engine
Handles N:1 mappings (multiple sources → single destination):
- Strategies: CONCAT, SUM, AVG, MAX, MIN, MERGE_JSON, etc.
- Generates Python aggregation code
- Detects data loss in merging operations
- Validates aggregation rules

#### 4.3 Decomposition Engine
Handles 1:N mappings (single source → multiple destinations):
- Strategies: SPLIT, PARSE_JSON, EXTRACT_REGEX, DISTRIBUTE, PARSE_STRUCT
- Generates Python decomposition code
- Detects incomplete decomposition losses
- Validates decomposition rules

#### 4.4 Dependency Analyzer
Analyzes and resolves mapping dependencies:
- Builds dependency graph
- Detects circular dependencies
- Resolves execution order (topological sort)
- Identifies mapping prerequisites

#### 4.5 Transformation Engine
Generates transformation code:
- Type conversion logic (STRING→INT, DATE→VARCHAR, etc.)
- Creates transformation pipelines
- Produces executable Python code for each mapping

### 5. LangGraph Workflow (src/graph/)

**WorkflowState**: Complete state container for entire mapping process

**Workflow Nodes** (execution order):
1. `parse_sources` - Extract source schemas in parallel
2. `parse_destinations` - Extract destination schemas in parallel
3. `create_context` - Initialize MappingContext
4. `identify_1_to_1` - LLM-based 1:1 mapping detection
5. `identify_n_to_1` - LLM-based aggregation detection
6. `identify_1_to_n` - LLM-based decomposition detection
7. `detect_destructive` - Flag risky operations
8. `resolve_order` - Determine execution sequence
9. `generate_code` - Create transformation code

**Graph Edge Flow**:
```
START
├→ parse_sources ──┐
└→ parse_destinations ──→ create_context → identify_1_to_1
                            ↓
                       identify_n_to_1
                            ↓
                       identify_1_to_n
                            ↓
                       detect_destructive
                            ↓
                       resolve_order
                            ↓
                       generate_code
                            ↓
                          END
```

### 6. Excel Exporter (src/exporters/)

**ExcelExporter** generates multi-tab Excel report:

| Tab | Purpose |
|-----|---------|
| Summary | Overall statistics and counts |
| 1:1 Mappings | Direct field-to-field mappings |
| N:1 Mappings | Aggregation rules with expressions |
| 1:N Mappings | Decomposition rules with expressions |
| Execution Order | Sequence with dependencies |
| Destructive Ops | Risk assessment for data-loss operations |
| Metadata | Context IDs and schema info |

**Features**:
- Color-coded cells (red=critical, yellow=warning)
- Cell comments with detailed explanations
- Formatted headers and data
- Type-specific sheets

## Data Flow Example: Multi-Source to Single Destination

```
Input: 2 source DDL files, 1 destination Excel

Step 1: Parse Sources
  source1.sql → Schema A (tables: employees)
    ├── emp_id: INTEGER
    ├── first_name: VARCHAR
    └── last_name: VARCHAR
    
  source2.sql → Schema B (tables: departments)
    ├── dept_id: INTEGER
    └── dept_name: VARCHAR

Step 2: Parse Destination
  template.xlsx → Schema C (sheet: Report)
    ├── EmployeeID: VARCHAR
    ├── FullName: VARCHAR
    └── Department: VARCHAR

Step 3: Create Context
  MappingContext with 2 source, 1 destination, 3 destination fields

Step 4: LLM Identifies Mappings
  1:1 Mapping:
    emp_id → EmployeeID
  
  N:1 Aggregation:
    (first_name, last_name) → FullName
    Strategy: CONCAT with space separator
    Risk: LOW, Destructive: NO
  
  1:1 Mapping:
    dept_name → Department

Step 5: Aggregation Engine
  Creates AggregationRule:
    CONCAT(emp.first_name, ' ', emp.last_name) → full_name
    Python: f"{first_name} {last_name}"

Step 6: Dependency Analyzer
  Execution Order:
    1. emp_id → EmployeeID (no dependencies)
    2. dept_name → Department (no dependencies)
    3. (first_name + last_name) → FullName (depends on source availability)

Step 7: Export to Excel
  Creates mapping_report.xlsx with all lineages and code
```

## Destructive Operations Detection

### Categories

| Type | Example | Risk |
|------|---------|------|
| NARROWING | VARCHAR(100) → VARCHAR(50) | CRITICAL |
| CONVERSION_RISK | DECIMAL → INTEGER | HIGH |
| AGGREGATION_LOSS | SUM([field1, field2]) loses details | MEDIUM |
| DECOMPOSITION_LOSS | SPLIT truncates unaligned data | MEDIUM |
| NULL_HANDLING | Source nullable, dest NOT NULL | MEDIUM |

### Detection Strategy

1. **Type Analysis**: Compare source and dest TypeInfo
2. **Strategy Assessment**: Evaluate aggregation/decomposition risk
3. **LLM Review**: Ask LLM to identify hidden data loss scenarios
4. **Confidence Scoring**: Rate risk probability

## Performance Characteristics

| Operation | Time |
|-----------|------|
| Parse 1000-field schema | < 1s |
| LLM mapping suggestion (batch 10) | 5-30s |
| Generate code for 100 mappings | < 1s |
| Create Excel report | < 2s |
| **Total workflow (typical)** | **10-40s** |

## Extensibility Points

### Adding New Source Format
1. Create parser class extending `DocumentParserBase`
2. Implement `can_parse()` and `parse()` methods
3. Return `ParsedContent` with normalized table structure
4. Register in `DocumentParser.parsers` list

### Adding New LLM Provider
1. Create class extending `LLMBase`
2. Implement `is_available()` and `invoke()` methods
3. Add to `LLMProvider.__init__()` initialization
4. Follows same fallback chain pattern

### Adding New Aggregation Strategy
1. Add strategy to `AggregationStrategy` enum
2. Implement logic in `AggregationEngine._generate_aggregation_code()`
3. Add template in `_init_strategy_templates()`

### Adding New Graph Node
1. Create node function receiving `WorkflowState`
2. Add to workflow via `workflow.add_node()`
3. Connect edges appropriately

## Error Handling Strategy

- **File not found**: Caught at CLI, exit gracefully
- **Parse errors**: Caught per parser, logged, continue with other files
- **LLM failures**: Caught, try fallback LLM, eventually fail if all unavailable
- **Type mismatches**: Detected and flagged as MEDIUM risk
- **Circular dependencies**: Detected and reported

All errors logged to console and included in Excel metadata.

## Security Considerations

- LLM API keys stored in .env (excluded from version control)
- No sensitive data logged by default
- File I/O restricted to specified paths
- LLM prompts don't include actual data (schema only)
