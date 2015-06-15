Yelp Dataset Challenge
======================

Overview
========

The dataset is a single gzip-compressed file, composed of one
json-object per line. Every object contains a 'type' field, which tells
you whether it is a business, a user, or a review.

--------------

Business Objects
----------------

Business objects contain basic information about local businesses. The
'business\_id' field can be used with the Yelp API to fetch even more
information for visualizations, but note that you'll still need to
comply with the API TOS. The fields are as follows:

.. code-block:: json

    {
      'type': 'business',
      'business_id': (a unique identifier for this business),
      'name': (the full business name),
      'neighborhoods': (a list of neighborhood names, might be empty),
      'full_address': (localized address),
      'city': (city),
      'state': (state),
      'latitude': (latitude),
      'longitude': (longitude),
      'stars': (star rating, rounded to half-stars),
      'review_count': (review count),
      'photo_url': (photo url),
      'categories': [(localized category names)]
      'open': (is the business still open for business?),
      'schools': (nearby universities),
      'url': (yelp url)
    }

--------------

Review Objects
--------------

Review objects contain the review text, the star rating, and information
on votes Yelp users have cast on the review. Use user\_id to associate
this review with others by the same user. Use business\_id to associate
this review with others of the same business.

.. code-block:: json

    {
      'type': 'review',
      'business_id': (the identifier of the reviewed business),
      'user_id': (the identifier of the authoring user),
      'stars': (star rating, integer 1-5),
      'text': (review text),
      'date': (date, formatted like '2011-04-19'),
      'votes': {
        'useful': (count of useful votes),
        'funny': (count of funny votes),
        'cool': (count of cool votes)
      }
    }

--------------

User Objects
------------

User objects contain aggregate information about a single user across
all of Yelp (including businesses and reviews not in this dataset).

.. code-block:: json

    {
      'type': 'user',
      'user_id': (unique user identifier),
      'name': (first name, last initial, like 'Matt J.'),
      'review_count': (review count),
      'average_stars': (floating point average, like 4.31),
      'votes': {
        'useful': (count of useful votes across all reviews),
        'funny': (count of funny votes across all reviews),
        'cool': (count of cool votes across all reviews)
      }
    }

|a|


The task is to predict the 'star rating' for a restaurant for a given
user.

The dataset comprises three tables that cover

-  11,537 businesses
-  8,282 check-ins
-  43,873 users
-  229,907 reviews.

Link to `Official Yelp
Website <http://www.yelp.com/dataset_challenge>`__

.. code-block:: python

    import os
    import sys
    import operator
    import functools
    import itertools
    import boto
    import warnings
    import json
    import pandas as pd

    import matplotlib.pyplot as plt
    import graphlab as gl

    from textblob import TextBlob
    from os.path import join as jp

    try:
        from configparser import ConfigParser
    except ImportError:
        from ConfigParser import ConfigParser

    gl.canvas.set_target('ipynb')

Technical Challenges
====================

1. Big Data... somewhat

   -  More like *Medium Data*

2. Highly Networked Data Structures
3. User Sentiment Analysis

Proposed Solutions
==================

1. Streaming and Lazy Evaluation. Also utilize compression.
2. Use Graph Algorithms and parsing strategies
3. Magic!??

S3 Remote File Streaming
========================

.. code-block:: python

    from IPython.display import *

.. code-block:: python

    def aws_config(cfg):
        """
        Queries local environment for aws configurations
        """
        home, user = os.getenv('HOME'), os.getlogin()
        valid_user = user in cfg.sections()

        return user if valid_user else cfg.sections()[0]

    def s3_signin(**auth):
        """
        Convenience function for validating keys  and providing
        access to bucket shares.

        Returns S3Object
        """
        token_ids  = 'aws_access_key_id', 'aws_secret_access_key'

        cfg = ConfigParser()
        cfg.read(jp(os.getenv('HOME'), '.aws', 'credentials'))

        account    = itertools.repeat(aws_config(cfg), 2)
        valid_auth = all(auth.has_key(i) for i in token_ids)
        token      = zip(account, token_ids) if not valid_auth else [token_ids]
        store      = cfg if not auth else auth

        user_id    = dict(zip(token_ids, map(lambda t: store.get(*t), token)))

        if not all(user_id.values()):
            raise ValueError('No valid authorization found')

        return boto.connect_s3(**user_id)

Key and Configuration Management
================================

.. code-block:: python

    s3 = s3_signin()

    gl.aws.set_credentials(s3.gs_access_key_id, s3.gs_secret_access_key)

Remote JSON to DataFrame
========================

.. code-block:: python

    def remote_json_loader(filename):
        """
        Load JSON from a remote data store.
        """
        sf = gl.SFrame.read_csv(filename, delimiter='\n', header=False)
        return sf.unpack('X1', column_name_prefix='')

    def gen_data_url(s3, bucket , dataset):
        s3_dir   = s3.get_bucket(bucket)
        s3_urls  = [
            '/'.join(['s3:/', s3_dir.name, d.name])
                    for d in s3_dir.list(dataset)
        ]
        for url in s3_urls:
            yield url

    def flatten(sf):
        """
        Flatten nested SFrame DataStructure.
        """
        dtypes = dict(zip(sf.column_names(), gl.SFrame.dtype(sf)))
        cols = [k for k,v in dtypes.items() if v in [dict, list]]
        return sf[cols]

Holy Crap Evil Unicorn Power
============================

