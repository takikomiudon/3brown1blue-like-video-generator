"""Eight-second route-selection pilot using the production scene and voice guards."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from manim import *
from script import PageIndexShort, card, txt, CYAN, BORDER, DIM, ROOT


class PageIndexPilot(PageIndexShort):
    def construct(self):
        root = card('決算資料', width=3.3, height=.9).move_to([0, 2.6, 0])
        branch = card('業績', width=2.4, height=.9).move_to([0, .4, 0])
        leaf = card('費用の分析', width=3.1, height=.9).move_to([1.3, -2.0, 0])
        other = card('会社概要', width=2.6, height=.9).move_to([-2.1, -2.0, 0])
        links = VGroup(Line(root.get_bottom(), branch.get_top(), color=BORDER),
                       Line(branch.get_bottom(), leaf.get_top(), color=BORDER),
                       Line(branch.get_bottom(), other.get_top(), color=BORDER))
        cursor = Dot(root.get_center(), radius=.12, color=CYAN)
        self.add(root, branch, leaf, other, links, cursor)
        self.add(txt('章を選び、本文へ進む', 34).move_to([0, 4.5, 0]))
        self.add(txt('音声：'+self.voice['credit'], 18, DIM).move_to([0, -6.9, 0]))
        self.add_sound(str(ROOT/'audio/04-traverse.wav'))
        self.wait(.3)
        self.play(cursor.animate.move_to(branch.get_center()), run_time=2.1)
        self.play(branch[0].animate.set_stroke(CYAN), other.animate.set_opacity(.35), run_time=.8)
        self.play(cursor.animate.move_to(leaf.get_center()), run_time=2.1)
        self.play(leaf[0].animate.set_stroke(CYAN), run_time=.8)
        self.play(leaf.animate.scale(1.12), run_time=.8)
        self.wait(1.6)
