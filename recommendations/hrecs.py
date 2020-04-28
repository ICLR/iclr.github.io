import numpy as np
from collections import Counter
import sys, os, subprocess, re, itertools, datetime, pickle, random, nltk.tokenize, nltk.corpus, gensim, pprint

def rec_scores(A, recs, sort=True):
    l = [sum([A[i,j] for j in rec if i != j]) for i,rec in recs.items()]
    if sort: l = sorted(l)
    return l

def rec_frequencies(A, recs):
    c = Counter(j for i,rec in recs.items() for j in rec if i != j)
    for i in range(A.shape[0]):
        if i not in c:
            c[i] = 0
    return c

def print_biggest_deltas(A, recs1, recs2, print_item, k=4):
    scores1 = rec_scores(A, recs1, sort=False)
    scores2 = rec_scores(A, recs2, sort=False)
    deltas = sorted([(s1-s2, i) for i,(s1,s2) in enumerate(zip(scores1,scores2))])
    #for i in range(k):
    #    j = deltas[i][1]
    #    print_item(i, deltas[i][0], j, scores1[j], scores2[j], recs1[j], recs2[j])
    for i in range(k):
        j = deltas[-i-1][1]
        print_item(-i-1, deltas[-i-1][0], j, scores1[j], scores2[j], recs1[j], recs2[j])

def sqrt_score(freqv):
    return sum(map(np.sqrt, freqv)) / len(freqv)

def print_rec_stats(A, recs):
    scores = rec_scores(A, recs)
    freqs = rec_frequencies(A, recs)
    freqv = sorted(list(freqs.values()))
    n = len(scores)
    m = len(freqv)

    print(f"""
       total items: {n}

        mean score: {sum(scores)/n}
   quartile scores: {scores[n//4]}  {scores[n//2]}  {scores[(3*n)//4]}
    minimum scores: {scores[:5]}
    maximum scores: {scores[-5:]}

         mean freq: {sum(freqv)/m}
    quartile freqs: {freqv[m//4]}  {freqv[m//2]}  {freqv[(3*m)//4]}
     minimum freqs: {freqv[:5]}
     maximum freqs: {freqv[-5:]}
         num zeros: {len([i for i in freqv if i == 0])}
     num zero/ones: {len([i for i in freqv if i <= 1])}
  sqrt(freq) score: {sqrt_score(freqv)}
    """)

#################################################################
## COPIED FROM ICML 2020 LDA STUFF
#################################################################
def remove_line_numbers(a):
    def isnum(s):
        return len(s) == 3 and s[0].isnumeric() and s[1].isnumeric() and s[2].isnumeric()
    b = []
    i = 0
    n = len(a)
    a += ["", ""]
    while i < n:
        if isnum(a[i]) and isnum(a[i+1]) and isnum(a[i+2]):
            while i < len(a) and isnum(a[i]):
                i += 1
            continue
        else:
            b.append(a[i])
            i += 1
    return b

def join_lines(a):
    b = []
    this = ""
    for l in a:
        if re.match('^\s*$', l):
            if len(this) > 0: b.append(this)
            this = ''
        else:
            if len(this)>0 and this[-1] == '-': this = this[:-1] + l
            else: this += ' ' + l
    if len(this) > 0: b.append(this)
    return b
    
def read_pdf_as_text(fname, swords=None):
    if swords is None:
        swords = set(nltk.corpus.stopwords.words('english'))
    txt = subprocess.check_output(['pdftotext', fname, '-']) \
            if fname.endswith('.pdf') else \
          open(fname, 'rb').read()
    txt = txt.decode('utf-8')
    txt = remove_line_numbers(re.split('\r*\n+', txt))
    txt = join_lines(txt)
    return list(itertools.chain.from_iterable([[w.lower() \
                         for w in nltk.tokenize.word_tokenize(l) \
                         if len(w) > 2 \
                         if w.lower() not in swords \
                         if 'latexit' not in w \
                         if re.match('^[0-9.]*$', w) is None] \
                        for l in txt]))

def read_all_pdfs(direc='pdfs'):
    swords = set(nltk.corpus.stopwords.words('english'))
    all_pdfs = []
    for fname in os.listdir(direc):
        if not fname.endswith('.pdf'): continue
        fname = fname[:-4] + '.txt' # get text version, assuming pdftotext has already run
        all_pdfs.append((fname, os.path.join(direc, fname)))
    print('found %d pdfs' % len(all_pdfs))
    res = []
    for nn, (d_id, fname) in enumerate(all_pdfs):
        res.append((d_id, read_pdf_as_text(fname, swords)))
        if nn % 100 == 0: sys.stderr.write(str(nn))
        elif nn % 10 == 0: sys.stderr.write('.')
        sys.stderr.flush()
    sys.stderr.write('\n')
    return res

def generate_iclr_pickle():
    corpus_with_ids = read_all_pdfs()
    pickle.dump(corpus_with_ids, open('iclr_fulltext.pkl', 'wb'))
    print('read %d papers' % len(corpus_with_ids))
    
    print('total %d tokens' % sum(len(doc[1]) for doc in corpus_with_ids))
    print('shortest:')
    pprint.pprint(sorted((len(doc), 'id=%s' % id) for id,doc in corpus_with_ids)[:20])

class PrintEpoch(gensim.models.callbacks.Callback):
    def __init__(self, corpus):
        self.epoch = 0
        self.small_corpus = corpus[::50]
        self.logger='me'
        self.best_ppl = None
        self.time = datetime.datetime.now()
        
    def get_value(self, *args, **kwargs): 
        self.epoch += 1
        ppl = kwargs['model'].log_perplexity(self.small_corpus)
        sec_passed = datetime.datetime.now() - self.time
        self.time += sec_passed
        print('pass %03d\tppl %0.4g\tsince last %s' % (self.epoch, ppl, sec_passed))
        return 0

def run_lda_on_iclr():
    corpus_with_ids = pickle.load(open('iclr_fulltext.pkl', 'rb'))
    print('read %d papers' % len(corpus_with_ids))
    corpus_with_ids = { a:b for (a,b) in corpus_with_ids }

    lda = pickle.load(open('lda_100_200_100.pkl', 'rb'))
    lda_dict = pickle.load(open('lda_dict.pkl', 'rb'))
    common_phrases = pickle.load(open('phrases.pkl', 'rb'))
    phraser = gensim.models.phrases.Phraser(common_phrases)

    def get_topics(doc):
        for token in phraser[doc]:
            if '_' in token:
                doc.append(token)
        bow = lda_dict.doc2bow(doc)
        return lda.get_document_topics(bow)

    A = np.zeros((len(corpus_with_ids), lda.num_topics))
    accepted_submissions = pickle.load(open("../cached_or.pkl", "br"))
    for ii, (k, v) in accepted_submissions.items():
        pdf = v.content["pdf"]
        pdf = pdf[5:-4] + '.txt'
        doc = corpus_with_ids[pdf]
        for topic, prob in get_topics(doc):
            A[ii, topic] = prob

    #for i, (_, doc) in enumerate(corpus_with_ids):
    #    for k,p in get_topics(doc):
    #        A[i,k] = p

    np.save(open('iclr_paper_topics.np', 'wb'), A)

    #import ipdb; ipdb.set_trace()

#run_lda_on_iclr()
