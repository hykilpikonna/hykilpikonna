import json
import os
import re
from collections import Counter
from datetime import datetime, date
from pathlib import Path

import yaml


class Encoder(json.JSONEncoder):
    def default(self, o: object) -> object:
        # Support encoding datetime
        if isinstance(o, (datetime, date)):
            return o.isoformat()

        return super().default(o)


if __name__ == '__main__':
    posts = []

    # Loop through all blog posts
    for b in os.listdir('content/posts'):
        if not b.endswith('.md'):
            continue

        # Read blog posts
        file = 'content/posts/' + b
        with open(file, 'r', encoding='utf-8') as f:
            yml, md = re.split('---+\n', f.read().strip())[1:]
            post = {**yaml.safe_load(yml), 'file': file}
            posts.append(post)
            post.setdefault('tags', [])

            # Parse date
            if 'date' not in post:
                try:
                    post['date'] = datetime(int(b[:4]), int(b[5:7]), int(b[8:10]))
                except:
                    post['date'] = datetime.fromtimestamp(os.path.getmtime(file))

            # Convert image path
            if 'title_image' in post and '/' not in post['title_image']:
                post['title_image'] = 'content/images/' + post['title_image']

            post['content'] = md.strip()

    posts.sort(key=lambda x: x['date'], reverse=True)

    # Count tags and categories
    tags = Counter([t for p in posts for t in p['tags']])
    cats = Counter([p['category'] for p in posts if 'category' in p])
    tags, cats = [[(k, c[k]) for k in c] for c in [tags, cats]]

    # Convert to json
    json_text = '{\n' \
                f'  "tags": {json.dumps(tags, ensure_ascii=False)},\n' \
                f'  "categories": {json.dumps(cats, ensure_ascii=False)},\n' \
                '  "posts": [\n    ' \
                + ',\n    '.join(json.dumps(p, cls=Encoder, ensure_ascii=False) for p in posts) + '\n' \
                '  ]\n' \
                '}'

    mp = Path('content/generated/metas.json')
    mp.parent.mkdir(exist_ok=True, parents=True)
    mp.write_text(json_text, 'utf-8')
