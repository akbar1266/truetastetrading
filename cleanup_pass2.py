import os
import glob
import re
import shutil

assets_dir = 'assets'
trash_dir = 'image-trash'
HTML_FILES = glob.glob('*.html')

# Ensure trash dir exists
os.makedirs(trash_dir, exist_ok=True)

moved_files = []
total_saved_size = 0

# 1. Update HTML files to point img src fallback to .webp instead of .png/.jpg/.jpeg
for html_file in HTML_FILES:
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()

    # Regex to find <img ... src="assets/...png/jpg/jpeg">
    # We'll just replace .png/.jpg/.jpeg with .webp in src attributes if the .webp exists
    
    def replacer(match):
        pre = match.group(1)
        path = match.group(2)
        ext = match.group(3)
        post = match.group(4)
        
        webp_path = path + '.webp'
        # Check if the webp exists locally
        if os.path.exists(webp_path):
            return f'{pre}{webp_path}{post}'
        return match.group(0)

    # replace src="..." if it ends in png/jpg/jpeg
    new_html = re.sub(r'(src=")(assets/[^"]+?)(\.(png|jpg|jpeg))(")', replacer, html, flags=re.IGNORECASE)
    
    # 2. Also replace data-img="..." if any
    new_html = re.sub(r'(data-img=")(assets/[^"]+?)(\.(png|jpg|jpeg))(")', replacer, new_html, flags=re.IGNORECASE)

    if new_html != html:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(new_html)

# Now scan assets completely to see which original files are truly unused now!
code_content = ""
for file in glob.glob('*.html') + glob.glob('*.css') + glob.glob('*.js'):
    with open(file, 'r', encoding='utf-8') as f:
        code_content += f.read()

import urllib.parse
for root, dirs, files in os.walk(assets_dir):
    for filename in files:
        full_path = os.path.join(root, filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg']:
            rel_path = os.path.relpath(full_path, start='.').replace('\\', '/')
            # Is it explicitly in the code anymore?
            
            path_esc = rel_path.replace(" ", "%20")
            url_encoded = urllib.parse.quote(filename)
            
            if rel_path not in code_content and path_esc not in code_content and filename not in code_content and url_encoded not in code_content:
                # Move to trash
                dest = os.path.join(trash_dir, rel_path)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                size = os.path.getsize(full_path)
                shutil.move(full_path, dest)
                total_saved_size += size
                moved_files.append((rel_path, size))

# Append to markdown
with open('cleanup_report.md', 'a', encoding='utf-8') as f:
    f.write("\n## Second Pass (Removing Original PNG/JPG Fallbacks)\n")
    if moved_files:
        for p, s in moved_files:
            f.write(f"- `{p}` ({s // 1024} KB)\n")
        f.write(f"\n**Extra Disk Space Reduced**: {total_saved_size / 1024 / 1024:.2f} MB\n")
    else:
        f.write("- No extra files moved.\n")

print("Second pass complete!")

