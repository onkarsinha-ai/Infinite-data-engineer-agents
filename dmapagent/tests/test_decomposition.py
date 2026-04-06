"""Unit tests for decomposition engine."""
import pytest
from src.mapping.decomposition_engine import DecompositionEngine
from src.core.schema_extractor import Field
from src.core.data_types import TypeConverter


@pytest.fixture
def decomposition_engine():
    """Create decomposition engine."""
    return DecompositionEngine()


@pytest.fixture
def sample_fields():
    """Create sample fields."""
    converter = TypeConverter()
    return {
        "full_name": Field(
            name="full_name",
            type_info=converter.parse_type_string("VARCHAR(100)"),
            table_name="source",
        ),
        "first_name": Field(
            name="first_name",
            type_info=converter.parse_type_string("VARCHAR(50)"),
            table_name="dest",
        ),
        "last_name": Field(
            name="last_name",
            type_info=converter.parse_type_string("VARCHAR(50)"),
            table_name="dest",
        ),
    }


def test_analyze_string_decomposition(decomposition_engine, sample_fields):
    """Test decomposition of string field."""
    rule = decomposition_engine.analyze_decomposition(
        sample_fields["full_name"],
        [sample_fields["first_name"], sample_fields["last_name"]],
    )
    
    assert rule is not None
    assert rule.strategy.value == "SPLIT"
    assert rule.is_destructive  # Decomposition is destructive


def test_validate_decomposition(decomposition_engine, sample_fields):
    """Test validation of decomposition rule."""
    rule = decomposition_engine.analyze_decomposition(
        sample_fields["full_name"],
        [sample_fields["first_name"], sample_fields["last_name"]],
    )
    
    assert decomposition_engine.validate_decomposition(rule)