.. code-block:: python

    # Data On the Internet!
    aws   = 'https://s3-us-west-1.amazonaws.com/ds3-machine-learning/yelp/{file}.csv'
    links = (aws.format(file=f) for f in ['business', 'user', 'review'])

    business, user, review = map(gl.SFrame.read_csv, links)


.. parsed-literal::

    PROGRESS: Downloading https://s3-us-west-1.amazonaws.com/ds3-machine-learning/yelp/business.csv to /var/tmp/graphlab-jjangsangy/3456/000000.csv
    PROGRESS: Finished parsing file https://s3-us-west-1.amazonaws.com/ds3-machine-learning/yelp/business.csv
    PROGRESS: Parsing completed. Parsed 100 lines in 0.114366 secs.
    ------------------------------------------------------
    Inferred types from first line of file as
    column_type_hints=[str,list,str,str,float,float,str,int,int,float,str,str]
    If parsing fails due to incorrect types, you can correct
    the inferred type list above and pass it to read_csv in
    the column_type_hints argument
    ------------------------------------------------------
    PROGRESS: Finished parsing file https://s3-us-west-1.amazonaws.com/ds3-machine-learning/yelp/business.csv
    PROGRESS: Parsing completed. Parsed 11537 lines in 0.115099 secs.
    PROGRESS: Downloading https://s3-us-west-1.amazonaws.com/ds3-machine-learning/yelp/user.csv to /var/tmp/graphlab-jjangsangy/3456/000001.csv
    PROGRESS: Finished parsing file https://s3-us-west-1.amazonaws.com/ds3-machine-learning/yelp/user.csv
    PROGRESS: Parsing completed. Parsed 100 lines in 0.085561 secs.
    ------------------------------------------------------
    Inferred types from first line of file as
    column_type_hints=[float,str,int,str,str,int,int,int]
    If parsing fails due to incorrect types, you can correct
    the inferred type list above and pass it to read_csv in
    the column_type_hints argument
    ------------------------------------------------------
    PROGRESS: Finished parsing file https://s3-us-west-1.amazonaws.com/ds3-machine-learning/yelp/user.csv
    PROGRESS: Parsing completed. Parsed 43873 lines in 0.114571 secs.
    PROGRESS: Downloading https://s3-us-west-1.amazonaws.com/ds3-machine-learning/yelp/review.csv to /var/tmp/graphlab-jjangsangy/3456/000002.csv
    PROGRESS: Finished parsing file https://s3-us-west-1.amazonaws.com/ds3-machine-learning/yelp/review.csv
    PROGRESS: Parsing completed. Parsed 100 lines in 1.67836 secs.
    ------------------------------------------------------
    Inferred types from first line of file as
    column_type_hints=[str,str,str,int,str,str,str,dict,int,int,int]
    If parsing fails due to incorrect types, you can correct
    the inferred type list above and pass it to read_csv in
    the column_type_hints argument
    ------------------------------------------------------
    PROGRESS: Read 61212 lines. Lines per second: 29778.6
    PROGRESS: Finished parsing file https://s3-us-west-1.amazonaws.com/ds3-machine-learning/yelp/review.csv
    PROGRESS: Parsing completed. Parsed 229907 lines in 5.48188 secs.


.. figure:: http://i.imgur.com/xsDUgFE.png
   :alt:

Data Compression (Please..)
===========================

Structures into a more compact data structure.

We join together based on user and business keys and the old objects get
garbage collected

.. code-block:: python

    review_business = review.join(business, how='inner', on='business_id')
    review_business = review_business.rename({'stars.1': 'business_avg_stars',
                                              'type.1' : 'business_type',
                                              'review_count': 'business_review_count'})

.. code-block:: python

    user_review = review_business.join(user, how='inner', on='user_id')
    user_review = user_review.rename({'name.1': 'user_name',
                                      'type.1': 'user_type',
                                      'average_stars': 'user_avg_stars',
                                      'review_count' : 'user_review_count'})

.. code-block:: python

    yelp_reviews = user_review.join(review_business, on='review_id')

Split Testing and Training Set
==============================

Data Science stuff

.. code-block:: python

    train_set, test_set = yelp_reviews.random_split(0.8, seed=1)

.. code-block:: python

    display(train_set.head(3))



