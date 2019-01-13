# deu.py “wort” -a -l
# -a: show all results (default max 3)
# —-linguee: use linguee instead of dictleo
# -it: translate from/to ita (default eng)
# -l: just show lemma instead of translation

# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
import argparse
import re
import urllib.request, urllib.parse
from bs4 import BeautifulSoup, SoupStrainer


class DictEntry(ABC):
	def __init__(self, query, lang, num_res):
		self.query = DictEntry.sanitize_query(query)
		self.lang = lang
		self.l = DictEntry.shorten_lang(lang)
		self.num_res = num_res
		self.transl_dict = self.translate()

	@staticmethod
	def sanitize_query(query):
		return urllib.parse.quote(query)

	@staticmethod
	def shorten_lang(lang):
		return "{}".format(lang[:2])

	@abstractmethod
	def get_page(self, url, strainer_filter):
		try:
			raw = urllib.request.urlopen(url)
		except:
			print("\nNo entry found for '{}'\n".format(self.query))
			raise SystemExit(0)
		subselection = SoupStrainer(strainer_filter)
		page = BeautifulSoup(raw.read(), "html.parser", parse_only=subselection)
		raw.close()
		return page

	@abstractmethod
	def translate(self):
		pass

	@abstractmethod
	def __str__(self):
		str = "\n"
		for d, t in zip(self.transl_dict["de"], self.transl_dict[self.l]):
			str += "{0:40} => {1}\n".format(d, t)
		return str

class LeoDictEntry(DictEntry):

	def get_page(self, url, strainer_filter):
		return super().get_page(url, strainer_filter)

	def translate(self):
		# Get HTML page, filtered by tags containing translations
		url = "https://dict.leo.org/{}-deutsch/{}".format(self.lang, self.query)
		strainer = lambda name, attrs: name == "td" and attrs.get("lang") in ("de", "en", "it")
		page = self.get_page(url, strainer)
		results_de = page.find_all("td", attrs={"lang":"de"}, limit=self.num_res)
		results_tr = page.find_all("td", attrs={"lang":self.l}, limit=self.num_res)

		# Construct dictionary for translation entries
		transl_dict = { "de": [], self.l: [] }
		for d, t in zip(results_de, results_tr):
			transl_dict["de"].append(d.get_text(" ", strip=True))
			transl_dict[self.l].append(t.get_text(" ", strip=True))

		# Check if the query is a verb, and if so append auxiliary verb to lemma
		ix_verbs = self.get_verb_indices(transl_dict["de"])
		if ix_verbs:
			self.add_hilfsverb(page, transl_dict["de"], ix_verbs[0])

		return transl_dict

	def get_verb_indices(self, de_list):
		lemma_pattern = re.compile("\|.*\|")
		ix = [ i for i in range(len(de_list)) if lemma_pattern.search(de_list[i]) != None ]
		return ix

	def add_hilfsverb(self, page, de_list, ix_verb):
		try:
			lemma = re.search("\|.*\|", de_list[ix_verb]).group(0)
			verb_tag = page.find("small", string=lemma)
			flect_link = verb_tag.find_parent("a").get("href")
			url = "https://dict.leo.org{}".format(flect_link)
			strainer = lambda name, attrs: name == "h3" and attrs.get("class") == "p bg-blue"
			flect_page = self.get_page(url, strainer)
			verb = flect_page.find().get_text().split()[1]
		except:
			verb = "?"
		de_list[ix_verb] += " ({})".format(verb)
		return de_list

	def __str__(self):
		return super().__str__()

class LingueeDictEntry(DictEntry):
	def get_page(self):
		pass
	def translate(self):
		pass
	def __str__(self):
		return super().__str__()


def main():
	parser = argparse.ArgumentParser(description='Traslate DEU<->ENG/ITA.')
	parser.add_argument('query')
	parser.add_argument('-a', dest='num_res', action='store_const',
						const=20, default=3, help='return all dict entries (default=3)')
	parser.add_argument('--ita', dest='lang', action='store_const',
						const="italienisch", default="englisch", help='translate to/from italian')
	parser.add_argument('--linguee', dest='use_linguee', action='store_true',
						help='use linguee instead of dicleo')
	args = parser.parse_args()

	if args.use_linguee:
		entry = LingueeDictEntry(args.query, args.lang, args.num_res)
		print("Linguee not implemented yet. Try with Dictleo!")
		return
	else:
		entry = LeoDictEntry(args.query, args.lang, args.num_res)
	print(entry)
	return


if __name__ == "__main__":
	main()
	raise SystemExit(0)
