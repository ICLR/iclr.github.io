import numpy as np
import torch
import random
from collections import Counter

unk_string = "UUUNKKK"

def get_ngrams(examples, share_vocab, max_len=200000, n=3):
    def update_counter(counter, sentence):
        word = " " + sentence.strip() + " "
        lis = []
        for j in range(len(word)):
            idx = j
            ngram = ""
            while idx < j + n and idx < len(word):
                ngram += word[idx]
                idx += 1
            if not len(ngram) == n:
                continue
            lis.append(ngram)
        counter.update(lis)

    counter = Counter()

    for i in examples:
        update_counter(counter, i.sentence)

    counter = sorted(counter.items(), key=lambda x: x[1], reverse=True)[0:max_len]
    vocab = {}
    for i in counter:
        vocab[i[0]] = len(vocab)

    vocab[unk_string] = len(vocab)
    return vocab, None

def get_words(examples, share_vocab, max_len=200000):
    def update_counter(counter, sentence):
        counter.update(sentence.split())

    counter = Counter()

    for i in examples:
        update_counter(counter, i.sentence)

    counter = sorted(counter.items(), key=lambda x: x[1], reverse=True)[0:max_len]

    vocab = {}
    for i in counter:
        vocab[i[0]] = len(vocab)

    vocab[unk_string] = len(vocab)

    return vocab, None

def get_minibatches_idx(n, minibatch_size, shuffle=False):
    idx_list = np.arange(n, dtype="int32")

    if shuffle:
        np.random.shuffle(idx_list)

    minibatches = []
    minibatch_start = 0
    for i in range(n // minibatch_size):
        minibatches.append(idx_list[minibatch_start:
                                    minibatch_start + minibatch_size])
        minibatch_start += minibatch_size

    if (minibatch_start != n):
        minibatches.append(idx_list[minibatch_start:])

    return list(zip(range(len(minibatches)), minibatches))

def max_pool(x, lengths, gpu):
    out = torch.FloatTensor(x.size(0), x.size(2)).zero_()
    if gpu:
        out = out.cuda()
    for i in range(len(lengths)):
        out[i] = torch.max(x[i][0:lengths[i]], 0)[0]
    return out

def mean_pool(x, lengths, gpu):
    out = torch.FloatTensor(x.size(0), x.size(2)).zero_()
    if gpu:
        out = out.cuda()
    for i in range(len(lengths)):
        out[i] = torch.mean(x[i][0:lengths[i]], 0)
    return out

def lookup(words, w, zero_unk):
    w = w.lower()
    if w in words:
        return words[w]
    else:
        if zero_unk:
            return None
        else:
            return words[unk_string]

class Batch(object):
    def __init__(self):
        self.g1 = None
        self.g1_l = None
        self.g2 = None
        self.g2_l = None
        self.p1 = None
        self.p1_l = None
        self.p2 = None
        self.p2_l = None

class Example(object):
    def __init__(self, sentence):
        self.sentence = sentence
        self.embeddings = []

    def populate_ngrams(self, words, zero_unk, n):
        embeddings = []
        if type(self.sentence) == str:
            sentence = [self.sentence]
        else:
            sentence = self.sentence
        for i in sentence:
            sent = " " + i.strip() + " "

            for j in range(len(sent)):
                idx = j
                gr = ""
                while idx < j + n and idx < len(sent):
                    gr += sent[idx]
                    idx += 1
                if not len(gr) == n:
                    continue
                wd = lookup(words, gr, zero_unk)
                if wd is not None:
                    embeddings.append(wd)

        if len(embeddings) == 0:
            return [words[unk_string]]
        return embeddings

    def populate_embeddings(self, words, zero_unk, ngrams):
        if ngrams:
            self.embeddings = self.populate_ngrams(words, zero_unk, ngrams)
        else:
            if type(self.sentence) == str:
                sentence = [self.sentence]
            else:
                sentence = self.sentence
            for i in sentence:
                arr = i.split()
                for i in arr:
                    wd = lookup(words, i, zero_unk)
                    if wd is not None:
                        self.embeddings.append(wd)
            if len(self.embeddings) == 0:
                self.embeddings = [words[unk_string]]
