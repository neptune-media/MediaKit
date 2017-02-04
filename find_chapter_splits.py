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


class IFrameSeeker(object):
	def __init__(self, filename):
		self._handle = open(filename, 'rb')
		self.iframes = [self._get_next_iframe(), self._get_next_iframe()]

	def next(self):
		self.iframes.pop(0)
		self.iframes.append(self._get_next_iframe())

	def current(self):
		return self.iframes[0]

	def peek(self):
		return self.iframes[1]

	def _get_next_iframe(self):
		line = self._handle.readline()
		if len(line) == 0:
			return None
		return timedelta(milliseconds=float(line.strip()))


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
	 iframe_filename=None, new_episode_grace=2):
	metadata = get_metadata(filename)
	chapters = filter(lambda x: x[1].enabled, enumerate_chapters(metadata))
	iframe_reader = None
	if iframe_filename:
		iframe_reader = IFrameSeeker(iframe_filename)

	episodes = []

	start_num = None
	start_chapter = None
	last_num = None
	last_chapter = None
	grace_remaining = new_episode_grace
	for num, ch in chapters:
		#print "Processing chapter length %s\t(offset @ %s)" % ((ch.end - ch.start).total_seconds(), ch.start)
		last_num = num
		last_chapter = ch
		grace_remaining -= 1
		if start_num is None:
			start_num = num
			start_chapter = ch
			if iframe_reader and num < len(chapters):
				start_chapter.start = iframe_reader.current()

		# Advance I-Frame pointer to just before end of chapter
		# Stops advance if at end of file
		while iframe_reader and iframe_reader.peek() is not None and ch.end > iframe_reader.peek():
			iframe_reader.next()
		duration = ch.end - ch.start

		# Tracks less than end_episode_thresh are considered the last chapter of the episode
		if grace_remaining < 0 and duration.total_seconds() < end_episode_thresh:
			if iframe_reader and num < len(chapters):
				# Adjust end of chapter to current I-frame
				ch.end = iframe_reader.current()

				# Move to next I-Frame if one is available
				if iframe_reader.peek() is not None:
					iframe_reader.next()
			e = Episode(start_num, num, start_chapter, ch)

			# If episode is less than min_episode_length, discard
			if (ch.end - start_chapter.start).total_seconds() < min_episode_length:
				e.discard = True
			episodes.append(e)
			start_num = None
			grace_remaining = new_episode_grace


	if start_num is not None and (last_chapter.end - start_chapter.start).total_seconds() > min_episode_length:
		episodes.append(Episode(start_num, last_num, start_chapter, last_chapter))

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
	parser.add_argument('--end-episode-thresh', action='store', default=30, type=int)
	args = parser.parse_args()
	
	main(args.input, output=args.output, iframe_filename=args.iframes, list_episodes=args.list,
	     end_episode_thresh=args.end_episode_thresh)
