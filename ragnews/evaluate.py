'''
This file is for evaluating the quality of our RAG system
using the Hairy Trumpet tool/dataset.
'''

import ragnews

class RAGEvaluator:
    def predict(self, masked_text):
        '''
        >>> model = RAGEvaluator()
        >>> model.predict('There no mask token here.')
        []
        >>> model.predict('[MASK0] is the democratic nominee')
        ['Harris']
        >>> model.predict('[MASK0] is the democratic nominee and [MASK1] is the republican nominee')
        ['Harris', 'Trump']
        '''
        # you might think about:
        # calling the ragnews.run_llm function directly;
        # so we will call the ragnews.rag function

        valid_labels = ['Harris', 'Trump']

        db = ragnews.ArticleDB('ragnews.db')
        textprompt = f'''
This is a fancier question that is based on standard cloze style benchmarks.
I'm going to provide you a sentence, and that sentence will have a masked token inside of it that will look like [MASK0] or [MASK1] or [MASK2] and so on.
And your job is to tell me what the value of that masked token was.
Valid values include: {valid_labels}

The size of you output should just be a single word for each mask.
You should not provide any explanation or other extraneous words.
If there are multiple mask tokens, provide each token separately with a whitespace in between.

INPUT: [MASK0] is the democratic nominee
OUTPUT: Harris

INPUT: [MASK0] is the democratic nominee and [MASK1] is the republican nominee
OUTPUT: Harris Trump

INPUT: {masked_text}
OUTPUT: '''
        output = ragnews.rag(textprompt, db, keywords_text=masked_text)
        return output

        # Reasons why bad results:
        # 1. the code (esp the prompt) in this function is bad
        # 2. the rag function itself could be bad
        #
        # In order to improve (1) above:
        # 1. prompt engineering didn't work
        # 2. I had to change what model I was using

import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO,
    )
