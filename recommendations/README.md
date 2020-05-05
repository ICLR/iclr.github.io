Run the recommendations code to produce a set of scores and recs.
The model learns a `1024 dimensional embedding` corresponding to each paper based on the abstract data.

## Setup & Usage

#### Install git-lfs, required to download the saved model later.
```bash
#### Linux
apt-get install git-lfs

#### MacOS
brew install git-lfs
```

```bash
git lfs install
rm -fr iclr.github.io
git clone https://github.com/ICLR/iclr.github.io
pip install -r iclr.github.io/requirements.txt
pip install -r iclr.github.io/recommendations/requirements.txt
```

To create the embeddings for the papers using the abstract information, run the following python script.

```bash
python cache_paper_embeddings.py
```