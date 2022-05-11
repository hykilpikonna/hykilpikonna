import json
import os
from pathlib import Path

import json5 as json5
import requests
import tweepy
from tweepy import User


def wget(url: str, file: Path):
    r = requests.get(url)
    file.write_bytes(r.content)
    return str(file).replace('\\', '/')


if __name__ == '__main__':
    token = os.environ['TWITTER_BEARER']
    auth = tweepy.OAuth2BearerHandler(token)
    api = tweepy.API(auth)

    gen_path = Path('content/generated/friends')
    (gen_path / 'img').mkdir(exist_ok=True, parents=True)

    # Loop through all friends
    friends = json5.loads(Path('content/friends.json5').read_text())
    for f in friends:
        if 'twitter' not in f:
            continue

        name = f['twitter']
        u: User = api.get_user(screen_name=name)

        f['banner'] = '/' + wget(u.profile_banner_url, gen_path / f'img/{name}-banner.jpg')
        f['avatar'] = '/' + wget(u.profile_image_url_https.replace('_normal', ''), gen_path / f'img/{name}-avatar.jpg')

        if 'link' not in f:
            f['link'] = f'https://twitter.com/{name}'

    (gen_path / 'friends.json').write_text(json.dumps(friends))

    print('Done')
