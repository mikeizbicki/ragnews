#!/bin/python3

'''
Run an interactive QA session with the news articles using the Groq LLM API and retrieval augmented generation (RAG).

New articles can be added to the database with the --add_url parameter,
and the path to the database can be changed with the --db parameter.
'''

from urllib.parse import urlparse
import datetime
import logging
import re
import sqlite3

import groq

from groq import Groq
import os


################################################################################
# LLM functions
################################################################################

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)


def run_llm(system, user, model='llama-3.1-70b-versatile', seed=None):
    '''
    This is a helper function for all the uses of LLMs in this file.
    '''
    chat_completion = client.chat.completions.create(
        messages=[
            {
                'role': 'system',
                'content': system,
            },
            {
                "role": "user",
                "content": user,
            }
        ],
        model=model,
        seed=seed,
    )
    return chat_completion.choices[0].message.content


def summarize_text(text, seed=None):
    system = 'Summarize the input text below.  Limit the summary to 1 paragraph.  Use an advanced reading level similar to the input text, and ensure that all people, places, and other proper and dates nouns are included in the summary.  The summary should be in English.'
    return run_llm(system, text, seed=seed)


def translate_text(text):
    system = 'You are a professional translator working for the United Nations.  The following document is an important news article that needs to be translated into English.  Provide a professional translation.'
    return run_llm(system, text)


def extract_keywords(text, seed=None):
    r'''
    This is a helper function for RAG.
    Given an input text,
    this function extracts the keywords that will be used to perform the search for articles that will be used in RAG.

    >>> extract_keywords('Who is the current democratic presidential nominee?', seed=0)
    'Joe candidate nominee presidential Democrat election primary TBD voting politics'
    >>> extract_keywords('What is the policy position of Trump related to illegal Mexican immigrants?', seed=0)
    'Trump Mexican immigrants policy position illegal border control deportation walls'

    Note that the examples above are passing in a seed value for deterministic results.
    In production, you probably do not want to specify the seed.
    '''

    # FIXME:
    # Implement this function.
    # It's okay if you don't get the exact same keywords as me.
    # You probably certainly won't because you probably won't come up with the exact same prompt as me.
    # To make the test cases above pass,
    # you'll have to modify them to be what the output of your prompt provides.

    system = 'Extract the most important 10 words from the user prompt.  All names and other proper nouns should be included in the output list.  For non-proper nouns, synonyms and related words should also appear in the output.  Each word should appear on a line by itself, with no numbering or other formatting.  Do not provide an explanation of what you did, only provide the list of words in the proper format.'
    user = text
    rex = re.compile(r'\W+')
    results = run_llm(system, user, seed=seed)
    return rex.sub(' ', results)


################################################################################
# helper functions
################################################################################

def _logsql(sql):
    rex = re.compile(r'\W+')
    sql_dewhite = rex.sub(' ', sql)
    logging.debug(f'SQL: {sql_dewhite}')


