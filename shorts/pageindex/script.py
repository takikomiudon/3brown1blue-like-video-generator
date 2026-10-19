"""PageIndex: a continuous, source-grounded schematic, timed to Japanese speech."""
from pathlib import Path
import json
from manim import *

config.frame_width = 9
config.frame_height = 16
config.frame_rate = 30
config.background_color = '#09121f'
ROOT = Path(__file__).resolve().parent
import os, sys
SKILL = Path(os.environ.get('SCIENCE_EXPLAINER_SKILL',
    ROOT.parent.parent / '.agents/skills/science-explainer'))
sys.path.insert(0, str(SKILL / 'scripts'))
from voicevox_audio import render_inputs, save_render, verify_project
TIMELINE = json.loads((ROOT / 'timeline.json').read_text())
FONT = 'Noto Sans CJK JP'
BG, INK, DIM = '#09121f', '#f1f5fc', '#9aacc1'
PANEL, BORDER = '#122236', '#334a63'
CYAN, ORANGE, GREEN = '#62d9ed', '#ffb777', '#8cdda7'
CX = -.22


def txt(s, size=32, color=INK, width=7.15):
    m = Text(s, font=FONT, font_size=size, color=color,
             line_spacing=.9, disable_ligatures=True)
    if m.width > width:
        m.scale_to_fit_width(width)
    return m.set_z_index(12)


def card(title, body='', width=3.0, height=1.7, color=BORDER, size=27):
    box = RoundedRectangle(width=width, height=height, corner_radius=.16,
                           stroke_color=color, stroke_width=2,
                           fill_color=PANEL, fill_opacity=1)
    if body:
        label = txt(title, size - 5, DIM, width - .32).move_to([0, height * .29, 0])
        content = txt(body, size, INK, width - .4).move_to([0, -.18, 0])
        return VGroup(box, label, content)
    return VGroup(box, txt(title, size, INK, width - .32))


def document():
    pages = VGroup(*[
        RoundedRectangle(width=3.8, height=4.0, corner_radius=.12,
                         stroke_color=BORDER, stroke_width=2,
                         fill_color=PANEL, fill_opacity=1).shift(RIGHT * k * .12 + UP * k * .10)
        for k in [2, 1, 0]
    ])
    lines = VGroup(*[Line([-1.35, .15 - i * .40, 0],
                         [1.3 if i % 2 == 0 else .65, .15 - i * .40, 0],
                         color=DIM, stroke_width=3, stroke_opacity=.5) for i in range(4)])
    return VGroup(pages, txt('決算資料', 38).move_to([0, 1.15, 0]), lines,
                  txt('PDF', 22, CYAN).move_to([0, -1.55, 0]))