.. raw:: html

    <div style="max-height:1000px;max-width:1500px;overflow:auto;"><table frame="box" rules="cols">
        <tr>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">business_id</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">date</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">review_id</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">stars</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">text</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">type</th>
        </tr>
        <tr>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">9yKzy9PApeiPPOUJEtnvkg</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">2011-01-26</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">fWKvX83p0-ka4JS3dc6E5A</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">5</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">My wife took me here on<br>my birthday for break ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">review</td>
        </tr>
        <tr>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">ZRJwVLyzEJq1VAihDhYiow</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">2011-07-27</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">IjZ33sJrzXqU-0X6U8NwyA</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">5</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">I have no idea why some<br>people give bad reviews ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">review</td>
        </tr>
        <tr>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">6oRAC4uyJCsJl1X0WZpVSA</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">2012-06-14</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">IESLBzqUCLdSzSqm0eCSxQ</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">4</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">love the gyro plate. Rice<br>is so good and I also ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">review</td>
        </tr>
    </table>
    <table frame="box" rules="cols">
        <tr>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">user_id</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">votes</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">year</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">month</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">day</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">categories</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">city</th>
        </tr>
        <tr>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">rLtl8ZkDX5vH5nAx9C3q5Q</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">{'funny': 0, 'useful': 5,<br>'cool': 2} ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">2011</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">1</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">26</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">[Breakfast &amp; Brunch,<br>Restaurants] ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">Phoenix</td>
        </tr>
        <tr>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">0a2KyEL0d3Yb1V6aivbIuQ</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">{'funny': 0, 'useful': 0,<br>'cool': 0} ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">2011</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">7</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">27</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">[Italian, Pizza,<br>Restaurants] ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">Phoenix</td>
        </tr>
        <tr>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">0hT2KtfLiobPvh6cDC8JQg</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">{'funny': 0, 'useful': 1,<br>'cool': 0} ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">2012</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">6</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">14</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">[Middle Eastern,<br>Restaurants] ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">Tempe</td>
        </tr>
    </table>
    <table frame="box" rules="cols">
        <tr>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">full_address</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">latitude</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">longitude</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">name</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">open</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">business_review_count</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">business_avg_stars</th>
        </tr>
        <tr>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">6106 S 32nd St\nPhoenix,<br>AZ 85042 ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">33.3908</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">-112.013</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">Morning Glory Cafe</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">1</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">116</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">4.0</td>
        </tr>
        <tr>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">4848 E Chandler<br>Blvd\nPhoenix, AZ 85044 ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">33.3056</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">-111.979</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">Spinato's Pizzeria</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">1</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">102</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">4.0</td>
        </tr>
        <tr>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">1513 E  Apache<br>Blvd\nTempe, AZ 85281 ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">33.4143</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">-111.913</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">Haji-Baba</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">1</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">265</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">4.5</td>
        </tr>
    </table>
    <table frame="box" rules="cols">
        <tr>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">state</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">business_type</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">user_avg_stars</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">user_name</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">user_review_count</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">user_type</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">votes_funny</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">votes_cool</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">votes_useful</th>
        </tr>
        <tr>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">AZ</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">business</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">3.72</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">Jason</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">376</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">user</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">331</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">322</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">1034</td>
        </tr>
        <tr>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">AZ</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">business</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">5.0</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">Paul</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">2</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">user</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">2</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">0</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">0</td>
        </tr>
        <tr>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">AZ</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">business</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">4.33</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">Nicole</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">3</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">user</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">0</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">0</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">3</td>
        </tr>
    </table>
    <table frame="box" rules="cols">
        <tr>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">business_id.1</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">date.1</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">stars.1</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">text.1</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">type.1</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">user_id.1</th>
        </tr>
        <tr>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">9yKzy9PApeiPPOUJEtnvkg</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">2011-01-26</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">5</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">My wife took me here on<br>my birthday for break ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">review</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">rLtl8ZkDX5vH5nAx9C3q5Q</td>
        </tr>
        <tr>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">ZRJwVLyzEJq1VAihDhYiow</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">2011-07-27</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">5</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">I have no idea why some<br>people give bad reviews ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">review</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">0a2KyEL0d3Yb1V6aivbIuQ</td>
        </tr>
        <tr>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">6oRAC4uyJCsJl1X0WZpVSA</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">2012-06-14</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">4</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">love the gyro plate. Rice<br>is so good and I also ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">review</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">0hT2KtfLiobPvh6cDC8JQg</td>
        </tr>
    </table>
    <table frame="box" rules="cols">
        <tr>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">votes.1</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">year.1</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">month.1</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">day.1</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">categories.1</th>
            <th style="padding-left: 1em; padding-right: 1em; text-align: center">...</th>
        </tr>
        <tr>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">{'funny': 0, 'useful': 5,<br>'cool': 2} ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">2011</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">1</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">26</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">[Breakfast &amp; Brunch,<br>Restaurants] ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">...</td>
        </tr>
        <tr>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">{'funny': 0, 'useful': 0,<br>'cool': 0} ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">2011</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">7</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">27</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">[Italian, Pizza,<br>Restaurants] ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">...</td>
        </tr>
        <tr>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">{'funny': 0, 'useful': 1,<br>'cool': 0} ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">2012</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">6</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">14</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">[Middle Eastern,<br>Restaurants] ...</td>
            <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">...</td>
        </tr>
    </table>
    [3 rows x 52 columns]<br/>
    </div>


.. code-block:: python

    display_javascript(train_set['city'].show())




Train Regression Model!
=======================

--------------

.. code-block:: python

    model = gl.linear_regression.create(train_set, target='stars',
                                        features = ['user_avg_stars','business_avg_stars',
                                                    'user_review_count', 'business_review_count',
                                                    'city'])


.. parsed-literal::

    PROGRESS: Creating a validation set from 5 percent of training data. This may take a while.
              You can set ``validation_set=None`` to disable validation tracking.

    PROGRESS: Linear regression:
    PROGRESS: --------------------------------------------------------
    PROGRESS: Number of examples          : 164052
    PROGRESS: Number of features          : 5
    PROGRESS: Number of unpacked features : 5
    PROGRESS: Number of coefficients    : 65
    PROGRESS: Starting Newton Method
    PROGRESS: --------------------------------------------------------
    PROGRESS: +-----------+----------+--------------+--------------------+----------------------+---------------+-----------------+
    PROGRESS: | Iteration | Passes   | Elapsed Time | Training-max_error | Validation-max_error | Training-rmse | Validation-rmse |
    PROGRESS: +-----------+----------+--------------+--------------------+----------------------+---------------+-----------------+
    PROGRESS: | 1         | 2        | 0.203407     | 3.971958           | 3.564674             | 0.970918      | 0.965084        |
    PROGRESS: +-----------+----------+--------------+--------------------+----------------------+---------------+-----------------+


