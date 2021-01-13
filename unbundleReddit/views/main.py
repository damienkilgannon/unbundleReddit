import os
import requests
import logging

from lxml import etree
from random import randint
from math import pow

from flask import Blueprint, render_template, request, redirect

main = Blueprint('main', __name__, url_prefix='/')

logging.basicConfig(level=logging.INFO)


@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@main.route('/feeling-lucky', methods=['GET', 'POST'])
def feelingLucky():
    logging.info('Someone is feeling lucky:')
    category = request.form.get('category', 'all')
    logging.info('Searching in category: %s', category)
    subreddits = gather_subreddits(category=category)
    logging.info('Redirecting to subreddit: r/%s', subreddits[0])
    return redirect('https://www.reddit.com/r/{}'.format(subreddits[0]))

# @main.route('/searching', methods=['GET'])
# def searching():


def gather_subreddits(category='all', growth_rate_thres=0.4, curr_subs_thres=75000, number=1):
    growth_rate = 0
    curr_subs = 0
    results = []

    logging.info('Gathering subreddits')

    while len(results) <= number:
        try:
            subreddit_name = get_subreddit(category='all')
        except:
            subreddit_name = None

        if subreddit_name:
            try:
                growth_rate, curr_subs = check_subreddit_sixmonth_growth(subreddit_name)
            except:
                growth_rate, curr_subs = 0, 0

            if growth_rate > growth_rate_thres and curr_subs > curr_subs_thres:
                results.append(subreddit_name)

        if len(results) >= number:
            break

    return results

def get_subreddit(category='all'):
    rand = randint(10, 1000)
    page = rand//125
    row = rand%125

    url = "http://redditlist.com/{}?page={}".format(category, page)
    response = requests.get(url)

    tree = etree.HTML(response.text)
    subreddit_name = tree.xpath("//*[@id='listing-parent']/div[3]/div[{}]/span[3]/a/text()".format(row+1))[0]

    logging.info('Randomly selected: %s', subreddit_name)

    return subreddit_name

def check_subreddit_sixmonth_growth(subreddit_name):
    url = "https://frontpagemetrics.com/r/{}".format(subreddit_name)
    response = requests.get(url)
    tree = etree.HTML(response.text)

    curr_subs = tree.xpath("/html/body/div[2]/div/div/center/div[2]/div[2]/table[1]/thead/tr/td/table//text()")[5]
    curr_subs = int(curr_subs.replace(',', ''))

    abs_daily_subs_growth = tree.xpath("/html/body/div[2]/div/div/center/div[2]/div[2]/table[2]/tbody/tr[3]/td[2]/text()")[0]

    if 'N/A' in abs_daily_subs_growth:
        return 0, 0

    abs_daily_subs_growth = int(abs_daily_subs_growth.replace(',', ''))
    daily_subs_growth_rate = round(abs_daily_subs_growth/curr_subs, 3)

    prev_subs = round(curr_subs/pow(1.0+daily_subs_growth_rate, 180))

    abs_sixmonth_subs_growth = curr_subs - prev_subs
    sixmonth_subs_growth_rate = round(abs_sixmonth_subs_growth/prev_subs, 3)

    logging.info('Subreddit subscribers: %s', curr_subs)
    logging.info('Subreddit growth rate: %s', sixmonth_subs_growth_rate)

    return sixmonth_subs_growth_rate, curr_subs