class PageIndexShort(Scene):
    def render(self, preview=False):
        inputs = render_inputs(ROOT)
        self.voice = verify_project(ROOT)
        result = super().render(preview=preview)
        if not result and not config.dry_run and config.write_to_movie and not config.save_last_frame:
            save_render(ROOT, self.renderer.file_writer.movie_file_path, inputs)
        return result

    def header(self, content, color=INK):
        new = txt(content, 45, color).move_to([CX, 5.78, 0])
        if hasattr(self, 'heading'):
            self.play(ReplacementTransform(self.heading, new), run_time=.4)
        else:
            self.add(new)
        self.heading = new

    def begin(self, i, shot):
        self.next_section(shot)
        cue = TIMELINE[i]
        assert abs(self.time - cue['start']) < .04, (cue['id'], self.time, cue['start'])
        if hasattr(self, 'caption'):
            self.remove(self.caption)
        self.caption = txt(cue['caption'], 33).move_to([CX, -5.0, 0])
        self.add(self.caption)
        self.add_sound(str(ROOT / cue['audio']))
        self.cue, self.started, self.target = cue, self.time, cue['end']

    def at(self, kana, lead=.05):
        """Use the actual voice query's mora timing at selected semantic landmarks."""
        query = json.loads((ROOT / self.cue['audio']).with_suffix('.query.json').read_text())
        utterance, times, t = '', [], query['prePhonemeLength']
        for phrase in query['accent_phrases']:
            for mora in phrase['moras']:
                utterance += mora['text']
                times.extend([t / query['speedScale']] * len(mora['text']))
                t += (mora.get('consonant_length') or 0) + mora['vowel_length']
            if phrase.get('pause_mora'):
                t += phrase['pause_mora']['vowel_length']
        index = utterance.find(kana)
        if index < 0:
            raise ValueError(f'No spoken landmark {kana!r} in {utterance!r}')
        delay = self.started + times[index] - lead - self.time
        if delay > 1 / config.frame_rate:
            self.wait(delay)

    def finish(self):
        remain = self.target - self.time
        if remain < -.04:
            raise RuntimeError(f'{self.cue["id"]} exceeded speech contract by {-remain:.3f}s')
        if remain > .001:
            self.wait(remain)

    def construct(self):
        # Persistent protected overlays. No moving camera, no full-board resets.
        self.add(txt('PageIndex  /  AIの資料探しを図解', 19, CYAN).move_to([CX, 7.0, 0]))
        self.add(Line([-3.85, 4.95, 0], [3.4, 4.95, 0], color=BORDER, stroke_width=1))
        self.add(txt('架空の資料 / 仕組みの模式図', 18, DIM).move_to([CX, -6.55, 0]))
        self.add(txt('出典：VectifyAI / PageIndex 公式GitHub', 16, DIM).move_to([CX, -6.95, 0]))
        # manim-skill:element object_id=obj_question
        obj_question = card('質問', '利益が減った理由は？', 7.0, 1.05, size=31).move_to([CX, 3.98, 0])
        self.header('そのページ、\n本当に答え？')
        obj_report = document().move_to([CX, .2, 0])
        self.add(obj_report)

        # manim-skill:shot shot_id=shot_problem beat_id=0
        self.begin(0, 'shot_problem')
        self.play(FadeIn(obj_question, shift=DOWN * .15), run_time=.7)
        self.play(obj_report.animate.scale(.83).shift(LEFT * 1.7), run_time=.7)
        teaser = card('経営方針 p.8', '利益を伸ばす\nことを目指す', 3.1, 2.2, ORANGE, 29).move_to([1.55, .0, 0])
        self.play(TransformFromCopy(obj_report, teaser), run_time=.8)
        uncertainty = txt('目標 ≠ 減った理由', 32, ORANGE).move_to([CX, -2.75, 0])
        self.play(FadeIn(uncertainty, shift=UP * .15), run_time=.5)
        self.at('ペエジインデックス')
        self.header('探し方を変える。\nPageIndex')
        self.finish()

        # manim-skill:shot shot_id=shot_chunks beat_id=1
        self.begin(1, 'shot_chunks')
        self.header('文章を分けて、探す。')
        self.play(FadeOut(teaser), FadeOut(uncertainty),
                  obj_report.animate.scale(.62).move_to([CX, 2.2, 0]), run_time=.6)
        obj_chunks = VGroup(
            card('経営方針', '利益を\n伸ばす目標', 2.15, 1.85, ORANGE, 27),
            card('業績', '売上や\n費用の変化', 2.15, 1.85, BORDER, 27),
            card('会社概要', '事業の\n紹介', 2.15, 1.85, BORDER, 27),
        ).arrange(RIGHT, buff=.25).move_to([CX, -.65, 0])
        self.play(LaggedStart(*[TransformFromCopy(obj_report, c) for c in obj_chunks], lag_ratio=.18), run_time=1.4)
        search_label = txt('質問と意味が近い断片へ', 29, ORANGE).move_to([CX, -2.6, 0])
        self.play(FadeIn(search_label), run_time=.4)
        self.play(Circumscribe(obj_chunks[0], color=ORANGE, buff=.08), run_time=.9)
        rag_gloss = txt('RAG：資料を探して答える仕組み', 21, DIM).move_to([CX, -3.55, 0])
        self.play(FadeIn(rag_gloss), run_time=.4)
        self.finish()

        # manim-skill:shot shot_id=shot_mismatch beat_id=2
        self.begin(2, 'shot_mismatch')
        self.header('似ている。\nでも、答えではない。')
        self.play(obj_chunks[1].animate.fade(.7).scale(.6).move_to([-2.9, -.35, 0]),
                  obj_chunks[2].animate.fade(.7).scale(.6).move_to([2.6, -.35, 0]),
                  obj_chunks[0].animate.move_to([CX, -.35, 0]).scale(1.35),
                  FadeOut(search_label), FadeOut(rag_gloss),
                  obj_report.animate.scale(.6).move_to([-2.9, 2.4, 0]), run_time=.7)
        link = DashedLine([CX, 3.35, 0], [CX, 1.1, 0], color=ORANGE, dash_length=.12)
        self.play(Create(link), run_time=.7)
        self.at('モクヒョオ')
        mismatch = txt('「目標」から\n「理由」は分からない', 35, ORANGE).move_to([CX, -2.8, 0])
        self.play(FadeIn(mismatch, shift=UP * .1), run_time=.6)
        cross = Cross(stroke_color=ORANGE, stroke_width=6).scale(.22).move_to([CX, 2.18, 0])
        self.play(Create(cross), run_time=.45)
        self.finish()

        # manim-skill:shot shot_id=shot_structure beat_id=3
        self.begin(3, 'shot_structure')
        self.header('バラバラの断片から、\n章・節のツリーへ。')
        self.play(FadeOut(link), FadeOut(cross), FadeOut(mismatch), run_time=.3)
        root = card('決算資料', width=2.6, height=.85, size=30).move_to([CX, 2.58, 0])
        branches = VGroup(*[card(s, width=2.0, height=.85, size=26)
                                for s in ['経営方針', '業績', '会社概要']])
        branches.arrange(RIGHT, buff=.38).move_to([CX, .82, 0])
        self.play(ReplacementTransform(obj_report, root),
                  *[ReplacementTransform(a, b) for a, b in zip(obj_chunks, branches)], run_time=1.0)
        leaves = VGroup(card('売上', width=2.1, height=.85, size=27),
                        card('費用の分析', width=2.1, height=.85, size=27))
        leaves[0].move_to([CX - 1.55, -1.0, 0])
        leaves[1].move_to([CX + 1.55, -1.0, 0])
        edges = VGroup(*[Line(root.get_bottom(), b.get_top(), color=BORDER, stroke_width=2) for b in branches],
                       *[Line(branches[1].get_bottom(), l.get_top(), color=BORDER, stroke_width=2) for l in leaves])
        self.play(LaggedStart(*[Create(e) for e in edges], lag_ratio=.08),
                  FadeIn(leaves, shift=DOWN * .1), run_time=.9)
        summaries = VGroup(txt('方針と目標', 20, DIM).move_to(branches[0].get_center() + DOWN * .75),
                           txt('売上・費用の変化', 20, CYAN).move_to(branches[1].get_center() + UP * .67),
                           txt('事業の紹介', 20, DIM).move_to(branches[2].get_center() + DOWN * .75))
        self.play(FadeIn(summaries), run_time=.4)
        # manim-skill:element object_id=obj_tree
        obj_tree = VGroup(edges, root, branches, leaves, summaries)
        self.finish()

        # manim-skill:shot shot_id=shot_traverse beat_id=4
        self.begin(4, 'shot_traverse')
        self.header('読む場所を、AIが選ぶ。')
        obj_cursor = Dot(root.get_bottom(), radius=.11, color=CYAN).set_z_index(25)
        self.play(FadeIn(obj_cursor), root[0].animate.set_stroke(CYAN, 4), run_time=.4)
        self.at('ギョオセキ')
        self.play(obj_cursor.animate.move_to(branches[1].get_top()),
                  edges[1].animate.set_stroke(CYAN, 4), branches[1][0].animate.set_stroke(CYAN, 4), run_time=.65)
        self.at('ヒヨオ')
        self.play(obj_cursor.animate.move_to(leaves[1].get_top()),
                  edges[4].animate.set_stroke(CYAN, 4), leaves[1][0].animate.set_stroke(CYAN, 4), run_time=.65)
        locator = card('選んだ本文', '費用の分析  p.42', 4.7, 1.15, CYAN, 28).move_to([CX, -2.8, 0])
        self.at('ヨム')
        self.play(TransformFromCopy(leaves[1], locator), run_time=.65)
        self.finish()

        # manim-skill:shot shot_id=shot_evidence beat_id=5
        self.begin(5, 'shot_evidence')
        self.header('本文から、根拠へ。')
        self.play(FadeOut(locator), FadeOut(obj_cursor), obj_tree.animate.scale(.66).move_to([CX, 1.83, 0]), run_time=.6)
        obj_cost_page = card('本文：費用の分析 p.42', '物流費が増加\n↓\n営業利益が減少', 3.25, 3.15, CYAN, 30).move_to([-2.05, -1.3, 0])
        self.play(TransformFromCopy(leaves[1], obj_cost_page), run_time=.7)
        self.at('ソノペエジ')
        obj_answer = card('回答', '物流費の増加で\n利益が減少', 3.2, 2.25, GREEN, 28).move_to([1.55, -.95, 0])
        self.play(TransformFromCopy(obj_cost_page[2], obj_answer), run_time=.75)
        citation = txt('根拠  p.42', 30, GREEN).move_to([1.55, -2.72, 0])
        self.play(TransformFromCopy(obj_cost_page[1], citation), run_time=.6)
        connection = Arrow(obj_cost_page.get_right(), obj_answer.get_left(), buff=.04,
                           color=GREEN, stroke_width=3, max_tip_length_to_length_ratio=.3)
        self.play(GrowArrow(connection), run_time=.4)
        self.finish()

        # manim-skill:shot shot_id=shot_principle beat_id=6
        self.begin(6, 'shot_principle')
        self.header('構造をたどる、という検索。')
        self.play(Indicate(root, color=CYAN, scale_factor=1.05), run_time=.65)
        self.at('コオゾオ')
        self.play(Indicate(VGroup(edges[1], branches[1], edges[4], leaves[1]),
                           color=CYAN, scale_factor=1.04), run_time=1.0)
        badge = card('ベクトルDB不要', width=5.0, height=.7, color=CYAN, size=28).move_to([CX, -3.65, 0])
        self.at('ベクトル')
        self.play(FadeIn(badge, shift=UP * .1), run_time=.6)
        self.finish()

        # manim-skill:shot shot_id=shot_limits beat_id=7
        self.begin(7, 'shot_limits')
        self.header('万能ではない。\n使う資料で、確かめる。')
        self.play(FadeOut(badge), run_time=.3)
        checks = VGroup(*[card(s, width=2.1, height=.8, color=ORANGE, size=27)
                          for s in ['精度', '待ち時間', 'AIの費用']])
        checks.arrange(RIGHT, buff=.25).move_to([CX, -3.65, 0])
        for check, landmark in zip(checks, ['セエド', 'マチジカン', 'コスト']):
            self.at(landmark)
            self.play(FadeIn(check, shift=UP * .12), run_time=.4)
        self.finish()

        # manim-skill:shot shot_id=shot_payoff beat_id=8
        self.begin(8, 'shot_payoff')
        self.header('目次をたどって、\n根拠に届く。', CYAN)
        self.play(FadeOut(checks), run_time=.4)
        brand = txt('PageIndex', 52, CYAN).move_to([CX, -3.6, 0])
        self.play(FadeIn(brand, shift=UP * .1), run_time=.65)
        self.play(Circumscribe(VGroup(obj_answer, citation), color=GREEN, buff=.15), run_time=.9)
        self.finish()
        self.add(txt('音声：'+self.voice['credit'], 18, DIM).move_to([CX, -7.4, 0]))
        self.wait(2.5)
