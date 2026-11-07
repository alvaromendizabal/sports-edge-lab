"""Keep displayed review pages neutral while preserving original data records."""
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[3]
ACTION=re.compile(r'\b(?:betting|wagers?|stakes?|paper)\b|NO BET',re.I)


class Visible(HTMLParser):
    def __init__(self):
        super().__init__();self.hidden=0;self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in ['script','style']:self.hidden+=1
    def handle_endtag(self,tag):
        if tag in ['script','style']:self.hidden-=1
    def handle_data(self,data):
        if not self.hidden:self.parts.append(data)


class PublicVocabularyTests(unittest.TestCase):
    def test_all_rendered_html_is_neutral(self):
        for path in (ROOT/'docs/fbs').glob('*.html'):
            with self.subTest(page=path.name):
                parser=Visible();parser.feed(path.read_text())
                self.assertIsNone(ACTION.search(' '.join(parser.parts)))

    def test_dynamic_legacy_messages_are_neutral(self):
        for name in ['season.js']:
            with self.subTest(script=name):
                self.assertIsNone(ACTION.search((ROOT/'docs/fbs'/name).read_text()))

    def test_dynamic_original_research_notes_are_neutral_only_at_display(self):
        source="const m=require('./docs/fbs/frontier.js'),d=require('./docs/fbs/frontier-review.json');for(const note of d.research.limitations){if(/\\b(?:betting|wagers?|stakes?|paper)\\b|NO BET/i.test(m.neutralResearchNote(note)))throw Error('Non-neutral rendered note');}"
        subprocess.run(['node','-e',source],cwd=ROOT,check=True,capture_output=True,text=True)
