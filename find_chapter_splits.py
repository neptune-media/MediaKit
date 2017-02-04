#!/usr/bin/env python2

import argparse
import enzyme
import sys

from datetime import timedelta


class Episode(object):
	def __init__(self, start_ch, end_ch, discard=False):
		self.start_chapter = start_ch
		self.end_chapter = end_ch
		self.discard = discard


class EpisodeBuilder(object):
	def __init__(self, min_length, ending_chapter_threshold, min_chapters):
		self.start = None
		self.end = None
		self.num_chapters = 0
		self.min_length = min_length
		self.ending_chapter_threshold = ending_chapter_threshold
		self.min_chapters = min_chapters

	def add_chapter(self, ch):
		if self.start is None:
			self.start = ch

		self.end = ch
		self.num_chapters += 1

	def build(self, ignore_missing_end=False):

		# If we haven't met the minimum, don't return anything
		if self.num_chapters < self.min_chapters + 1:
			return None

		# Check if last chapter meets criteria for stopping
		if not ignore_missing_end and (self.end.end - self.end.start).total_seconds() > self.ending_chapter_threshold:
			return None

		duration = self.end.end - self.start.start
		e = Episode(self.start, self.end)

		# Discard episode if episode length is too short
		# (such as the ending bits for DVD credits, etc)
		if duration.total_seconds() < self.min_length:
			e.discard = True

		# Reset state to start a new episode
		self.start = self.end = None
		self.num_chapters = 0
		return e


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
	 iframe_filename=None, min_chapters=2):
	metadata = get_metadata(filename)
	chapters = filter(lambda x: x[1].enabled, enumerate_chapters(metadata))
	iframe_reader = None
	if iframe_filename:
		iframe_reader = IFrameSeeker(iframe_filename)

	episodes = []
	eBuilder = EpisodeBuilder(
		min_length=min_episode_length,
		ending_chapter_threshold=end_episode_thresh,
		min_chapters=min_chapters,
	)

	for num, ch in chapters:
		#print "Processing chapter length %s\t(offset @ %s)" % ((ch.end - ch.start).total_seconds(), ch.start)
		if iframe_reader and num < len(chapters):
			ch.start = iframe_reader.current()

		# Advance I-Frame pointer to just before end of chapter
		# Stops advance if at end of file
		while iframe_reader and iframe_reader.peek() is not None and ch.end > iframe_reader.peek():
			iframe_reader.next()

		# Adjust end of chapter to I-Frame
		if iframe_reader:
			ch.end = iframe_reader.current()

		# Add chapter and try to build episode
		eBuilder.add_chapter(ch)
		e = eBuilder.build()
		if e is not None:
			# Move to next I-Frame if one is available
			if iframe_reader and iframe_reader.peek() is not None:
				iframe_reader.next()
			episodes.append(e)

	# End of file, check if we found enough for another episode
	e = eBuilder.build(True)
	if e is not None:
		episodes.append(e)

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