def _catch_errors(func):
    '''
    This function is intended to be used as a decorator.
    It traps whatever errors the input function raises and logs the errors.
    We use this decorator on the add_urls method below to ensure that a webcrawl continues even if there are errors.
    '''
    def inner_function(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            logging.error(str(e))
    return inner_function


################################################################################
# rag
################################################################################


def rag(text, db, keywords_text=None):
    '''
    This function uses retrieval augmented generation (RAG) to generate an LLM response to the input text.
    The db argument should be an instance of the `ArticleDB` class that contains the relevant documents to use.
    '''

    if keywords_text is None:
        keywords_text = text

    # FIXME:
    # Implement this function.
    # Recall that your RAG system should:
    # 1. Extract keywords from the text.
    # 2. Use those keywords to find articles related to the text.
    # 3. Construct a new user prompt that includes all of the articles and the original text.
    # 4. Pass the new prompt to the LLM and return the result.
    #
    # HINT:
    # You will also have to write your own system prompt to use with the LLM.
    # I needed a fairly long system prompt (about 15 lines) in order to get good results.
    # You can start with a basic system prompt right away just to check if things are working,
    # but don't spend a lot of time on the system prompt until you're sure everything else is working.
    # Then, you can iteratively add more commands into the system prompt to correct "bad" behavior you see in your program's output.

    keywords = extract_keywords(keywords_text)

    articles = db.find_articles(keywords)
    assert(len(articles) > 0)
    user = ''
    for i, article in enumerate(articles):
        user += f'''
ARTICLE{i}_URL: {article['url']}
ARTICLE{i}_TITLE: {article['title']}
ARTICLE{i}_SUMMARY: {article['en_summary']}
'''

    user += f'''
QUESTION: {text}
    '''
    
    system = f'You are a professional news commentator answering questions about current events.  Your audience is well educated American citizens, but they have not been following the news closely.  Below, you are given a question and several related news articles.   The current date is now {datetime.datetime.now().isoformat()}, and these news articles are all contain new information about the world since you were last trained.  Your job is to answer the question in an unbiased manner using the new information provided in the news articles.  As much as practical, you should use only knowledge contained in the news articles and not background knowledge, because the background knowledge might be out of date.  Your final answer should not mention that you are summarizing news articles, just provide the information the way a professional news commentator would provide it.  Do not provide citations.  Your answers should be short and to the point.  They should be at most 1 paragraph, and preferably only 1-2 sentences.  Do not provide any extra commentary unless asked.  It is okay to provide opinions about controversial subjects such as who to vote for as long as those opinions are grounded in facts specified in both the user prompt and the news articles.  If there is not enough information in the user prompt, then ask for the specified information to be provided.'

    logging.info('rag.SYSTEM: ' + system)
    logging.info('rag.USER: ' + user)

    return run_llm(system, user)


class ArticleDB:
    '''
    This class represents a database of news articles.
    It is backed by sqlite3 and designed to have no external dependencies and be easy to understand.

    The following example shows how to add urls to the database.

    >>> db = ArticleDB()
    >>> len(db)
    0
    >>> db.add_url(ArticleDB._TESTURLS[0])
    >>> len(db)
    1

    Once articles have been added,
    we can search through those articles to find articles about only certain topics.

    >>> articles = db.find_articles('Economía')

    The output is a list of articles that match the search query.
    Each article is represented by a dictionary with a number of fields about the article.

    >>> articles[0]['title']
    'La creación de empleo defrauda en Estados Unidos en agosto y aviva el temor a una recesión | Economía | EL PAÍS'
    >>> articles[0].keys()
    ['rowid', 'rank', 'title', 'publish_date', 'hostname', 'url', 'staleness', 'timebias', 'en_summary', 'text']
    '''

    _TESTURLS = [
        'https://elpais.com/economia/2024-09-06/la-creacion-de-empleo-defrauda-en-estados-unidos-en-agosto-y-aviva-el-fantasma-de-la-recesion.html',
        'https://www.cnn.com/2024/09/06/politics/american-push-israel-hamas-deal-analysis/index.html',
        ]

    def __init__(self, filename=':memory:'):
        self.db = sqlite3.connect(filename)
        self.db.row_factory=sqlite3.Row
        self.logger = logging
        self._create_schema()

    def _create_schema(self):
        '''
        Create the DB schema if it doesn't already exist.

        The test below demonstrates that creating a schema on a database that already has the schema will not generate errors.

        >>> db = ArticleDB()
        >>> db._create_schema()
        >>> db._create_schema()
        '''
        try:
            sql = '''
            CREATE VIRTUAL TABLE articles
            USING FTS5 (
                title,
                text,
                hostname,
                url,
                publish_date,
                crawl_date,
                lang,
                en_translation,
                en_summary
                );
            '''
            self.db.execute(sql)
            self.db.commit()

        # if the database already exists,
        # then do nothing
        except sqlite3.OperationalError:
            self.logger.debug('CREATE TABLE failed')

    def find_articles(self, query, limit=10, timebias_alpha=1):
        '''
        Return a list of articles in the database that match the specified query.

        Lowering the value of the timebias_alpha parameter will result in the time becoming more influential.
        '''
        
        # FIXME:
        # Implement this function.
        # You do not need to concern yourself with the timebias_alpha parameter.
        #
        # HINT:
        # The only thing my solution does is pass a SELECT statement to the sqlite3 database.
        # The SELECT statement will need to use sqlite3's FTS5 syntax for full text search.
        # If you need to review how to coordinate sqlite3 and python,
        # there is an example in the __len__ method below.
        # The details of the SELECT statement will be different
        # (because the functions collect different information)
        # but the outline of the python code is the same.

        sql = '''
        SELECT
            rowid,
            rank,
            title,
            publish_date,
            hostname,
            url,
            MAX(1, abs(MIN(JULIANDAY(publish_date), JULIANDAY(crawl_date)) - JULIANDAY(date('now')))) AS staleness,
            (?)/(? + MAX(1, abs(MIN(JULIANDAY(publish_date), JULIANDAY(crawl_date)) - JULIANDAY(date('now'))))) AS timebias,
            en_summary,
            text
        FROM articles(?)
        WHERE text IS NOT NULL
        ORDER BY rank*timebias ASC
        LIMIT ?;
        '''
        _logsql(sql)
        cursor = self.db.cursor()
        cursor.execute(sql, [timebias_alpha,timebias_alpha,query, limit])
        return cursor.fetchall()

    @_catch_errors
    def add_url(self, url, recursive_depth=0, allow_dupes=False):
        '''
        Download the url, extract various metainformation, and add the metainformation into the db.

        By default, the same url cannot be added into the database multiple times.

        >>> db = ArticleDB()
        >>> db.add_url(ArticleDB._TESTURLS[0])
        >>> db.add_url(ArticleDB._TESTURLS[0])
        >>> db.add_url(ArticleDB._TESTURLS[0])
        >>> len(db)
        1

        >>> db = ArticleDB()
        >>> db.add_url(ArticleDB._TESTURLS[0], allow_dupes=True)
        >>> db.add_url(ArticleDB._TESTURLS[0], allow_dupes=True)
        >>> db.add_url(ArticleDB._TESTURLS[0], allow_dupes=True)
        >>> len(db)
        3

        '''
        logging.info(f'add_url {url}')
        from bs4 import BeautifulSoup
        import requests
        import metahtml

        if not allow_dupes:
            logging.debug(f'checking for url in database')
            sql = '''
            SELECT count(*) FROM articles WHERE url=?;
            '''
            _logsql(sql)
            cursor = self.db.cursor()
            cursor.execute(sql, [url])
            row = cursor.fetchone()
            is_dupe = row[0] > 0
            if is_dupe:
                logging.debug(f'duplicate detected, skipping!')
                return

        logging.debug(f'downloading url')
        try:
            response = requests.get(url)
        except requests.exceptions.MissingSchema:
            # if no schema was provided in the url, add a default
            url = 'https://' + url
            response = requests.get(url)
        parsed_uri = urlparse(url)
        hostname = parsed_uri.netloc

        logging.debug(f'extracting information')
        parsed = metahtml.parse(response.text, url)
        info = metahtml.simplify_meta(parsed)

        if info['type'] != 'article' or len(info['content']['text']) < 100:
            logging.debug(f'not an article... skipping')
            en_translation = None
            en_summary = None
            info['title'] = None
            info['content'] = {'text': None}
            info['timestamp.published'] = {'lo': None}
            info['language'] = None
        else:
            logging.debug('summarizing')
            if not info['language'].startswith('en'):
                en_translation = translate_text(info['content']['text'])
            else:
                en_translation = None
            en_summary = summarize_text(info['content']['text'])

        logging.debug('inserting into database')
        sql = '''
        INSERT INTO articles(title, text, hostname, url, publish_date, crawl_date, lang, en_translation, en_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        '''
        _logsql(sql)
        cursor = self.db.cursor()
        cursor.execute(sql, [
            info['title'],
            info['content']['text'], 
            hostname,
            url,
            info['timestamp.published']['lo'],
            datetime.datetime.now().isoformat(),
            info['language'],
            en_translation,
            en_summary,
            ])
        self.db.commit()

        logging.debug('recursively adding more links')
        if recursive_depth > 0:
            for link in info['links.all']:
                url2 = link['href']
                parsed_uri2 = urlparse(url2)
                hostname2 = parsed_uri2.netloc
                if hostname in hostname2 or hostname2 in hostname:
                    self.add_url(url2, recursive_depth-1)
        
    def __len__(self):
        sql = '''
        SELECT count(*)
        FROM articles
        WHERE text IS NOT NULL;
        '''
        _logsql(sql)
        cursor = self.db.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        return row[0]


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--loglevel', default='warning')
    parser.add_argument('--db', default='ragnews.db')
    parser.add_argument('--recursive_depth', default=0, type=int)
    parser.add_argument('--add_url', help='If this parameter is added, then the program will not provide an interactive QA session with the database.  Instead, the provided url will be downloaded and added to the database.')
    args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=args.loglevel.upper(),
        )

    db = ArticleDB(args.db)

    if args.add_url:
        db.add_url(args.add_url, recursive_depth=args.recursive_depth, allow_dupes=True)

    else:
        import readline
        while True:
            text = input('ragnews> ')
            if len(text.strip()) > 0:
                output = rag(text, db)
                print(output)
