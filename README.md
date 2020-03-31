

## Installation

For installing, follow these intructions

```
conda env create -f environment.yml
source activate iclr_website
pip install -r requirements.txt
```

## Test

```
bash run.sh or sh run.sh
```

Starts a server goto http://localhost:5000/index.html

## Make static pages

```
bash freeze.sh
```

Puts the static pages in `build/`

## Code

Code is all in `main.py`

HTML is all in  `templates/pages/page.html`