.. code-block:: python

    model.evaluate(test_set)




.. parsed-literal::

    {'max_error': 4.016124743972821, 'rmse': 0.9706849263734884}



.. code-block:: python

    model.summary()


.. parsed-literal::

    Class                         : LinearRegression

    Schema
    ------
    Number of coefficients        : 65
    Number of examples            : 205139
    Number of feature columns     : 5
    Number of unpacked features   : 5

    Hyperparameters
    ---------------
    L1 penalty                    : 0.0
    L2 penalty                    : 0.01

    Training Summary
    ----------------
    Solver                        : auto
    Solver iterations             : 1
    Solver status                 : SUCCESS: Optimal solution found.
    Training time (sec)           : 0.3522

    Settings
    --------
    Residual sum of squares       : 193305.2713
    Training RMSE                 : 0.9707

    Highest Positive Coefficients
    -----------------------------
    city[Sun City Anthem]         : 1.5828
    user_avg_stars                : 0.8133
    business_avg_stars            : 0.7777
    city[North Pinal]             : 0.3682
    city[Grand Junction]          : 0.3246

    Lowest Negative Coefficients
    ----------------------------
    (intercept)                   : -2.2332
    city[Saguaro Lake]            : -0.2227
    city[Florence]                : -0.1593
    city[Wittmann]                : -0.1486
    city[Youngtown]               : -0.1122



More Training!!
===============

Well crap, just keep on the iterating!

Iterate 10 More Times!
======================

.. code-block:: python

    model = gl.linear_regression.create(yelp_reviews, target='stars',
                                        features = ['user_id','business_id',
                                                    'user_avg_stars','business_avg_stars'],
                                                    max_iterations=10)


.. parsed-literal::

    PROGRESS: Creating a validation set from 5 percent of training data. This may take a while.
              You can set ``validation_set=None`` to disable validation tracking.

    PROGRESS: Linear regression:
    PROGRESS: --------------------------------------------------------
    PROGRESS: Number of examples          : 205280
    PROGRESS: Number of features          : 4
    PROGRESS: Number of unpacked features : 4
    PROGRESS: Number of coefficients    : 54308
    PROGRESS: Starting L-BFGS
    PROGRESS: --------------------------------------------------------
    PROGRESS: +-----------+----------+-----------+--------------+--------------------+----------------------+---------------+-----------------+
    PROGRESS: | Iteration | Passes   | Step size | Elapsed Time | Training-max_error | Validation-max_error | Training-rmse | Validation-rmse |
    PROGRESS: +-----------+----------+-----------+--------------+--------------------+----------------------+---------------+-----------------+
    PROGRESS: | 1         | 6        | 0.000000  | 0.732986     | 3.364958           | 3.425305             | 1.006274      | 1.109129        |
    PROGRESS: | 2         | 9        | 5.000000  | 1.190700     | 4.038661           | 6.434633             | 0.875567      | 1.182896        |
    PROGRESS: | 3         | 10       | 5.000000  | 1.397855     | 8.005615           | 7.137092             | 1.051506      | 1.313125        |
    PROGRESS: | 4         | 12       | 1.000000  | 1.759148     | 3.815589           | 5.885623             | 0.857827      | 1.184018        |
    PROGRESS: | 5         | 13       | 1.000000  | 2.004362     | 3.875218           | 5.915696             | 0.856124      | 1.180297        |
    PROGRESS: | 6         | 14       | 1.000000  | 2.238819     | 3.835793           | 5.914847             | 0.854844      | 1.181280        |
    PROGRESS: | 10        | 18       | 1.000000  | 3.205266     | 3.896264           | 5.995503             | 0.852408      | 1.195639        |
    PROGRESS: +-----------+----------+-----------+--------------+--------------------+----------------------+---------------+-----------------+


Or even 100X!
=============

.. figure:: http://img3.wikia.nocookie.net/__cb20120228151221/dragonball/images/thumb/3/3e/Goku_Charges_Kaioken_Times_3.JPG/1023px-Goku_Charges_Kaioken_Times_3.JPG
   :alt:

.. code-block:: python

    model = gl.linear_regression.create(yelp_reviews, target='stars',
                                        features = ['user_id','business_id',
                                                    'user_avg_stars','business_avg_stars'],
                                                    max_iterations=100)


