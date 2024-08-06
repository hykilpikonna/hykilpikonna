import json
import os
import re
from collections import Counter
from datetime import datetime, date
from pathlib import Path

import yaml
import urllib.parse


class Encoder(json.JSONEncoder):
    def default(self, o: object) -> object:
        # Support encoding datetime
        if isinstance(o, (datetime, date)):
            return o.isoformat()

        return super().default(o)


if __name__ == '__main__':
    posts = []
    basedir = Path('content/posts')
    src = 'https://profile-content.hydev.org'

    # Loop through all blog posts
    for file in basedir.glob('*.md'):
        stem = file.stem
        yml, md = re.split('---+\n', file.read_text('utf-8').strip())[1:]
        
        post = {'id': 0, **yaml.safe_load(yml), 'file': str(file)}
        posts.append(post)
        post.setdefault('tags', [])

        # Parse date
        if 'date' not in post:
            try:
                post['date'] = datetime(int(stem[:4]), int(stem[5:7]), int(stem[8:10]))
            except:
                post['date'] = datetime.fromtimestamp(os.path.getmtime(file))
                
        def convert_img_path(s: str):
            if s.startswith('http'):
                return s
            return f'{src}/content/posts/Assets/{urllib.parse.quote(stem)}/{urllib.parse.quote(s)}'

        # Convert image path
        if 'title_image' in post:
            post['title_image'] = convert_img_path(post['title_image'])

        # Generate url-name
        if 'url_name' not in post:
            post['url_name'] = stem.replace(' ', '-')
        
        post['content'] = md.strip()

        # Process images
        for img in re.findall(r'!\[\[(.*)\]\]', md):
            if '|' in img:
                img, cap = img.split('|', 1)
                post['content'] = post['content'].replace(f'![[{img}|{cap}]]', f'<figure><img src="{convert_img_path(img)}" /><caption>{cap}</caption></figure>')
            else:
                post['content'] = post['content'].replace(f'![[{img}]]', f'<img src="{convert_img_path(img)}" />')

    posts.sort(key=lambda x: x['date'], reverse=True)

    # Give every post an id based on index
    for i, p in enumerate(posts):
        p['id'] = len(posts) - i

    # Count tags and categories
    tags = Counter([t for p in posts for t in p['tags']])
    cats = Counter([p['category'] for p in posts if 'category' in p])
    tags, cats = [[(k, c[k]) for k in c] for c in [tags, cats]]

    # Pins
    pins = [p for p in posts if 'pinned' in p]
    pins.sort(key=lambda x: x['pinned'])
    pins = [p['id'] for p in pins]

    # Convert to json
    json_text = '{\n' \
                f'  "tags": {json.dumps(tags, ensure_ascii=False)},\n' \
                f'  "categories": {json.dumps(cats, ensure_ascii=False)},\n' \
                f'  "pins": {json.dumps(pins, ensure_ascii=False)},\n' \
                '  "posts": [\n    ' \
                + ',\n    '.join(json.dumps(p, cls=Encoder, ensure_ascii=False) for p in posts) + '\n' \
                '  ]\n' \
                '}'

    mp = Path('content/generated/metas.json')
    mp.parent.mkdir(exist_ok=True, parents=True)
    mp.write_text(json_text, 'utf-8')
