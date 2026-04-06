"""Unit tests for mapper."""
import pytest
from src.mapping.mapper import DataMapper
from src.mapping.mapping_lineage import MappingLineage, MappingType
from src.core.schema_extractor import Schema, Field
from src.core.data_types import TypeConverter


@pytest.fixture
def mapper():
    """Create mapper instance."""
    return DataMapper()


@pytest.fixture
def sample_schemas():
    """Create sample schemas."""
    converter = TypeConverter()
    
    source_schema = Schema(name="source")
    source_fields = [
        Field(
            name="id",
            type_info=converter.parse_type_string("INTEGER"),
            table_name="users",
        ),
        Field(
            name="name",
            type_info=converter.parse_type_string("VARCHAR(100)"),
            table_name="users",
        ),
    ]
    source_schema.add_table("users", source_fields)
    
    dest_schema = Schema(name="destination")
    dest_fields = [
        Field(
            name="user_id",
            type_info=converter.parse_type_string("VARCHAR(50)"),
            table_name="report",
        ),
        Field(
            name="user_name",
            type_info=converter.parse_type_string("VARCHAR(200)"),
            table_name="report",
        ),
    ]
    dest_schema.add_table("report", dest_fields)
    
    return {"source": source_schema, "dest": dest_schema}


def test_mapper_initialization(mapper):
    """Test mapper initialization."""
    context = mapper.get_context()
    assert context is not None
    assert len(context.lineages) == 0


def test_set_schemas(mapper, sample_schemas):
    """Test setting schemas."""
    mapper.set_source_schemas({"source": sample_schemas["source"]})
    mapper.set_destination_schemas({"dest": sample_schemas["dest"]})
    
    context = mapper.get_context()
    assert "source" in context.source_schemas
    assert "dest" in context.destination_schemas


def test_mapper_reset(mapper):
    """Test mapper reset."""
    mapper.reset()
    context = mapper.get_context()
    assert len(context.lineages) == 0