.. parsed-literal::

    PROGRESS: Creating a validation set from 5 percent of training data. This may take a while.
              You can set ``validation_set=None`` to disable validation tracking.

    PROGRESS: Linear regression:
    PROGRESS: --------------------------------------------------------
    PROGRESS: Number of examples          : 205059
    PROGRESS: Number of features          : 4
    PROGRESS: Number of unpacked features : 4
    PROGRESS: Number of coefficients    : 54334
    PROGRESS: Starting L-BFGS
    PROGRESS: --------------------------------------------------------
    PROGRESS: +-----------+----------+-----------+--------------+--------------------+----------------------+---------------+-----------------+
    PROGRESS: | Iteration | Passes   | Step size | Elapsed Time | Training-max_error | Validation-max_error | Training-rmse | Validation-rmse |
    PROGRESS: +-----------+----------+-----------+--------------+--------------------+----------------------+---------------+-----------------+
    PROGRESS: | 1         | 6        | 0.000000  | 0.879003     | 3.374304           | 3.546180             | 1.006509      | 1.096167        |
    PROGRESS: | 2         | 9        | 5.000000  | 1.371499     | 3.973070           | 4.880738             | 0.875498      | 1.187452        |
    PROGRESS: | 3         | 10       | 5.000000  | 1.689919     | 6.860610           | 6.562078             | 1.051744      | 1.314555        |
    PROGRESS: | 4         | 12       | 1.000000  | 2.093925     | 3.791061           | 4.934615             | 0.857630      | 1.187303        |
    PROGRESS: | 5         | 13       | 1.000000  | 2.322499     | 3.897381           | 4.955225             | 0.855922      | 1.181546        |
    PROGRESS: | 6         | 14       | 1.000000  | 2.512237     | 3.853703           | 4.917000             | 0.854624      | 1.183400        |
    PROGRESS: | 10        | 18       | 1.000000  | 3.425410     | 3.938762           | 5.014433             | 0.852165      | 1.198493        |
    PROGRESS: | 11        | 19       | 1.000000  | 3.628849     | 3.932378           | 5.035921             | 0.852049      | 1.199107        |
    PROGRESS: | 15        | 23       | 1.000000  | 4.415253     | 3.919294           | 5.395360             | 0.851920      | 1.201375        |
    PROGRESS: | 20        | 28       | 1.000000  | 5.529039     | 3.918947           | 6.530650             | 0.851892      | 1.201231        |
    PROGRESS: | 25        | 33       | 1.000000  | 6.475729     | 3.919687           | 7.317974             | 0.851865      | 1.200497        |
    PROGRESS: | 30        | 38       | 1.000000  | 7.550670     | 3.934781           | 5.465904             | 0.851702      | 1.186699        |
    PROGRESS: | 35        | 43       | 1.000000  | 8.518818     | 3.912145           | 5.022651             | 0.851493      | 1.181603        |
    PROGRESS: | 40        | 48       | 1.000000  | 9.455839     | 3.920923           | 6.399283             | 0.851450      | 1.183357        |
    PROGRESS: | 45        | 53       | 1.000000  | 10.436233    | 3.919441           | 6.639106             | 0.851444      | 1.182982        |
    PROGRESS: | 50        | 58       | 1.000000  | 11.404371    | 3.919144           | 6.635648             | 0.851442      | 1.183203        |
    PROGRESS: | 51        | 59       | 1.000000  | 11.582491    | 3.918729           | 6.644113             | 0.851441      | 1.183239        |
    PROGRESS: | 55        | 63       | 1.000000  | 12.319183    | 3.923829           | 6.339387             | 0.851426      | 1.181220        |
    PROGRESS: | 60        | 68       | 1.000000  | 13.772160    | 3.917975           | 6.501958             | 0.851390      | 1.179843        |
    PROGRESS: | 65        | 73       | 1.000000  | 15.090546    | 3.918622           | 6.894069             | 0.851343      | 1.178876        |
    PROGRESS: | 70        | 78       | 1.000000  | 16.286698    | 3.918026           | 6.679894             | 0.851333      | 1.178368        |
    PROGRESS: | 75        | 83       | 1.000000  | 17.448901    | 3.918813           | 6.477494             | 0.851331      | 1.178350        |
    PROGRESS: | 80        | 88       | 1.000000  | 18.420837    | 3.919651           | 6.442720             | 0.851331      | 1.178452        |
    PROGRESS: | 85        | 93       | 1.000000  | 19.371725    | 3.919406           | 6.442897             | 0.851331      | 1.178563        |
    PROGRESS: | 90        | 98       | 1.000000  | 20.350318    | 3.919393           | 6.465814             | 0.851331      | 1.178605        |
    PROGRESS: | 95        | 103      | 1.000000  | 21.314862    | 3.919420           | 6.482812             | 0.851331      | 1.178628        |
    PROGRESS: | 100       | 108      | 1.000000  | 22.254052    | 3.919421           | 6.482513             | 0.851331      | 1.178636        |
    PROGRESS: +-----------+----------+-----------+--------------+--------------------+----------------------+---------------+-----------------+


Dictionary and List Features
============================

.. code-block:: python

    train_set['votes'].head(3)




.. parsed-literal::

    dtype: dict
    Rows: 3
    [{'funny': 0, 'useful': 5, 'cool': 2}, {'funny': 0, 'useful': 0, 'cool': 0}, {'funny': 0, 'useful': 1, 'cool': 0}]



.. code-block:: python

    tags_to_dict = lambda tags: dict(zip(tags, [1 for tag in tags]))

Using Review Category Tags
==========================

.. code-block:: python

    train_set['categories_dict'] = train_set.apply(lambda row: tags_to_dict(row['categories']))
    train_set['categories_dict'].head(5)




.. parsed-literal::

    dtype: dict
    Rows: 5
    [{'Breakfast & Brunch': 1, 'Restaurants': 1}, {'Restaurants': 1, 'Pizza': 1, 'Italian': 1}, {'Middle Eastern': 1, 'Restaurants': 1}, {'Dog Parks': 1, 'Parks': 1, 'Active Life': 1}, {'Tires': 1, 'Automotive': 1}]



.. code-block:: python

    model = gl.linear_regression.create(train_set, target='stars',
                                        features = ['user_id','business_id', 'categories_dict',
                                                    'user_avg_stars','votes', 'business_avg_stars'])


