"""Unit tests for document parser."""
import pytest
import tempfile
import os
from src.core.document_parser import DDLParser, DocumentParser


@pytest.fixture
def sample_ddl_file():
    """Create a temporary DDL file."""
    sql_content = """
    CREATE TABLE employees (
        emp_id INTEGER PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        salary DECIMAL(10,2),
        hire_date DATE
    );
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
        f.write(sql_content)
        return f.name


def test_ddl_parser(sample_ddl_file):
    """Test DDL parser."""
    parser = DDLParser()
    
    assert parser.can_parse(sample_ddl_file)
    
    parsed = parser.parse(sample_ddl_file)
    
    assert parsed.source_type == "ddl"
    assert "employees" in parsed.tables
    assert len(parsed.tables["employees"]) == 5
    
    # Clean up
    os.unlink(sample_ddl_file)


def test_document_parser_routing(sample_ddl_file):
    """Test document parser routing."""
    parser = DocumentParser()
    
    parsed = parser.parse(sample_ddl_file)
    
    assert parsed.source_type == "ddl"
    assert len(parsed.tables) > 0
    
    # Clean up
    os.unlink(sample_ddl_file)
