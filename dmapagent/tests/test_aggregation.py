"""Unit tests for aggregation engine."""
import pytest
from src.mapping.aggregation_engine import AggregationEngine
from src.core.schema_extractor import Field
from src.core.data_types import TypeInfo, SQLDataType, TypeConverter


@pytest.fixture
def aggregation_engine():
    """Create aggregation engine."""
    return AggregationEngine()


@pytest.fixture
def sample_fields():
    """Create sample fields."""
    converter = TypeConverter()
    return {
        "first_name": Field(
            name="first_name",
            type_info=converter.parse_type_string("VARCHAR(50)"),
            table_name="employee",
        ),
        "last_name": Field(
            name="last_name",
            type_info=converter.parse_type_string("VARCHAR(50)"),
            table_name="employee",
        ),
        "salary": Field(
            name="salary",
            type_info=converter.parse_type_string("DECIMAL(10,2)"),
            table_name="employee",
        ),
        "bonus": Field(
            name="bonus",
            type_info=converter.parse_type_string("DECIMAL(10,2)"),
            table_name="employee",
        ),
        "full_name": Field(
            name="full_name",
            type_info=converter.parse_type_string("VARCHAR(200)"),
            table_name="report",
        ),
        "total_comp": Field(
            name="total_comp",
            type_info=converter.parse_type_string("DECIMAL(15,2)"),
            table_name="report",
        ),
    }


def test_analyze_string_aggregation(aggregation_engine, sample_fields):
    """Test aggregation of string fields."""
    rule = aggregation_engine.analyze_aggregation(
        [sample_fields["first_name"], sample_fields["last_name"]],
        sample_fields["full_name"],
    )
    
    assert rule is not None
    assert rule.strategy.value == "CONCAT"
    assert not rule.is_destructive


def test_analyze_numeric_aggregation(aggregation_engine, sample_fields):
    """Test aggregation of numeric fields."""
    rule = aggregation_engine.analyze_aggregation(
        [sample_fields["salary"], sample_fields["bonus"]],
        sample_fields["total_comp"],
    )
    
    assert rule is not None
    assert rule.strategy.value == "SUM"
    assert rule.is_destructive  # SUM is destructive


def test_validate_aggregation(aggregation_engine, sample_fields):
    """Test validation of aggregation rule."""
    rule = aggregation_engine.analyze_aggregation(
        [sample_fields["first_name"], sample_fields["last_name"]],
        sample_fields["full_name"],
    )
    
    assert aggregation_engine.validate_aggregation(rule)