.. parsed-literal::

    PROGRESS: Creating a validation set from 5 percent of training data. This may take a while.
              You can set ``validation_set=None`` to disable validation tracking.

    PROGRESS: Linear regression:
    PROGRESS: --------------------------------------------------------
    PROGRESS: Number of examples          : 163915
    PROGRESS: Number of features          : 6
    PROGRESS: Number of unpacked features : 515
    PROGRESS: Number of coefficients    : 50076
    PROGRESS: Starting L-BFGS
    PROGRESS: --------------------------------------------------------
    PROGRESS: +-----------+----------+-----------+--------------+--------------------+----------------------+---------------+-----------------+
    PROGRESS: | Iteration | Passes   | Step size | Elapsed Time | Training-max_error | Validation-max_error | Training-rmse | Validation-rmse |
    PROGRESS: +-----------+----------+-----------+--------------+--------------------+----------------------+---------------+-----------------+
    PROGRESS: | 1         | 6        | 0.000000  | 1.016222     | 19.169677          | 6.678086             | 1.289192      | 1.344118        |
    PROGRESS: | 2         | 9        | 5.000000  | 1.608496     | 13.975451          | 5.198082             | 1.031652      | 1.224624        |
    PROGRESS: | 3         | 10       | 5.000000  | 1.876383     | 29.764258          | 10.649397            | 1.997984      | 2.095041        |
    PROGRESS: | 4         | 12       | 1.000000  | 2.334323     | 3.852072           | 5.231593             | 0.858294      | 1.150716        |
    PROGRESS: | 5         | 13       | 1.000000  | 2.628560     | 3.947246           | 5.334254             | 0.849495      | 1.150773        |
    PROGRESS: | 6         | 14       | 1.000000  | 2.911206     | 3.914202           | 5.614301             | 0.838725      | 1.161301        |
    PROGRESS: | 10        | 18       | 1.000000  | 3.995491     | 3.857460           | 6.684582             | 0.818123      | 1.187864        |
    PROGRESS: +-----------+----------+-----------+--------------+--------------------+----------------------+---------------+-----------------+


Text Data: Using Raw Review Data
================================

.. code-block:: python

    train_set['text'].head(1)




.. parsed-literal::

    dtype: str
    Rows: 1
    ['My wife took me here on my birthday for breakfast and it was excellent.  The weather was perfect which made sitting outside overlooking their grounds an absolute pleasure.  Our waitress was excellent and our food arrived quickly on the semi-busy Saturday morning.  It looked like the place fills up pretty quickly so the earlier you get here the better.

    Do yourself a favor and get their Bloody Mary.  It was phenomenal and simply the best I've ever had.  I'm pretty sure they only use ingredients from their garden and blend them fresh when you order it.  It was amazing.

    While EVERYTHING on the menu looks excellent, I had the white truffle scrambled eggs vegetable skillet and it was tasty and delicious.  It came with 2 pieces of their griddled bread with was amazing and it absolutely made the meal complete.  It was the best "toast" I've ever had.

    Anyway, I can't wait to go back!']



.. code-block:: python

    gen_blobs = (TextBlob(i) for i in train_set['text'])
    sample    = itertools.islice(gen_blobs, 0, 10)

    for blob in sample:
        print("Calculated Polarity and Subjectivity")
        print("====================================")
        print(blob.sentiment.polarity, blob.sentiment.subjectivity, sep='\n', end='\n\n')
        print(blob)
        print("----------\n")


