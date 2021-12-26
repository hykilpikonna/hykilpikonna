import json
import os
from datetime import datetime, date
from pathlib import Path

import yaml


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o: object) -> object:
        # Support encoding datetime
        if isinstance(o, (datetime, date)):
            return o.isoformat()

        return super().default(o)


if __name__ == '__main__':
    metas = []
    for b in os.listdir('content/posts'):
        if not b.endswith('.md'):
            continue

        # Read blog posts
        file = 'content/posts/' + b
        with open(file, 'r', encoding='utf-8') as f:
            md = f.read().strip()
            start = md.index('---\n')
            stop = md.index('---\n', start + 1)
            yml = md[start + 4:stop]
            meta = {**yaml.safe_load(yml), 'file': file}
            metas.append(meta)
            meta.setdefault('tags', [])

            # Parse date
            if 'date' not in meta:
                try:
                    meta['date'] = date(int(b[:4]), int(b[5:7]), int(b[8:10]))
                except:
                    pass

            # Convert image path
            if 'title_image' in meta and '/' not in meta['title_image']:
                meta['title_image'] = 'content/images/' + meta['title_image']

            content = md[stop + 4:].strip()
            meta['preview'] = '\n'.join(content.split('\n')[:5])
            meta['more_content'] = len(content.split('\n')) > 5

    metas.sort(key=lambda x: x['date'], reverse=True)

    metas_path = Path('content/generated/metas.json')
    metas_path.parent.mkdir(exist_ok=True, parents=True)
    with open(metas_path, 'w', encoding='utf-8') as f:
        f.write('[\n    ' + ',\n    '.join(
            json.dumps(m, cls=EnhancedJSONEncoder, ensure_ascii=False) for m in metas) + '\n]')
