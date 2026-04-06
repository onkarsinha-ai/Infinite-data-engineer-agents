# Usage Examples

## CLI Examples

### Basic Usage

```bash
# Simple 1:1 mapping
python main.py \
  --source employees.sql \
  --destination employee_report.xlsx \
  --output mapping.xlsx
```

### Multiple Sources (N:1 Scenario)

```bash
# Combine two source schemas into one destination
python main.py \
  --source employee.sql department.sql \
  --destination combined_report.xlsx \
  --output mapping.xlsx

# Output will include:
# - Direct 1:1 mappings
# - Aggregation rules for combining fields
# - Execution order respecting dependencies
```

### Multiple Destinations (1:N Scenario)

```bash
# Map one source to multiple destinations
python main.py \
  --source master_data.sql \
  --destination sales_template.xlsx billing_template.xlsx \
  --output mapping.xlsx

# Output will include:
# - Decomposition rules where needed
# - Field reuse across destinations
# - Separate transformation for each dest schema
```

### Mixed Format Sources

```bash
# Combine different source formats
python main.py \
  --source \
    schema_definition.sql \
    employee_list.xlsx \
    contact_data.pdf \
  --destination \
    report_template.xlsx \
  --output mapping.xlsx
```

## Python API Examples

### Example 1: Basic Programmatic Usage

```python
from src.core.schema_extractor import SchemaExtractor
from src.mapping.mapper import DataMapper
from src.graph.workflow import run_mapping_workflow
from src.exporters.excel_exporter import ExcelExporter

# Extract schemas
extractor = SchemaExtractor()
source_schema = extractor.extract_from_file("employees.sql", "Employee")
dest_schema = extractor.extract_from_file("report.xlsx", "Report")

# Run mapping workflow
state = run_mapping_workflow(
    source_files=["employees.sql"],
    destination_files=["report.xlsx"]
)

# Export results
exporter = ExcelExporter("mapping_report.xlsx")
exporter.export(state.mapping_context)

print(f"Generated {len(state.one_to_one_mappings)} 1:1 mappings")
print(f"Generated {len(state.many_to_one_mappings)} N:1 aggregations")
print(f"Found {len(state.destructive_mappings)} destructive operations")
```

### Example 2: Custom Aggregation Analysis

```python
from src.mapping.aggregation_engine import AggregationEngine
from src.core.schema_extractor import Field, SchemaExtractor
from src.core.data_types import TypeInfo, SQLDataType

# Extract source fields
extractor = SchemaExtractor()
schema = extractor.extract_from_file("employee_data.sql")
table_fields = schema.get_table("Employee")

# Create aggregation rule manually
agg_engine = AggregationEngine()

first_name = table_fields[0]  # VARCHAR field
last_name = table_fields[1]   # VARCHAR field
full_name = Field(
    name="full_name",
    type_info=TypeInfo(base_type=SQLDataType.VARCHAR, precision=100),
    table_name="Report"
)

# Analyze aggregation
rule = agg_engine.analyze_aggregation([first_name, last_name], full_name)

if rule:
    print(f"Aggregation Strategy: {rule.strategy}")
    print(f"Expression: {rule.aggregation_expression}")
    print(f"Generated Code:\n{rule.aggregation_code}")
    print(f"Is Destructive: {rule.is_destructive}")
    print(f"Data Loss: {rule.data_loss_description}")
```

### Example 3: Detecting Destructive Operations

```python
from src.core.data_types import TypeConverter, TypeInfo, SQLDataType

converter = TypeConverter()

# Narrowing conversion (destructive)
source_type = TypeInfo(SQLDataType.VARCHAR, precision=100)
dest_type = TypeInfo(SQLDataType.VARCHAR, precision=50)

narrowing = converter.is_type_narrowing(source_type, dest_type)
risk = converter.get_conversion_risk(source_type, dest_type)

print(f"Narrowing: {narrowing}")  # True
print(f"Risk Level: {risk}")  # CRITICAL

# Widening conversion (safe)
source_type = TypeInfo(SQLDataType.INTEGER)
dest_type = TypeInfo(SQLDataType.BIGINT)

widening = converter.is_type_widening(source_type, dest_type)
risk = converter.get_conversion_risk(source_type, dest_type)

print(f"Widening: {widening}")  # True
print(f"Risk Level: {risk}")  # LOW
```

### Example 4: Decomposition Analysis

```python
from src.mapping.decomposition_engine import DecompositionEngine

# Decompose full name into first and last
decomp_engine = DecompositionEngine()

source_schema = extractor.extract_from_file("source.sql")
dest_schema = extractor.extract_from_file("dest.xlsx")

source_field = source_schema.get_field("Person", "full_name")
dest_fields = [
    dest_schema.get_field("Report", "first_name"),
    dest_schema.get_field("Report", "last_name")
]

# Analyze decomposition
rule = decomp_engine.analyze_decomposition(source_field, dest_fields)

if rule:
    print(f"Strategy: {rule.strategy}")
    print(f"Expression: {rule.decomposition_expression}")
    print(f"Code:\n{rule.decomposition_code}")
    print(f"Destructive: {rule.is_destructive}")
    print(f"Data Loss Risk: {rule.data_loss_description}")
```

### Example 5: Dependency Resolution

