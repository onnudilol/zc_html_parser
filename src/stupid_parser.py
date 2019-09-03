from kanji_to_romaji import kanji_to_romaji
from nltk.tokenize.util import is_cjk
import re
import argparse
import os
import json
import shutil


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


def main(source, trim, dest, prefix):

    tl_json = {}
    file_name = os.path.split(source)[1]

    with open("new_file", "w") as new_file:
        with open(source) as old_file:
            # the prefix for the json keys
            file_path = os.path.normpath(old_file.name)
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

            # removes everything in the path up to zenclerk
            else:
                split_path = file_path.split(os.sep)[1:]
                split_dirs = split_path[split_path.index("zenclerk") :]
                camelCase = [s.title() for s in split_dirs[1:]]
                strip_punctuation = [s.replace("_", "") for s in camelCase]
                file_prefix = "".join([split_dirs[0]] + strip_punctuation)

            for line in old_file:
                if any([is_cjk(char) for char in line]):
                    japanese = extract_cjk(line)
                    romaji = "_".join(kanji_to_romaji(japanese).split()[:3])
                    tl_json[romaji] = japanese
                    new_file.write(
                        str(
                            re.sub(
                                japanese,
                                f"{{{{ '{file_prefix}.{romaji}' | translate }}}}",
                                line,
                            )
                        )
                    )
                else:
                    new_file.write(line)

        shutil.move(os.path.join(os.getcwd(), "new_file"), source)

        # path to save the json file to
        base_dir = os.path.split(old_file.name)[0]
        json_file = (
            f"{os.path.splitext(os.path.split(old_file.name)[1])[0]}{prefix}.json"
        )

        if dest:
            home = os.getcwd()
            output_path = os.path.join(home, dest, json_file)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        else:
            # write out a json file adjacent to the html file
            json_path = os.path.join(base_dir, json_file)
            output_path = json_path

        with open(output_path, "w+") as rj:
            json.dump({file_prefix: tl_json}, rj, ensure_ascii=False, indent=2)
            rj.write("\n")


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
        "-p", "--prefix", type=str, default="", help="Some sort of prefix"
    )
    args = parser.parse_args()
    main(args.source, args.trim, args.dest, args.prefix)
