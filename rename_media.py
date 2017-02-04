#!/usr/bin/env python2

import argparse
import os
import re


OUTPUT_FORMAT = "%s - s%02de%02d.mkv"


def main(input_format, show_name, season, episode_start, work_dir, dry_run):
	input_re = re.compile(input_format)
	dir_files = os.listdir(work_dir)
	potential_files = []
	for f in dir_files:
		if input_re.match(f) is not None:
			potential_files.append(f)

	output_files = []
	episode_num = episode_start
	for f in sorted(potential_files):
		output_files.append((f, OUTPUT_FORMAT % (show_name, season, episode_num)))
		episode_num += 1

	for f in output_files:
		print "%s -> %s" % (f[0], f[1])
		if not dry_run:
			os.rename(f[0], f[1])
	

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('show_name', action='store')
	parser.add_argument('work_dir', action='store')
	parser.add_argument('--format', dest='input_format', action='store')
	parser.add_argument('--season', action='store', type=int)
	parser.add_argument('--episode_start', action='store', default=1, type=int)
	parser.add_argument('--dry-run', action='store_true')
	args = parser.parse_args()
	

	main(**vars(args))
