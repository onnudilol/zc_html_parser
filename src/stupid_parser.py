from kanji_to_romaji import kanji_to_romaji
from nltk.tokenize.util import is_cjk
import re
import argparse
import os
import json
import shutil
import yaml
import string


def extract_cjk(mixed_string):
    """
    Takes a string with english in it and spits out only the Japanese parts
    This is mostly for the tooltip attributes

    :param mixed_string: A string with some Japanese and some other language in it
    :return: A string with only the Japanese parts
    """
    jp_only = []
    jp_start_index = 0
    jp_end_index = 0
    jp_punctuation = ['（', '）']

    for char in mixed_string:

        if is_cjk(char) or char in jp_punctuation:
            jp_only.append(char)

    return "".join(jp_only)


def main(source, trim, dest, prefix, key):

    tl_dict = {}
    file_name = os.path.split(source)[1]

    with open("new_file", "w") as new_file:
        with open(source) as old_file:
            # the prefix for the json keys
            file_path = os.path.normpath(old_file.name)
            file_path = file_path.replace(os.path.splitext(file_path)[1], "")
            file_ext = os.path.splitext(file_name)[1]

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

            # sets the translation tag to a manually input key
            elif key:
                file_prefix = key

            # removes everything in the path up to zenclerk
            else:
                split_path = file_path.split(os.sep)[1:][-3:]
                camelCase = [s.title() for s in split_path[1:]]
                strip_punctuation = [s.replace("_", "") for s in camelCase]
                file_prefix = "".join([split_path[0]] + strip_punctuation)

            for line in old_file:

                if any([is_cjk(char) for char in line]):
                    japanese = extract_cjk(line)
                    romaji = "_".join(re.sub('[()]', '', kanji_to_romaji(japanese)).split()[:3])
                    tl_dict[romaji] = japanese

                    i18n_tag = {
                        ".html": f"{{{{ '{file_prefix}.{romaji}' | translate }}}}",
                        ".js": f"$translate.instant('{file_prefix}.{romaji}')",
                        ".rb": f"t('{romaji}')"
                    }
                    if file_ext == ".html":
                        new_file.write(
                            str(
                                re.sub(
                                    japanese,
                                    i18n_tag[file_ext],
                                    line,
                                )
                            )
                        )
                    elif file_ext == ".js":
                        new_file.write(
                            str(
                                re.sub(
                                    f"'{japanese}'",
                                    i18n_tag[file_ext],
                                    line,
                                )
                            )
                        )
                    else:
                        new_file.write(
                            str(
                                re.sub(
                                    f"'{japanese}'",
                                    i18n_tag[file_ext],
                                    line,
                                )
                            )
                        )

                else:
                    new_file.write(line)


        shutil.move(os.path.join(os.getcwd(), "new_file"), source)

        # path to save the json file to
        base_dir = os.path.split(old_file.name)[0]
        if file_ext == '.html' or file_ext == '.js':
            i18n_file = (
                f"{os.path.splitext(os.path.split(old_file.name)[1])[0]}{prefix}.json"
            )
            if dest:
                home = os.getcwd()
                output_path = os.path.join(home, dest, i18n_file)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
            else:
                # write out a json file adjacent to the html file
                json_path = os.path.join(base_dir, i18n_file)
                output_path = json_path

            with open(output_path, "w+") as rj:
                if key:
                    json_key = key.split('.')
                    romaji_dict = {json_key[-1]: tl_dict}

                    for k in json_key[:-1]:
                        romaji_dict = {k: romaji_dict}

                    json.dump(romaji_dict, rj, ensure_ascii=False, indent=2)
                else:
                    json.dump({file_prefix: tl_dict}, rj, ensure_ascii=False, indent=2)
                rj.write("\n")
        else:
            i18n_file = (
                f"{os.path.splitext(os.path.split(old_file.name)[1])[0]}{prefix}.yml"
            )

            if dest:
                home = os.getcwd()
                output_path = os.path.join(home, dest, i18n_file)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
            else:
                # write out a json file adjacent to the html file
                json_path = os.path.join(base_dir, i18n_file)
                output_path = json_path

            with open(output_path, "w+") as rj:
                yaml.dump({file_prefix: tl_dict}, rj, encoding='utf-8', allow_unicode=True, default_flow_style=False)
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
    parser.add_argument(
        "-k", "--key", type=str, default="", help="Specify a json key for the translations"
    )
    args = parser.parse_args()
    main(args.source, args.trim, args.dest, args.prefix, args.key)
