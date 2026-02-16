#!/usr/bin/env python3
"""
Text File Normalization Script
Removes hidden Unicode characters and enforces LF line endings
"""
import os
import sys


# Hidden Unicode characters to remove
HIDDEN_CHARS = [
    '\u202A',  # LEFT-TO-RIGHT EMBEDDING
    '\u202B',  # RIGHT-TO-LEFT EMBEDDING
    '\u202C',  # POP DIRECTIONAL FORMATTING
    '\u202D',  # LEFT-TO-RIGHT OVERRIDE
    '\u202E',  # RIGHT-TO-LEFT OVERRIDE
    '\u2066',  # LEFT-TO-RIGHT ISOLATE
    '\u2067',  # RIGHT-TO-LEFT ISOLATE
    '\u2068',  # FIRST STRONG ISOLATE
    '\u2069',  # POP DIRECTIONAL ISOLATE
    '\u200E',  # LEFT-TO-RIGHT MARK
    '\u200F',  # RIGHT-TO-LEFT MARK
    '\ufeff',  # ZERO WIDTH NO-BREAK SPACE (BOM)
]


def normalize_file(filepath):
    """
    Normalize a single file:
    - Remove hidden Unicode characters
    - Replace NBSP with regular space
    - Enforce LF line endings
    - Ensure UTF-8 encoding (no BOM)
    
    Args:
        filepath: Path to the file to normalize
    
    Returns:
        bool: True if file was modified, False otherwise
    """
    try:
        # Read file as bytes
        with open(filepath, 'rb') as f:
            raw_bytes = f.read()
        
        # Decode with error handling
        try:
            content = raw_bytes.decode('utf-8')
        except UnicodeDecodeError:
            content = raw_bytes.decode('utf-8', errors='replace')
            print(f"  WARNING: {filepath} had encoding errors (replaced)")
        
        original_content = content
        
        # Remove hidden Unicode characters
        for char in HIDDEN_CHARS:
            content = content.replace(char, '')
        
        # Replace NBSP with regular space
        content = content.replace('\u00A0', ' ')
        
        # Normalize line endings to LF
        content = content.replace('\r\n', '\n')
        content = content.replace('\r', '\n')
        
        # Check if file was modified
        if content == original_content:
            return False
        
        # Write back as UTF-8 (no BOM) with LF line endings
        with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        
        return True
        
    except Exception as e:
        print(f"  ERROR processing {filepath}: {e}")
        return False


def main():
    """
    Main function to normalize target files
    """
    # Target files to normalize
    target_files = [
        'core/middleware.py',
        'core/mixins.py',
        'finance/models.py',
        'tests/test_tenant_isolation.py',
        'greekfleet/settings.py',
        '.gitattributes',
    ]
    
    print("=" * 60)
    print("TEXT FILE NORMALIZATION")
    print("=" * 60)
    print()
    print("Target operations:")
    print("  - Remove Bidi/Hidden Unicode marks")
    print("  - Replace NBSP with ASCII space")
    print("  - Enforce LF line endings")
    print("  - Ensure UTF-8 (no BOM)")
    print()
    print("=" * 60)
    print()
    
    modified_count = 0
    skipped_count = 0
    error_count = 0
    
    for filepath in target_files:
        if not os.path.exists(filepath):
            print(f"SKIP: {filepath} (not found)")
            skipped_count += 1
            continue
        
        print(f"Processing: {filepath}")
        was_modified = normalize_file(filepath)
        
        if was_modified:
            print(f"  -> MODIFIED")
            modified_count += 1
        else:
            print(f"  -> OK (no changes needed)")
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Modified: {modified_count}")
    print(f"Skipped:  {skipped_count}")
    print(f"Errors:   {error_count}")
    print()
    
    if modified_count > 0:
        print("Files have been normalized successfully!")
        return 0
    else:
        print("All files were already normalized.")
        return 0


if __name__ == '__main__':
    sys.exit(main())