.. parsed-literal::

    Calculated Polarity and Subjectivity
    ====================================
    0.402469135802
    0.65911228689

    My wife took me here on my birthday for breakfast and it was excellent.  The weather was perfect which made sitting outside overlooking their grounds an absolute pleasure.  Our waitress was excellent and our food arrived quickly on the semi-busy Saturday morning.  It looked like the place fills up pretty quickly so the earlier you get here the better.

    Do yourself a favor and get their Bloody Mary.  It was phenomenal and simply the best I've ever had.  I'm pretty sure they only use ingredients from their garden and blend them fresh when you order it.  It was amazing.

    While EVERYTHING on the menu looks excellent, I had the white truffle scrambled eggs vegetable skillet and it was tasty and delicious.  It came with 2 pieces of their griddled bread with was amazing and it absolutely made the meal complete.  It was the best "toast" I've ever had.

    Anyway, I can't wait to go back!
    ----------

    Calculated Polarity and Subjectivity
    ====================================
    0.229772727273
    0.638484848485

    I have no idea why some people give bad reviews about this place. It goes to show you, you can please everyone. They are probably griping about something that their own fault...there are many people like that.

    In any case, my friend and I arrived at about 5:50 PM this past Sunday. It was pretty crowded, more than I thought for a Sunday evening and thought we would have to wait forever to get a seat but they said we'll be seated when the girl comes back from seating someone else. We were seated at 5:52 and the waiter came and got our drink orders. Everyone was very pleasant from the host that seated us to the waiter to the server. The prices were very good as well. We placed our orders once we decided what we wanted at 6:02. We shared the baked spaghetti calzone and the small "Here's The Beef" pizza so we can both try them. The calzone was huge and we got the smallest one (personal) and got the small 11" pizza. Both were awesome! My friend liked the pizza better and I liked the calzone better. The calzone does have a sweetish sauce but that's how I like my sauce!

    We had to box part of the pizza to take it home and we were out the door by 6:42. So, everything was great and not like these bad reviewers. That goes to show you that  you have to try these things yourself because all these bad reviewers have some serious issues.
    ----------

    Calculated Polarity and Subjectivity
    ====================================
    0.566666666667
    0.733333333333

    love the gyro plate. Rice is so good and I also dig their candy selection :)
    ----------

    Calculated Polarity and Subjectivity
    ====================================
    0.608645833333
    0.7

    Rosie, Dakota, and I LOVE Chaparral Dog Park!!! It's very convenient and surrounded by a lot of paths, a desert xeriscape, baseball fields, ballparks, and a lake with ducks.

    The Scottsdale Park and Rec Dept. does a wonderful job of keeping the park clean and shaded.  You can find trash cans and poopy-pick up mitts located all over the park and paths.

    The fenced in area is huge to let the dogs run, play, and sniff!
    ----------

    Calculated Polarity and Subjectivity
    ====================================
    0.468125
    0.81

    General Manager Scott Petello is a good egg!!! Not to go into detail, but let me assure you if you have any issues (albeit rare) speak with Scott and treat the guy with some respect as you state your case and I'd be surprised if you don't walk out totally satisfied as I just did. Like I always say..... "Mistakes are inevitable, it's how we recover from them that is important"!!!

    Thanks to Scott and his awesome staff. You've got a customer for life!! .......... :^)
    ----------

    Calculated Polarity and Subjectivity
    ====================================
    0.243277201725
    0.524092459265

    Quiessence is, simply put, beautiful.  Full windows and earthy wooden walls give a feeling of warmth inside this restaurant perched in the middle of a farm.  The restaurant seemed fairly full even on a Tuesday evening; we had secured reservations just a couple days before.

    My friend and I had sampled sandwiches at the Farm Kitchen earlier that week, and were impressed enough to want to eat at the restaurant.  The crisp, fresh veggies didn't disappoint: we ordered the salad with orange and grapefruit slices and the crudites to start.  Both were very good; I didn't even know how much I liked raw radishes and turnips until I tried them with their pesto and aioli sauces.

    For entrees, I ordered the lamb and my friend ordered the pork shoulder.  Service started out very good, but trailed off quickly.  Waiting for our food took a very long time (a couple seated after us received and finished their entrees before we received our's), and no one bothered to explain the situation until the maitre'd apologized almost 45 minutes later.  Apparently the chef was unhappy with the sauce on my entree, so he started anew.  This isn't really a problem, but they should have communicated this to us earlier.  For our troubles, they comped me the glass of wine I ordered, but they forgot to bring out with my entree  as I had requested.  Also, they didn't offer us bread, but I will echo the lady who whispered this to us on her way out: ask for the bread.  We received warm foccacia, apple walnut, and pomegranate slices of wonder with honey and butter.  YUM.

    The entrees were both solid, but didn't quite live up to the innovation and freshness of the vegetables.  My lamb's sauce was delicious, but the meat was tough.  Maybe the vegetarian entrees are the way to go?  But our dessert, the gingerbread pear cake, was yet another winner.

    If the entrees were tad more inspired, or the service weren't so spotty, this place definitely would have warranted five stars.  If I return, I'd like to try the 75$ tasting menu.  Our bill came out to about 100$ for two people, including tip, no drinks.
    ----------

    Calculated Polarity and Subjectivity
    ====================================
    0.300645342312
    0.577132435466

    Drop what you're doing and drive here. After I ate here I had to go back the next day for more.  The food is that good.

    This cute little green building may have gone competely unoticed if I hadn't been driving down Palm Rd to avoid construction.  While waiting to turn onto 16th Street the "Grand Opening" sign caught my eye and my little yelping soul leaped for joy!  A new place to try!

    It looked desolate from the outside but when I opened the door I was put at easy by the decor, smell and cleanliness inside.  I ordered dinner for two, to go.  The menu was awesome.  I loved seeing all the variety: poblano peppers, mole, mahi mahi, mushrooms...something wrapped in banana leaves.  It made it difficult to choose something.  Here's what I've had so far: La Condesa Shrimp Burro and Baja Sur Dogfish Shark Taco.  They are both were very delicious meals but the shrimp burro stole the show.  So much flavor.  I snagged some bites from my hubbys mole and mahi mahi burros- mmmm such a delight.  The salsa bar is endless.  I really stocked up.  I was excited to try the strawberry salsa but it was too hot, in fact it all was, but I'm a big wimp when it comes to hot peppers. The horchata is handmade and delicious.  They throw pecans and some fruit in there too which is a yummy bonus!

    As if the good food wasn't enough to win me over the art in this restaurant sho did!  I'm a sucker for Mexican folk art and Frida Kahlo is my Oprah.  There's a painting of her and Diego hanging over the salsa bar, it's amazing.  All the paintings are great, love the artist.
    ----------

    Calculated Polarity and Subjectivity
    ====================================
    0.225595238095
    0.647619047619

    Luckily, I didn't have to travel far to make my connecting flight. And for this, I thank you, Phoenix.

    My brief layover was pleasant as the employees were kind and the flight was on time.  Hopefully, next time I can grace Phoenix with my presence for a little while longer.
    ----------

    Calculated Polarity and Subjectivity
    ====================================
    0.326388888889
    0.794444444444

    The oldish man who owns the store is as sweet as can be.  Perhaps sweeter than the cookies or ice cream.

    Here's the lowdown: Giant ice cream cookie sandwiches for super cheap.  The flavor permutations are basically endless.  I had snickerdoodle with cookies and cream ice cream.  It was marvelous.
    ----------

    Calculated Polarity and Subjectivity
    ====================================
    0.608333333333
    0.716666666667

    Wonderful Vietnamese sandwich shoppe. Their baguettes are great hot out of the oven with butter or in one of their many sandwich choices. They have a modest selection of baked goods along with some of the best egg rolls around. Bring cash or your ATM card as no credit cards are accepted but they have an ATM on premises.
    ----------



Insight from Bad Reviews
========================

.. code-block:: python

    train_set['negative_review_tags'] = gl.text_analytics.count_words(train_set['text'])

.. code-block:: python

    bad_review_words = (
        'hate','terrible', 'awful', 'spit', 'disgusting', 'filthy', 'tasteless', 'rude',
        'dirty', 'slow', 'poor', 'late', 'angry', 'flies', 'disappointed', 'disappointing', 'wait',
        'waiting', 'dreadful', 'appalling', 'horrific', 'horrifying', 'horrible', 'horrendous', 'atrocious',
        'abominable', 'deplorable', 'abhorrent', 'frightful', 'shocking', 'hideous', 'ghastly', 'grim',
        'dire', 'unspeakable', 'gruesome'
    )
    train_set['negative_review_tags'] = train_set['negative_review_tags'].dict_trim_by_keys(bad_review_words, exclude=False)

.. code-block:: python

    model = gl.linear_regression.create(train_set, target='stars',
                                        features = ['user_id', 'business_id', 'categories_dict', 'negative_review_tags',
                                                    'user_avg_stars', 'votes', 'business_avg_stars'])


.. parsed-literal::

    PROGRESS: Creating a validation set from 5 percent of training data. This may take a while.
              You can set ``validation_set=None`` to disable validation tracking.

    PROGRESS: Linear regression:
    PROGRESS: --------------------------------------------------------
    PROGRESS: Number of examples          : 164054
    PROGRESS: Number of features          : 7
    PROGRESS: Number of unpacked features : 551
    PROGRESS: Number of coefficients    : 50130
    PROGRESS: Starting L-BFGS
    PROGRESS: --------------------------------------------------------
    PROGRESS: +-----------+----------+-----------+--------------+--------------------+----------------------+---------------+-----------------+
    PROGRESS: | Iteration | Passes   | Step size | Elapsed Time | Training-max_error | Validation-max_error | Training-rmse | Validation-rmse |
    PROGRESS: +-----------+----------+-----------+--------------+--------------------+----------------------+---------------+-----------------+
    PROGRESS: | 1         | 6        | 0.000000  | 1.454297     | 18.547201          | 8.797567             | 1.342222      | 1.401939        |
    PROGRESS: | 2         | 9        | 5.000000  | 2.172289     | 13.394241          | 5.203442             | 0.984446      | 1.176960        |
    PROGRESS: | 3         | 10       | 5.000000  | 2.478749     | 30.440370          | 11.241691            | 1.950388      | 2.076235        |
    PROGRESS: | 4         | 12       | 1.000000  | 2.958619     | 4.464780           | 5.129925             | 0.821395      | 1.108677        |
    PROGRESS: | 5         | 13       | 1.000000  | 3.261281     | 4.275049           | 5.307988             | 0.812739      | 1.107683        |
    PROGRESS: | 6         | 14       | 1.000000  | 3.591777     | 4.246562           | 5.457276             | 0.804644      | 1.112277        |
    PROGRESS: | 10        | 18       | 1.000000  | 4.796135     | 4.587629           | 6.365625             | 0.780278      | 1.144836        |
    PROGRESS: +-----------+----------+-----------+--------------+--------------------+----------------------+---------------+-----------------+


.. code-block:: python

    test_set['categories_dict'] = test_set.apply(lambda row: tags_to_dict(row['categories']))
    test_set['categories_dict'].head(5)




.. parsed-literal::

    dtype: dict
    Rows: 5
    [{'Sushi Bars': 1, 'Restaurants': 1}, {'Food': 1, 'Tea Rooms': 1, 'Japanese': 1, 'Restaurants': 1}, {'Pubs': 1, 'Bars': 1, 'Restaurants': 1, 'Nightlife': 1, 'Irish': 1}, {'Breakfast & Brunch': 1, 'Bars': 1, 'Mexican': 1, 'Nightlife': 1, 'Restaurants': 1}, {'American (Traditional)': 1, 'Bars': 1, 'Nightlife': 1, 'Lounges': 1, 'Restaurants': 1}]



.. code-block:: python

    test_set['negative_review_tags'] = gl.text_analytics.count_words(test_set['text'])
    test_set['negative_review_tags'] = test_set['negative_review_tags'].dict_trim_by_keys(bad_review_words, exclude=False)

    model.evaluate(test_set)




.. parsed-literal::

    {'max_error': 6.253360542412668, 'rmse': 1.1452486861156776}



In Progress
=====================

Graph of Elite Users' Connectedness
-----------------------------------

  - Review Data:
    - The Review data set has the user reivews for each business.
      This means that both an encrypted user id and business id is stored in the data set,
      letting us know which user commented on which business.

  - User Data:
    - The User data set tells us detailed information about a user and their profile.
      Distinguishes users who are elite from those that are non-elite

Sentiment Analysis
------------------

  - Tip Data:
    - The tip data set provides immediate updates from the user as sto their experience at a business.
    - Entry is in text format (character strings)

  - Review data set: The review data set includes a full user reviews in text format (character strings)
