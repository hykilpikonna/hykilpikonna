import json
import os
from pathlib import Path

import requests
import tweepy
import yaml
from hypy_utils import ensure_dir, write
from tweepy import User


def wget(url: str, file: Path):
    if not file.is_file():
        r = requests.get(url)
        write(file, r.content)


if __name__ == '__main__':
    token = os.environ['TWITTER_BEARER']
    auth = tweepy.OAuth2BearerHandler(token)
    api = tweepy.API(auth)

    gen_path = ensure_dir('content/generated/friends')
    (gen_path / 'img').mkdir(exist_ok=True, parents=True)

    # Load friends
    friends: dict[str, dict] = yaml.safe_load(Path('content/friends.yaml').read_text())

    # Loop through all friends
    for name, f in friends.items():
        avatar_path = gen_path / f'img/{name}-avatar.jpg'
        banner_path = gen_path / f'img/{name}-banner.jpg'

        avatar, banner = f.get('avatar'), f.get('banner')

        # Get avatar url
        if 'twitter' in f:
            u: User = api.get_user(user_id=f['twitter'])
            print(f"{f['twitter']}'s username is {u.screen_name}")
            f['twitter'] = f"https://twitter.com/{u.screen_name}"

            if not avatar:
                avatar = u.profile_image_url_https.replace('_normal', '')
            if not banner and 'profile_banner_url' in u.__dict__:
                banner = u.profile_banner_url

        # Download avatar/banner locally if not exist
        if banner:
            wget(banner, banner_path)
        if avatar:
            wget(avatar, avatar_path)

        f['avatar'], f['banner'] = str(avatar_path), str(banner_path)

    # Map names
    friends: list[dict] = [{'name': name, **f} for name, f in friends.items()]

    write(gen_path / 'friends.json', json.dumps(friends))

    print('Done')
