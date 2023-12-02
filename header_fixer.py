#!/usr/bin/env python3
"""
Run <cc> -E for every entry in a given compilation database. The output is a list of header files.

We attempt to remove the `-o <output>` arguments from the compile commands, so we don't overwrite anything. This is based on a very basic heuristic, use at your own risk, etc.

TODO: gracefully handle errors
TODO: skip processing for assembly files

NB: currently this picks up non-C files, so it treats comments in assembly files as preprocessor output. You may have to manually fix the output.

Suggested use:
$ ./header_fixer.py compile_commands.json > output # get include list
$ sed 's/^\.\///g' -i output               # remove ./ from beginning of lines
$ sort -u output > output_sorted           # remove duplicate entries

$ cd /path/to/source/dir                   # ensure you're in right dir
$ while read FILE; do                      # check all entries are real files
    if [ ! -f $FILE ]; then echo "invalid: $FILE"; fi;
$ done<output_sorted
$ vim output_sorted                        # remove invalid entries
"""

import json, subprocess, os, logging

log = logging.getLogger("header_fixer")
logging.basicConfig(level=logging.DEBUG)

# compile_commands can have either a 'command' string, or 'arguments' as an array
NewType = 0xDEAD
OldType = 0xBEEF


def compile_version(input_json):
    if "arguments" in input_json[0] and "command" not in input_json[0]:
        return NewType
    if "command" in input_json[0] and "arguments" not in input_json[0]:
        return OldType
    log.critical("Unexpected JSON type?")
    return -1


def load_compdb(filename):
    raw_data = open(filename).read()
    return json.loads(raw_data)


def process_includes(data):
    lines = data.split("\n")
    for line in lines:
        if line.startswith("#"):
            try:
                line_data = line.split(" ")
                inc_name = line_data[2]
                flags = line_data[3:]
                if "1" in flags:
                    if "/usr/" not in inc_name and inc_name[1] != "<":
                        print(inc_name.strip('"'))
            except:
                log.error(f"bad/unhandled line?: '{line}'")


def process_compdb(compdb, version):
    def process_new_cmd(cmd):
        new_cmd = ""
        skip_next = False
        for arg in cmd["arguments"]:
            if arg == "-o":
                skip_next = True
                continue
            if skip_next == False:
                new_cmd += arg + " "
            else:
                skip_next = False

        # snarf the data directly from stdout
        new_cmd += f" -E"

        chdir = None
        if "directory" in cmd:
            chdir = cmd["directory"]

        log.debug(f"will run '{new_cmd}' in directory '{chdir}'")

        ret = subprocess.run(new_cmd, shell=True, cwd=chdir, capture_output=True)
        if ret.returncode != 0:
            log.critical(f"Failed to run compiler! ret is {ret}. Everything is b0rk")
            exit(-1)

        process_includes(ret.stdout.decode("utf-8"))

    def process_old_cmd(cmd):
        cmd["arguments"] = cmd["command"].split(" ")
        process_new_cmd(cmd)

    if version == NewType:
        for cmd in compdb:
            process_new_cmd(cmd)
    else:
        for cmd in compdb:
            process_old_cmd(cmd)


def header_fix(args):
    compdb_filename = args[0]
    compdb_data = load_compdb(compdb_filename)
    version = compile_version(compdb_data)

    if version == NewType:
        log.info(f"{compdb_filename} has new-style data")
    else:
        log.info(f"{compdb_filename} has old-style data")

    process_compdb(compdb_data, version)


if __name__ == "__main__":
    from sys import argv as arguments

    header_fix(arguments[1:])
