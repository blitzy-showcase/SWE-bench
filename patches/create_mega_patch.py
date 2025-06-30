#!/usr/bin/env python3
"""
Script to combine multiple patch files into a single mega patch file.
Includes proper Unicode handling to avoid decoding errors.
"""

import os
import sys
from pathlib import Path


def create_mega_patch(patch_files=None, output_file="mega_patch.patch"):
    """
    Combine multiple patch files into a single mega patch.
    
    Args:
        patch_files: List of patch file paths. If None, auto-detects .patch files
        output_file: Name of the output mega patch file
    """
    # If no patch files specified, auto-detect in current directory
    if patch_files is None:
        patch_files = sorted(Path(".").glob("*.patch"))
        # Exclude the output file if it exists
        patch_files = [f for f in patch_files if f.name != output_file]
        
        if not patch_files:
            print("No patch files found in current directory")
            return
        
        print(f"Auto-detected {len(patch_files)} patch files:")
        for pf in patch_files:
            print(f"  - {pf}")
    
    # Create the mega patch
    with open(output_file, 'w', encoding='utf-8') as mega_file:
        for i, patch_file in enumerate(patch_files):
            if i > 0:
                # Add separator between patches
                mega_file.write("\n\n")
            
            # Write patch identifier
            patch_name = Path(patch_file).stem
            mega_file.write(f"# ===== Patch from {patch_name} =====\n")
            
            # Read and write patch content with proper encoding
            try:
                with open(patch_file, 'r', encoding='utf-8') as pf:
                    content = pf.read()
                    mega_file.write(content)
                    
                    # Ensure patch ends with newline
                    if not content.endswith('\n'):
                        mega_file.write('\n')
                        
            except UnicodeDecodeError as e:
                print(f"Warning: Unicode decode error in {patch_file}: {e}")
                # Try with different encoding or error handling
                try:
                    with open(patch_file, 'r', encoding='utf-8', errors='replace') as pf:
                        content = pf.read()
                        mega_file.write(content)
                        if not content.endswith('\n'):
                            mega_file.write('\n')
                    print(f"  - Recovered using error replacement")
                except Exception as e2:
                    print(f"  - Failed to read patch: {e2}")
                    continue
    
    print(f"\nCreated mega patch: {output_file}")
    
    # Show file size
    size = os.path.getsize(output_file)
    print(f"File size: {size:,} bytes")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Use provided patch files
        patch_files = sys.argv[1:]
        create_mega_patch(patch_files)
    else:
        # Auto-detect patch files
        create_mega_patch()


if __name__ == "__main__":
    main()
