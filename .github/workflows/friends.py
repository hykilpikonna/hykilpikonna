import json
import os
from pathlib import Path

import json5 as json5
import requests
import tweepy
from tweepy import User


def wget(url: str, file: Path):
    if not file.is_file():
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
    friends: list[dict] = json5.loads(Path('content/friends.json5').read_text('utf-8'))
    for f in friends:
        name = f['name']
        avatar_path = gen_path / f'img/{name}-avatar.jpg'
        banner_path = gen_path / f'img/{name}-banner.jpg'

        # Already cached
        if avatar_path.is_file():
            f['avatar'] = str(avatar_path)
        if banner_path.is_file():
            f['banner'] = str(banner_path)
        if avatar_path.is_file() and banner_path.is_file():
            continue

        avatar, banner = f.get('avatar'), f.get('banner')

        # Get avatar url
        if 'twitter' in f:
            name = f['twitter']
            u: User = api.get_user(screen_name=name)

            if not avatar:
                avatar = u.profile_image_url_https.replace('_normal', '')
            if not banner and 'profile_banner_url' in u.__dict__:
                banner = u.profile_banner_url

        # Download avatar/banner locally
        if banner:
            f['banner'] = '/' + wget(banner, banner_path)
        if avatar:
            f['avatar'] = '/' + wget(avatar, avatar_path)

    (gen_path / 'friends.json').write_text(json.dumps(friends), 'utf-8')

    print('Done')
