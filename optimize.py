import os
import glob
from PIL import Image
import pillow_heif
from bs4 import BeautifulSoup
import re

try:
    pillow_heif.register_avif_opener()
except AttributeError:
    pillow_heif.register_heif_opener()

ASSETS_DIR = 'assets'
HTML_FILES = glob.glob('*.html')
CSS_FILES = glob.glob('*.css')
JS_FILES = glob.glob('*.js')

# We'll generate a single webp and avif for each image, with a max dimension of 1200px (to keep things simple but performant).
# And a smaller thumb version if it's used in cards? For simplicity and high impact, we'll produce .webp and .avif
# and we will update HTML to use <picture> tags or just change the src to .webp across all files for maximum compatibility
# (Modern browsers all support WebP. AVIF is great too).
# Let's provide a <picture> fallback for regular <img>, and change data-img and CSS to .webp directly.

def optimize_image(filepath):
    """
    Optimizes an image, generating a WebP and AVIF version.
    Returns the new paths and dimensions.
    """
    filename, ext = os.path.splitext(filepath)
    ext = ext.lower()
    
    if ext not in ['.jpg', '.jpeg', '.png']:
        return None
        
    try:
        with Image.open(filepath) as img:
            # Strip EXIF
            data = list(img.getdata())
            img_without_exif = Image.new(img.mode, img.size)
            img_without_exif.putdata(data)
            
            width, height = img_without_exif.size
            
            # Resize if too large (max 1200px width/height)
            max_dim = 1200
            if width > max_dim or height > max_dim:
                img_without_exif.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                width, height = img_without_exif.size
            
            # Convert RGBA to RGB if saving to a format that doesn't support alpha,
            # but WebP and AVIF both support alpha.
            
            webp_path = f"{filename}.webp"
            avif_path = f"{filename}.avif"
            
            # Save WebP
            img_without_exif.save(webp_path, format="WEBP", quality=80, method=6)
            
            # Save AVIF (pillow_heif)
            try:
                # pillow-heif uses 'AVIF'
                img_without_exif.save(avif_path, format="AVIF", quality=75)
            except Exception as e:
                print(f"AVIF save failed for {avif_path}: {e}")
                avif_path = None
                
            original_size = os.path.getsize(filepath)
            webp_size = os.path.getsize(webp_path) if os.path.exists(webp_path) else 0
            avif_size = os.path.getsize(avif_path) if avif_path and os.path.exists(avif_path) else 0
            
            return {
                'original': filepath,
                'webp': webp_path,
                'avif': avif_path,
                'width': width,
                'height': height,
                'orig_size': original_size,
                'webp_size': webp_size,
                'avif_size': avif_size
            }
    except Exception as e:
        print(f"Failed to process {filepath}: {e}")
        return None

results = []
for root, dirs, files in os.walk(ASSETS_DIR):
    for file in files:
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            full_path = os.path.join(root, file)
            res = optimize_image(full_path)
            if res:
                results.append(res)
                print(f"Optimized: {file} | Orig: {res['orig_size'] // 1024}KB -> WebP: {res['webp_size'] // 1024}KB")

# Update HTML files
for html_file in HTML_FILES:
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
        
    soup = BeautifulSoup(html, 'html.parser')
    modified = False
    
    # Process regular img tags
    for img in soup.find_all('img'):
        src = img.get('src')
        if not src: continue
        
        # Check if we have an optimized version
        matching_res = None
        for r in results:
            if src.replace('/', os.sep) == r['original']:
                matching_res = r
                break
            elif src == r['original'].replace(os.sep, '/'):
                matching_res = r
                break
                
        if matching_res:
            # We add width/height to prevent CLS
            if not img.get('width'):
                img['width'] = str(matching_res['width'])
            if not img.get('height'):
                img['height'] = str(matching_res['height'])
                
            # decoding async
            img['decoding'] = 'async'
            
            # Add lazy loading if not hero/logo
            classes = img.get('class', [])
            if 'logo' not in classes and 'main-plate-img' not in classes and not (html_file == 'index.html' and 'hero' in str(classes)):
                img['loading'] = 'lazy'
            else:
                img['fetchpriority'] = 'high'
            
            # Wrap in <picture> for avif/webp support if not already wrapped
            parent = img.parent
            if parent.name != 'picture':
                # Create picture tag
                picture = soup.new_tag('picture')
                
                # AVIF source
                if matching_res['avif']:
                    source_avif = soup.new_tag('source')
                    source_avif['srcset'] = matching_res['avif'].replace(os.sep, '/')
                    source_avif['type'] = 'image/avif'
                    picture.append(source_avif)
                    
                # WEBP source
                source_webp = soup.new_tag('source')
                source_webp['srcset'] = matching_res['webp'].replace(os.sep, '/')
                source_webp['type'] = 'image/webp'
                picture.append(source_webp)
                
                # Insert picture before img, then move img inside picture
                img.insert_before(picture)
                picture.append(img.extract())
                modified = True
    
    # Also fix data-img attributes in HTML (for JS dynamic swapping)
    for div in soup.find_all(attrs={"data-img": True}):
        data_img = div['data-img']
        for r in results:
            if data_img == r['original'].replace(os.sep, '/'):
                div['data-img'] = r['webp'].replace(os.sep, '/') # We fallback to webp for dynamic JS src to be safe
                modified = True
                break

    if modified:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
# Update CSS background images
for css_file in CSS_FILES:
    with open(css_file, 'r', encoding='utf-8') as f:
        css = f.read()
        
    orig_css = css
    for r in results:
        orig_path = r['original'].replace(os.sep, '/')
        webp_path = r['webp'].replace(os.sep, '/')
        # Replaces exact string match
        css = css.replace(orig_path, webp_path)
        
    if css != orig_css:
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(css)

# Output summary to a markdown artifact
md_content = "# Pre-Deployment Image Optimization Report\n\n"
md_content += "| Image | Original Size | WebP Size | Reduction |\n"
md_content += "|-------|--------------|-----------|-----------|\n"
total_orig = 0
total_webp = 0
for r in results:
    orig_kb = r['orig_size'] / 1024
    webp_kb = r['webp_size'] / 1024
    total_orig += r['orig_size']
    total_webp += r['webp_size']
    reduction = 100 - (webp_kb / orig_kb * 100) if orig_kb > 0 else 0
    md_content += f"| {r['original']} | {orig_kb:.1f} KB | {webp_kb:.1f} KB | {reduction:.1f}% |\n"

md_content += f"\n**Total Original Size**: {total_orig / 1024 / 1024:.2f} MB\n"
md_content += f"**Total Optimized Size**: {total_webp / 1024 / 1024:.2f} MB\n"
md_content += f"**Total Bandwidth Saved**: {(total_orig - total_webp) / 1024 / 1024:.2f} MB\n"

with open('optimization_report.md', 'w', encoding='utf-8') as f:
    f.write(md_content)

print("Optimization complete!")
