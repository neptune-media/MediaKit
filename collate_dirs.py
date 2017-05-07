#!/usr/bin/env python2

import argparse
import os

OUTPUT_FORMAT = "%s - s%02de%02d.mkv"


def find_files(input_prefix, root='.'):
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        curdir = dirpath.split(os.path.sep)[-1]
        if curdir.rsplit('-', 1)[0].strip() == input_prefix:
            for f in filenames:
                files.append(os.path.join(dirpath, f))
        else:
            to_remove = []
            for dir in dirnames:
                if dir.rsplit('-', 1)[0].strip() != input_prefix:
                    print "Removing %s" % dir
                    to_remove.append(dir)
            for dir in to_remove:
                dirnames.remove(dir)
    return files


def main(input_prefix, show_name, season, work_dir, dry_run=True):
    files = find_files(input_prefix, work_dir)
    output_dir = os.path.join(work_dir, input_prefix)

    output_files = []
    episode_num = 1
    for f in sorted(files):
        output_path = os.path.join(output_dir, OUTPUT_FORMAT % (show_name, season, episode_num))
        output_files.append((f, output_path))
        episode_num += 1

    if not os.path.isdir(output_dir):
        print "Creating output directory %s" % output_dir
        if not dry_run:
            os.mkdir(output_dir)

    for f in output_files:
        print "%s -> %s" % (f[0], f[1])
        if not dry_run:
            os.rename(f[0], f[1])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--show', dest='show_name', action='store')
    parser.add_argument('work_dir', action='store')
    parser.add_argument('--prefix', dest='input_prefix', action='store')
    parser.add_argument('--season', action='store', type=int)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    main(**vars(args))
