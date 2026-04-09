import os
import re

def process_html_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add security meta tags to <head> if not present
    meta_tags = """
    <!-- Security Headers -->
    <meta http-equiv="X-XSS-Protection" content="1; mode=block">
    <meta http-equiv="X-Content-Type-Options" content="nosniff">
    <meta name="referrer" content="strict-origin-when-cross-origin">
    <!-- Performance Optimization -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
"""
    if 'X-XSS-Protection' not in content:
        content = content.replace('</title>', '</title>' + meta_tags)

    # Defer external scripts
    content = re.sub(r'<script\s+src="([^"]+)"(?!\s+defer)>', r'<script src="\1" defer>', content)

    # Lazy load images that are below the fold (not in hero, navbar, or logo)
    # Simple regex approach: add loading="lazy" to all <img ...> unless they have class="logo" or class="main-plate-img" or id="main-plate-img"
    
    def replacer(match):
        img_tag = match.group(0)
        class_str = match.group(2) if match.group(2) else ""
        if 'loading=' in img_tag:
            return img_tag
        # Check if the image seems essential/above the fold based on attributes
        if 'logo' in img_tag or 'hero' in img_tag or 'main-plate-img' in img_tag:
            return img_tag
        # Add loading="lazy"
        return img_tag.replace('<img ', '<img loading="lazy" ')

    # Matches <img ... (class="...")? ...>
    content = re.sub(r'<img\s+([^>]*?(class="([^"]+)")?[^>]*?)>', replacer, content)

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

folder = '.'
for file in os.listdir(folder):
    if file.endswith('.html'):
        path = os.path.join(folder, file)
        process_html_file(path)
        print(f"Hardened {file}")
