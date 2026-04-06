"""Main entry point for Data Mapping Agent."""
import argparse
import sys
from pathlib import Path
from src.graph.workflow import run_mapping_workflow
from src.exporters.excel_exporter import ExcelExporter
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Data Mapping Agent - Schema transformation and field mapping"
    )
    
    parser.add_argument(
        "--source",
        nargs="+",
        required=True,
        help="Source file(s) (DDL, Excel, HTML, PDF, Word)",
    )
    
    parser.add_argument(
        "--destination",
        nargs="+",
        required=True,
        help="Destination file(s)",
    )
    
    parser.add_argument(
        "--output",
        default="mapping_report.xlsx",
        help="Output Excel file path",
    )
    
    args = parser.parse_args()
    
    # Validate files exist
    for file_path in args.source + args.destination:
        if not Path(file_path).exists():
            logger.error(f"File not found: {file_path}")
            sys.exit(1)
    
    logger.info(f"Starting mapping workflow")
    logger.info(f"Sources: {args.source}")
    logger.info(f"Destinations: {args.destination}")
    logger.info(f"Output: {args.output}")
    
    # Run workflow
    try:
        state = run_mapping_workflow(args.source, args.destination)
        
        if state.errors:
            logger.error(f"Workflow completed with {len(state.errors)} errors")
            for error in state.errors:
                logger.error(f"  - {error}")
        
        if state.warnings:
            logger.warning(f"Workflow has {len(state.warnings)} warnings")
            for warning in state.warnings:
                logger.warning(f"  - {warning}")
        
        # Export to Excel
        exporter = ExcelExporter(args.output)
        if state.mapping_context and exporter.export(state.mapping_context):
            logger.info(f"Successfully exported mapping report to {args.output}")
        else:
            logger.error("Failed to export mapping report")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
