import os
import re

# Small script to point html files to .min versions
# We'll also just remove unnecessary comments from CSS and JS as a basic minification step for now

folder = '.'
for file in os.listdir(folder):
    if file.endswith('.html'):
        path = os.path.join(folder, file)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update style.css
        # content = content.replace('href="style.css"', 'href="style.min.css"')
        
        # Adding loading="lazy" logic if missed
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
