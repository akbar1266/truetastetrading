import os
import glob
import re
import shutil
from datetime import datetime

assets_dir = 'assets'
trash_dir = 'image-trash'

# Create trash directory
if not os.path.exists(trash_dir):
    os.makedirs(trash_dir)

# Read all code files for usage checking
code_files = []
for ext in ['*.html', '*.css', '*.js']:
    code_files.extend(glob.glob(ext))

code_content = ""
for file in code_files:
    with open(file, 'r', encoding='utf-8') as f:
        code_content += f.read()

# Get all images
image_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.avif', '.svg', '.gif')
all_images = []
for root, dirs, files in os.walk(assets_dir):
    for filename in files:
        if filename.lower().endswith(image_extensions):
            full_path = os.path.join(root, filename)
            size = os.path.getsize(full_path)
            # Use forward slashes for URL-like matching
            rel_path = os.path.relpath(full_path, start='.').replace('\\', '/')
            all_images.append({
                'path': full_path,
                'rel_path': rel_path,
                'filename': filename,
                'size': size,
                'modified': datetime.fromtimestamp(os.path.getmtime(full_path)).strftime('%Y-%m-%d %H:%M:%S')
            })

# Usage Analysis
used_images = []
unused_images = []

for img in all_images:
    # URL encoded version of the filename in case there are spaces exactly matched
    import urllib.parse
    url_encoded = urllib.parse.quote(img['filename'])
    
    # We will search for literal occurrences of the filename or url-encoded filename
    # Also check if the rel_path is explicitly used (since the filename might be too generic like '1.png')
    rel_path_encoded = urllib.parse.quote(img['rel_path'])
    
    # We will just do simple text search. If the exact filename or the url-encoded filename appears in the code,
    # or if the rel_path appears, it's used.
    # To be extremely safe, check if filename is anywhere. (Since "1.png" might be risky, we check rel_path)
    
    # Since this is a static site with simple paths like assets/mixmasala/beef.png
    # Let's check if the specific image path or its parts are referenced.
    
    path_str = img['rel_path']  # e.g., assets/mixmasala/beef.png
    path_esc = path_str.replace(" ", "%20") # handles spaces
    
    if path_str in code_content or path_esc in code_content:
        used_images.append(img)
    elif img['filename'] in code_content or url_encoded in code_content:
        # Generic match but safe
        used_images.append(img)
    else:
        unused_images.append(img)

# Move unused to trash
total_moved_size = 0
for img in unused_images:
    dest = os.path.join(trash_dir, img['rel_path'])
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.move(img['path'], dest)
    total_moved_size += img['size']

# Generate Markdown Report
md = "# Image Cleanup Report\n\n"
md += "## Verification Results\n"
md += f"- **Images scanned**: {len(all_images)}\n"
md += f"- **Images confirmed in use**: {len(used_images)}\n"
md += f"- **Unused images moved to review**: {len(unused_images)}\n"
md += f"- **Disk space reduced**: {total_moved_size / 1024 / 1024:.2f} MB\n\n"

md += "## Move Log (To `image-trash/`)\n"
if unused_images:
    for img in unused_images:
        md += f"- `{img['rel_path']}` ({img['size'] // 1024} KB)\n"
else:
    md += "- No unused images found.\n"

with open("cleanup_report.md", "w", encoding="utf-8") as f:
    f.write(md)

print("Cleanup script executed. Check cleanup_report.md.")
