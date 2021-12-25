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

        file = 'content/posts/' + b
        with open(file, 'r', encoding='utf-8') as f:
            md = f.read().strip()
            start = md.index('---\n')
            stop = md.index('---\n', start + 1)
            yml = md[start + 4:stop]
            meta = {**yaml.safe_load(yml), 'file': file}
            metas.append(meta)

    metas_path = Path('content/generated/metas.json')
    metas_path.parent.mkdir(exist_ok=True, parents=True)
    with open(metas_path, 'w', encoding='utf-8') as f:
        f.write('[\n    ' + ',\n    '.join(
            json.dumps(m, cls=EnhancedJSONEncoder, ensure_ascii=False) for m in metas) + '\n]')
