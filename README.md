Run `<cc> -E` for every entry in a given compilation database. The output is a list of header files.

We attempt to remove the `-o <output>` arguments from the compile commands, so we don't overwrite anything. This is based on a very basic heuristic, use at your own risk, etc.

TODO:
- gracefully handle errors
- skip processing for assembly files

NB: currently this picks up non-C files, so it treats comments in assembly files as preprocessor output. You may have to manually fix the output.

Suggested use:
```text
$ ./header_fixer.py compile_commands.json > output # get include list
$ sed 's/^\.\///g' -i output               # remove ./ from beginning of lines
$ sort -u output > output_sorted           # remove duplicate entries

$ cd /path/to/source/dir                   # ensure you're in right dir
$ while read FILE; do                      # check all entries are real files
    if [ ! -f $FILE ]; then echo "invalid: $FILE"; fi;
$ done<output_sorted
$ vim output_sorted                        # remove invalid entries
```