```python
from src.mapping.dependency_analyzer import DependencyAnalyzer
from src.mapping.mapping_lineage import MappingLineage, MappingType

# Create mappings with dependencies
mapping1 = MappingLineage(
    mapping_type=MappingType.ONE_TO_ONE,
    source_fields=[source_field1],
    destination_field=dest_field1
)

mapping2 = MappingLineage(
    mapping_type=MappingType.ONE_TO_ONE,
    source_fields=[source_field2],
    destination_field=dest_field2
)

mapping3 = MappingLineage(
    mapping_type=MappingType.MANY_TO_ONE,
    source_fields=[source_field1, source_field2],
    destination_field=combined_field
)
mapping3.add_dependency(mapping1.mapping_id)
mapping3.add_dependency(mapping2.mapping_id)

# Analyze dependencies
analyzer = DependencyAnalyzer()
execution_order = analyzer.resolve_execution_order([mapping1, mapping2, mapping3])

print(f"Execution order: {execution_order}")
# Output: [mapping1.id, mapping2.id, mapping3.id] or similar ordering

# Check for circular dependencies
cycles = analyzer.detect_circular_dependencies()
print(f"Circular dependencies: {cycles}")  # []
```

### Example 6: Custom Excel Export

```python
from src.exporters.excel_exporter import ExcelExporter
from src.mapping.mapping_lineage import MappingContext

# Create context with mappings
context = MappingContext()
context.source_schemas = {"Employee": source_schema}
context.destination_schemas = {"Report": dest_schema}
context.add_lineage(mapping1)
context.add_lineage(mapping2)

# Export with custom path
exporter = ExcelExporter("custom_output/mappings_report.xlsx")
success = exporter.export(context)

if success:
    print("Excel report generated successfully!")
    stats = context.get_statistics()
    print(f"Total mappings: {stats['total_mappings']}")
    print(f"Destructive: {stats['destructive_mappings']}")
```

### Example 7: Using Multiple LLM Providers

```python
from src.llm.llm_provider import get_llm_provider
from src.llm.prompts import MappingPrompts

# Get LLM provider (automatically tries Gemini > Claude > Ollama)
llm = get_llm_provider()

print(f"Using LLM: {llm.get_current_llm_name()}")
print(f"Available LLMs: {llm.get_available_llms()}")

# Use LLM for mapping suggestions
source_fields = ["emp_id", "first_name", "last_name"]
dest_fields = ["EmployeeID", "FullName"]

prompt = MappingPrompts.identify_one_to_one_mappings(source_fields, dest_fields)
response = llm.invoke(prompt)

print(response)
```

### Example 8: Batch Processing Multiple Mappings

```python
from pathlib import Path
import json

# Process multiple file pairs
source_files = Path("sources").glob("*.sql")
dest_files = Path("destinations").glob("*.xlsx")

results = []

for src, dest in zip(sorted(source_files), sorted(dest_files)):
    print(f"Processing {src.name} -> {dest.name}")
    
    state = run_mapping_workflow([str(src)], [str(dest)])
    
    results.append({
        "source": src.name,
        "destination": dest.name,
        "status": "success" if not state.errors else "failed",
        "errors": state.errors,
        "warnings": state.warnings,
        "mappings": {
            "one_to_one": len(state.one_to_one_mappings),
            "many_to_one": len(state.many_to_one_mappings),
            "one_to_many": len(state.one_to_many_mappings),
            "destructive": len(state.destructive_mappings)
        }
    })

# Save batch results
with open("batch_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"Processed {len(results)} mappings")
```

## Configuration Examples

### .env File

```ini
# Google Gemini (preferred)
GOOGLE_API_KEY=AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Anthropic Claude (fallback 1)
ANTHROPIC_API_KEY=sk-ant-v0-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Ollama (fallback 2)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma2

# LLM Settings
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# Logging
LOG_LEVEL=INFO
```

### Advanced Configuration

```python
# Custom configuration in code
from config import DMAPSettings

settings = DMAPSettings(
    GOOGLE_API_KEY="your_key",
    LLM_TEMPERATURE=0.5,
    LLM_MAX_TOKENS=2048,
    LOG_LEVEL="DEBUG"
)
```

## Output Examples

### Excel Report Preview

**Summary Tab**:
```
Data Mapping Report
Generated: 2024-01-15T10:30:00

Mapping Summary
Total Mappings: 15
1:1 Mappings: 10
N:1 Mappings (Aggregation): 3
1:N Mappings (Decomposition): 2
Destructive Mappings: 2
Unmapped Source Fields: 0
Unmapped Destination Fields: 0
Circular Dependencies: 0
```

**N:1 Mappings Tab Example**:
```
| Mapping ID | Source Fields | Destination | Strategy | Destructive? |
|------------|---------------|-------------|----------|--------------|
| map_001    | first_name, last_name | full_name | CONCAT | No |
| map_002    | salary_base, bonus | annual_comp | SUM | Yes (precision loss) |
```

**Destructive Operations Tab**:
```
| Mapping ID | Type | Severity | Details | Recommendation |
|------------|------|----------|---------|-----------------|
| map_005    | 1:1  | CRITICAL | VARCHAR(100)→VARCHAR(50) | Review data before narrowing |
| map_002    | N:1  | MEDIUM   | SUM loses individual values | Document in data dictionary |
```

---

For more information, see `docs/architecture.md` and `README.md`
