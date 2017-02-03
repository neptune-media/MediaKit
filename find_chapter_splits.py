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


def get_next_iframe(f):
	line = f.readline()
	if len(line) == 0:
		return None
	return timedelta(milliseconds=float(line.strip()))


def main(filename, output='output.mkv', end_episode_thresh=30, min_episode_length=1200, list_episodes=False,
	 iframe_filename=None):
	metadata = get_metadata(filename)
	chapters = filter(lambda x: x[1].enabled, enumerate_chapters(metadata))
	iframe_file = None
	if iframe_filename:
		iframe_file = open(iframe_filename, 'rb')

	episodes = []
	if iframe_file:
		iframes = [get_next_iframe(iframe_file), get_next_iframe(iframe_file)]

	start_num = None
	start_chapter = None
	for num, ch in chapters:
		if start_num is None:
			start_num = num
			start_chapter = ch
			if iframe_file and num < len(chapters):
				start_chapter.start = iframes[0]

		while iframe_file and iframes[1] is not None and ch.end > iframes[1]:
			iframes.pop(0)
			iframes.append(get_next_iframe(iframe_file))
		duration = ch.end - ch.start
		if duration.total_seconds() < end_episode_thresh:
			if iframe_file and num < len(chapters):
				ch.end = iframes[0]
				if iframes[1] is not None:
					iframes.pop(0)
					iframes.append(get_next_iframe(iframe_file))
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
	
	main(args.input, output=args.output, iframe_filename=args.iframes, list_episodes=args.list)
