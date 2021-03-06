"""Publish content from reddit to twitter."""

from scripts import *
import creds as creds
from random import choice
from pickle import dump
from pickle import load
from os import makedirs, path
from os import walk
from os import remove
from random import shuffle
from yaml import safe_load

# import config
with open('settings.yaml', 'r') as file:
    conf = safe_load(file)

# Create the file if it doesn't exist
# Load the list using pickle.
if path.exists('previous_posts.pickle'):
    with open('previous_posts.pickle', 'rb') as file:
        previous_posts = load(file)
else:
    previous_posts = []


# Create the folder if it doesn't exist
if not path.exists(conf['media_folder']):
    makedirs(conf['media_folder'])


submissions = []


# initialiation logging.
init_logger(conf['logger'])

# log on the apis.
# read the documentation for dict keys.
twitter = log_on_twitter_api(**creds.twitter)
reddit = log_on_reddit_api(**creds.reddit)


# pick and select a random subreddit.
random_subreddit = choice(list(conf['subreddits'].keys()))
subreddit = reddit.subreddit(random_subreddit)


# set up the body of the tweet
tweet_body = conf['subreddits'][random_subreddit]
if not tweet_body:
    tweet_body = conf['default_tweet']


# fetch the submissions we're going to look through.
# excludeds stickied, unsupported media
# and previously posted media.
for submission in subreddit.hot(limit=conf['fetch_limit']):
    if not submission.stickied and not submission.over_18:
        if submission.link_flair_text not in conf['excluded_flair']:
            if submission.id not in (previous_posts or previous_posts):
                media_type = get_media_type_for_reddit(submission)
                if media_type:
                    submission.type = media_type
                    submissions.append(submission)


tweet = False
shuffle(submissions)
for submission in submissions:

    # remove every file in media.
    for root, dirs, files in walk(conf['media_folder']):
        for file in files:
            remove(path.join(root, file))

    args = [
        twitter,
        submission,
        tweet_body,
        conf['media_folder']
    ]
    if submission.type == 'image':
        tweet = tweet_image(*args)

    elif submission.type == 'gallery':
        tweet = tweet_gallery(*args)

    elif submission.type == 'video':
        tweet = tweet_video(*args)

    previous_posts.append(submission.id)

    if tweet:
        break

# update the previous_post list.
# emptying it so the size stays constant.
# this is less to load in ram.
while len(previous_posts) > 400:
    previous_posts.pop()


# save the previous_posts list on the disk
with open('previous_posts.pickle', 'wb') as file:
    dump(previous_posts, file)
