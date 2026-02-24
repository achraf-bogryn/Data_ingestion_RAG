"""
Utility functions for the ISO 13485 QMS Procedure Guide

Includes:
- JSON validation
- Knowledge base integrity checks
- Data loading helpers
"""

import json
from pathlib import Path


def validate_procedure_json(filepath: str) -> tuple[bool, list]:
    """
    Validate the procedure JSON structure
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return False, [f"File not found: {filepath}"]
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {str(e)}"]
    
    # Check required top-level structure
    if 'procedure' not in data:
        errors.append("Missing 'procedure' key at root level")
        return False, errors
    
    proc = data['procedure']
    
    # Check required procedure fields
    required_fields = ['id', 'title', 'version', 'standard', 'purpose', 'sections']
    for field in required_fields:
        if field not in proc:
            errors.append(f"Missing required field: procedure.{field}")
    
    # Check sections structure
    if 'sections' in proc:
        for section_num, section_data in proc['sections'].items():
            if not isinstance(section_data, dict):
                errors.append(f"Section {section_num} is not a dictionary")
                continue
            
            required_section_fields = ['section_number', 'section_title']
            for field in required_section_fields:
                if field not in section_data:
                    errors.append(f"Section {section_num} missing: {field}")
    
    # Check document control information
    if 'document_control_information' not in proc:
        errors.append("Missing 'document_control_information'")
    else:
        dci = proc['document_control_information']
        if 'must_contain' not in dci:
            errors.append("document_control_information missing 'must_contain'")
    
    # Check key explanations and common mistakes
    if 'key_explanations' not in proc:
        errors.append("Missing 'key_explanations'")
    if 'common_mistakes' not in proc:
        errors.append("Missing 'common_mistakes'")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def load_procedure_data(filepath: str) -> dict:
    """
    Load and validate procedure data from JSON
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Procedure data dictionary
        
    Raises:
        ValueError: If validation fails
    """
    is_valid, errors = validate_procedure_json(filepath)
    
    if not is_valid:
        error_msg = "Validation errors:\n" + "\n".join(errors)
        raise ValueError(error_msg)
    
    with open(filepath, 'r') as f:
        return json.load(f)


def get_procedure_statistics(procedure_data: dict) -> dict:
    """
    Get statistics about the procedure
    
    Args:
        procedure_data: Loaded procedure data
        
    Returns:
        Dictionary with statistics
    """
    proc = procedure_data['procedure']
    
    section_count = len(proc.get('sections', {}))
    subsection_count = sum(
        len(s.get('subsections', {})) 
        for s in proc.get('sections', {}).values()
    )
    definition_count = len(proc.get('key_explanations', {}))
    mistake_count = len(proc.get('common_mistakes', []))
    
    total_must_contain_items = sum(
        len(s.get('must_contain', [])) 
        for s in proc.get('sections', {}).values()
    ) + len(proc.get('document_control_information', {}).get('must_contain', []))
    
    return {
        'procedure_id': proc.get('id'),
        'procedure_title': proc.get('title'),
        'standard': proc.get('standard'),
        'version': proc.get('version'),
        'sections': section_count,
        'subsections': subsection_count,
        'total_definitions': definition_count,
        'common_mistakes': mistake_count,
        'must_contain_items': total_must_contain_items,
    }


def print_procedure_statistics(procedure_data: dict) -> None:
    """
    Print procedure statistics in a formatted way
    
    Args:
        procedure_data: Loaded procedure data
    """
    stats = get_procedure_statistics(procedure_data)
    
    print("\n" + "="*60)
    print("PROCEDURE STATISTICS")
    print("="*60)
    print(f"ID: {stats['procedure_id']}")
    print(f"Title: {stats['procedure_title']}")
    print(f"Standard: {stats['standard']}")
    print(f"Version: {stats['version']}")
    print("-"*60)
    print(f"Main Sections: {stats['sections']}")
    print(f"Subsections: {stats['subsections']}")
    print(f"Key Terms Defined: {stats['total_definitions']}")
    print(f"Common Mistakes Listed: {stats['common_mistakes']}")
    print(f"Total Must-Contain Items: {stats['must_contain_items']}")
    print("="*60 + "\n")


def export_procedure_to_markdown(procedure_data: dict, output_file: str = "procedure.md") -> None:
    """
    Export procedure to Markdown format
    
    Args:
        procedure_data: Loaded procedure data
        output_file: Path for output markdown file
    """
    proc = procedure_data['procedure']
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write(f"# {proc['title']}\n\n")
        f.write(f"**Standard:** {proc['standard']}\n")
        f.write(f"**Version:** {proc['version']}\n")
        f.write(f"**ID:** {proc['id']}\n\n")
        
        # Purpose
        f.write("## Purpose\n\n")
        f.write(f"{proc['purpose']}\n\n")
        
        # Sections
        f.write("## Contents\n\n")
        for section_num in sorted(proc['sections'].keys()):
            section = proc['sections'][section_num]
            f.write(f"### Section {section_num}: {section['section_title']}\n\n")
            f.write(f"{section.get('description', '')}\n\n")
            
            f.write("**Must Contain:**\n")
            for item in section.get('must_contain', []):
                f.write(f"- {item}\n")
            f.write("\n")
            
            if 'example_text' in section:
                f.write(f"**Example:**\n```\n{section['example_text']}\n```\n\n")
            
            # Subsections
            if 'subsections' in section:
                for sub_id, subsection in section['subsections'].items():
                    f.write(f"#### {sub_id}: {subsection['title']}\n\n")
                    for item in subsection.get('must_contain', []):
                        f.write(f"- {item}\n")
                    f.write("\n")
        
        # Definitions
        f.write("## Key Definitions\n\n")
        for term, explanation in proc.get('key_explanations', {}).items():
            f.write(f"**{term.replace('_', ' ').title()}:** {explanation}\n\n")
        
        # Common Mistakes
        f.write("## Common Mistakes\n\n")
        for i, mistake in enumerate(proc.get('common_mistakes', []), 1):
            f.write(f"{i}. {mistake}\n\n")
    
    print(f"✓ Procedure exported to {output_file}")


def count_content_items(procedure_data: dict) -> dict:
    """
    Count different types of content in the procedure
    
    Args:
        procedure_data: Loaded procedure data
        
    Returns:
        Dictionary with content counts
    """
    proc = procedure_data['procedure']
    
    counts = {
        'sections': len(proc.get('sections', {})),
        'subsections': 0,
        'must_contain_items': 0,
        'examples': 0,
        'definitions': len(proc.get('key_explanations', {})),
        'common_mistakes': len(proc.get('common_mistakes', [])),
    }
    
    for section in proc.get('sections', {}).values():
        counts['must_contain_items'] += len(section.get('must_contain', []))
        if section.get('example_text'):
            counts['examples'] += 1
        
        if 'subsections' in section:
            counts['subsections'] += len(section['subsections'])
            for subsection in section['subsections'].values():
                counts['must_contain_items'] += len(subsection.get('must_contain', []))
                if subsection.get('example_text'):
                    counts['examples'] += 1
    
    return counts


# ============================================================================
# MAIN - For testing and validation
# ============================================================================

if __name__ == "__main__":
    import sys
    
    procedure_file = "procedure_db.json"
    
    # Check if file exists
    if not Path(procedure_file).exists():
        print(f"Error: {procedure_file} not found")
        sys.exit(1)
    
    print("Validating procedure JSON...")
    is_valid, errors = validate_procedure_json(procedure_file)
    
    if is_valid:
        print("✓ JSON structure is valid\n")
        
        # Load and display statistics
        try:
            data = load_procedure_data(procedure_file)
            print_procedure_statistics(data)
            
            # Count content
            counts = count_content_items(data)
            print("\nContent Summary:")
            print(f"- Sections: {counts['sections']}")
            print(f"- Subsections: {counts['subsections']}")
            print(f"- Must-Contain Items: {counts['must_contain_items']}")
            print(f"- Examples: {counts['examples']}")
            print(f"- Definitions: {counts['definitions']}")
            print(f"- Common Mistakes: {counts['common_mistakes']}")
            
            # Export to markdown
            export_procedure_to_markdown(data, "procedure_export.md")
            
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        print("✗ JSON validation failed:\n")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)