# What is this
It parses html files for 日本語 and turns it into {{ romaji | translate }} tags 
and outputs a json file with romaji as keys and the original 日本語 as values

# How to use this
`pip install -r requirements.txt`

`python src/parser.py /path/with/a/bunch/of/subdirs/app/file.html --trim /with/a/bunch/of/subdirs/ --dest /output/path`