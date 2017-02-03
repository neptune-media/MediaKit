#!/usr/bin/env python2

import argparse
import enzyme
import sys

from datetime import timedelta


class Episode(object):
	def __init__(self, start_num, end_num, start_ch, end_ch, discard=False):
		self.start_num = start_num
		self.end_num = end_num
		self.start_chapter = start_ch
		self.end_chapter = end_ch
		self.discard = discard


def get_metadata(filename):
	with open(filename, 'rb') as f:
		return enzyme.MKV(f)


def enumerate_chapters(metadata):
	chapters = []
	i = 1
	for ch in metadata.chapters:
		ch.end = timedelta(microseconds=ch.end // 1000)
		chapters.append((i, ch))
		i += 1

	return chapters


def main(filename, output='output.mkv', end_episode_thresh=30, min_episode_length=1200, list_episodes=False,
	 iframes=None):
	metadata = get_metadata(filename)
	chapters = filter(lambda x: x[1].enabled, enumerate_chapters(metadata))

	episodes = []

	start_num = None
	start_chapter = None
	for num, ch in chapters:
		if start_num is None:
			start_num = num
			start_chapter = ch
		duration = ch.end - ch.start
		if duration.total_seconds() < end_episode_thresh:
			e = Episode(start_num, num, start_chapter, ch)
			if (ch.end - start_chapter.start).total_seconds() < min_episode_length:
				e.discard = True
			episodes.append(e)
			start_num = None

	if list_episodes:
		for ep in episodes:
			op = ' '
			if ep.discard:
				op = 'D'
			print "%s %s-%s" % (op, ep.start_chapter.start, ep.end_chapter.end)
	else:
		parts = []
		for ep in episodes:
			if ep.discard:
				continue
			parts.append("%s-%s" % (ep.start_chapter.start, ep.end_chapter.end))
	
		split = "parts:%s" % ','.join(parts)
		print "mkvmerge -o %s --split %s %s" % (output, split, filename)
if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('input', metavar='filename', action='store')
	parser.add_argument('--iframes', action='store', default=None, help='filename of I-Frame list')
	parser.add_argument('--list', action='store_true')
	parser.add_argument('--output', action='store')
	args = parser.parse_args()
	
	main(args.input, output=args.output, iframes=args.iframes, list_episodes=args.list)
