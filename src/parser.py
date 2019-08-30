import argparse
import json
import os
import re

from bs4 import BeautifulSoup
from kanji_to_romaji import kanji_to_romaji
from nltk.tokenize.util import is_cjk


def extract_cjk(mixed_string):
    """
    Takes a string with english in it and spits out only the Japanese parts
    This is mostly for the tooltip attributes

    :param mixed_string: A string with some Japanese and some other language in it
    :return: A string with only the Japanese parts
    """
    jp_only = []

    for char in mixed_string:

        if is_cjk(char):
            jp_only.append(char)

    return "".join(jp_only)


def scrape_html(source, trim, dest, lang):

    # this must be r+ mode because a+ doesn't work with beautifulsoup
    with open(source, "r+") as f:

        soup = BeautifulSoup(f, "html.parser")

        # removes all script and style tags
        for script in soup(["script", "style"]):
            script.decompose()

        # just the text
        text = soup.get_text()
        lines = [
            line
            for line in text.split()
            if line != "" and any([is_cjk(char) for char in line])
        ]

        # <i> tags
        eyes = [
            i["title"]
            for i in soup.find_all("i")
            if i.has_attr("title") and any(is_cjk(char) for char in i["title"])
        ]

        # tooltip attributes in spans
        tooltips = [
            extract_cjk(s["uib-tooltip"])
            for s in soup.find_all("span")
            if s.has_attr("uib-tooltip")
            and any(is_cjk(char) for char in s["uib-tooltip"])
        ]

        lines += eyes
        lines += tooltips

        # sort the lines by length, to avoid the edge case where a short string is a substring of a longer string
        # and the short substring gets replaced first and breaks the longer string into 日本romaji語 that doesn't
        # get picked up by the regex
        lines = sorted(lines, key=len, reverse=True)

        # only take the first three words of long romaji strings
        romaji = {"_".join(kanji_to_romaji(line).split()[:3]): line for line in lines}

        # convert the entire html doc into a string to parse with regex
        # this is because contents breaks the document into pieces by parent elements and re.search doesn't work well
        soup_str = str(soup.prettify())

        # the prefix for the json keys
        file_path = os.path.normpath(f.name)
        file_path = file_path.replace(os.path.splitext(file_path)[1], "")

        # removes a subset of directories from the filepath up to and including the trim argument
        if trim:
            trim_index = file_path.find(trim)

            if trim_index == -1:
                raise ValueError("Subdir path doesn't exist")

            trim_path = file_path[(trim_index + len(trim)) :].replace(trim, "")
            split_path = trim_path.split(os.sep)[1:]
            camelCase = [s.title() for s in split_path[1:]]
            strip_punctuation = [s.replace("_", "") for s in camelCase]
            file_prefix = "".join([split_path[0]] + strip_punctuation)

        # removes everything in the path up to zcs
        else:
            split_path = file_path.split(os.sep)[1:]
            split_dirs = split_path[split_path.index("zcs") :]
            camelCase = [s.title() for s in split_dirs[1:]]
            strip_punctuation = [s.replace("_", "") for s in camelCase]
            file_prefix = "".join([split_dirs[0]] + strip_punctuation)

        # overwrite japanese strings with {{ romaji tags }}
        for key, value in romaji.items():
            jp_re = re.compile(value)
            soup_str = jp_re.sub(
                f"{{{{ '{file_prefix}.{key}' | translate }}}}", soup_str
            )

        # path to save the json file to
        base_dir = os.path.split(f.name)[0]
        json_file = f"{os.path.splitext(os.path.split(f.name)[1])[0]}.{lang}.json"

        if dest:
            home = os.getcwd()
            output_path = os.path.join(home, dest, json_file)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        else:
            # write out a json file adjacent to the html file
            json_path = os.path.join(base_dir, json_file)
            output_path = json_path

        with open(output_path, "w+") as rj:
            json.dump({file_prefix: romaji}, rj, ensure_ascii=False, indent=2)

        # zero out the file and replace it with the modified string in place
        f.seek(0)
        f.truncate()
        f.write(soup_str)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Replaces Japanese in an html file with romaji translation tags"
    )
    parser.add_argument("source", type=str, help="Path to an html file")
    parser.add_argument(
        "-t",
        "--trim",
        type=str,
        help="Removes everything up to and including the subdirs from the generated json key",
    )
    parser.add_argument(
        "-d",
        "--dest",
        type=str,
        help="Output directory relative to PWD.  Defaults to source file directory",
    )
    parser.add_argument(
        "-l",
        "--lang",
        type=str,
        default="ja",
        help="Two letter language code",
    )
    args = parser.parse_args()
    scrape_html(args.source, args.trim, args.dest)
