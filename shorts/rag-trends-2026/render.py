"""Manim CE: source-backed schematic operations, rather than animated slide titles.

RAG_EPISODE selects one of the ten story directories. RAG_PILOT=1 renders 8 seconds.
Each diagram exposes four distinct data/state changes. Narration drives their timing.
"""
from pathlib import Path
import json, os
import numpy as np
from manim import *

ROOT=Path(__file__).resolve().parent
SLUG=os.environ.get('RAG_EPISODE','01_graphrag')
EP=next(e for e in json.loads((ROOT/'episodes.json').read_text()) if e['slug']==SLUG)
SPECS=json.loads((ROOT/'diagrams.json').read_text())[SLUG]
config.frame_width=9;config.frame_height=16;config.frame_rate=24
config.background_color='#08111F'
FONT='Noto Sans CJK JP'
INK='#F2F6FF';DIM='#9AAFC8';BORDER='#34465F';PANEL='#112137'
ACCENT=EP['color'];GREEN='#68E4B0';RED='#FF829E';BLUE='#86B8FF'

def text(s,size=28,color=INK,width=7.25):
    obj=Text(s,font=FONT,font_size=size,color=color,line_spacing=.9,disable_ligatures=True)
    if obj.width>width:obj.scale_to_fit_width(width)
    return obj

def pos(x,y):return np.array([x,y,0.])

def box(label,x,y,w=2.25,h=.85,color=BORDER,size=26):
    shape=RoundedRectangle(width=w,height=h,corner_radius=.13,
       stroke_color=color,stroke_width=2,fill_color=PANEL,fill_opacity=1)
    words=text(label,size,width=w-.24)
    if words.height>h-.18:words.scale_to_fit_height(h-.18)
    return VGroup(shape,words).move_to(pos(x,y))

def link(a,b,color=BORDER):
    delta=b.get_center()-a.get_center()
    if abs(delta[1])>abs(delta[0]):
        p=a.get_bottom() if delta[1]<0 else a.get_top()
        q=b.get_top() if delta[1]<0 else b.get_bottom()
    else:
        p=a.get_right() if delta[0]>0 else a.get_left()
        q=b.get_left() if delta[0]>0 else b.get_right()
    return Arrow(p,q,buff=.10,stroke_width=3,color=color,
                 max_tip_length_to_length_ratio=.16)

def pulse_path(path,color=ACCENT):
    return ShowPassingFlash(path.copy().set_color(color).set_stroke(width=8),time_width=.8)

def transform_label(old,new,color=INK):
    return Transform(old,text(new,26,color,width=old.width+1).move_to(old))

class Diagrams:
    def __init__(self,spec):
        self.s=spec;self.group=VGroup();self.steps=[];self.descriptions=[]
        getattr(self,spec['mode'])()

    def keep(self,*objects):
        self.group.add(*objects);return objects[0] if len(objects)==1 else objects

    def step(self,meaning,fn):self.descriptions.append(meaning);self.steps.append(fn)

    def graph(self):
        s=self.s
        source=self.keep(box(s['input'],0,2.65,5.8,.8,ACCENT))
        nodes=[box(label,x,y,1.95,.85,ACCENT) for label,(x,y) in zip(
            s['nodes'],[(-2,1.1),(1.7,1.1),(-2,-.9),(1.7,-.9)])]
        edges=[link(nodes[a],nodes[b]) for a,b in [(0,1),(0,2),(1,3),(2,3)]]
        groupA=RoundedRectangle(width=2.55,height=3.25,corner_radius=.3,stroke_color=ACCENT,
            fill_color=ACCENT,fill_opacity=.055).move_to(pos(-2,.1))
        groupB=groupA.copy().move_to(pos(1.7,.1)).set_stroke(BLUE).set_fill(BLUE,.055)
        summary=box('集団の要約',0,-2.55,4,.85,GREEN)
        self.keep(*edges,*nodes,groupA,groupB,summary)
        for o in [*nodes,*edges,groupA,groupB,summary]:o.set_opacity(0)
        self.step('原文から実体を取り出す',lambda:[TransformFromCopy(source,n.set_opacity(1)) for n in nodes[:2]])
        self.step('実体と関係を結び、構造にする',lambda:[FadeIn(n.set_opacity(1)) for n in nodes[2:]]+[Create(e.set_opacity(1)) for e in edges])
        self.step('つながりの集団を見つける',lambda:[FadeIn(groupA.set_stroke(opacity=1).set_fill(opacity=.055)),FadeIn(groupB.set_stroke(opacity=1).set_fill(opacity=.055))])
        self.step('集団の情報を要約へ移す',lambda:[TransformFromCopy(VGroup(*nodes),summary.set_opacity(1))])

    def entities(self):
        s=self.s;source=self.keep(box(s['input'],0,2.7,6,.8,ACCENT))
        nodes=[box(l,x,y,1.95,.8,ACCENT) for l,(x,y) in zip(s['nodes'],[(-2,1.2),(1.7,1.2),(-2,-.35),(1.7,-.35)])]
        edges=[link(nodes[a],nodes[b]) for a,b in [(0,1),(0,2),(2,3)]]
        vectors=VGroup(box('実体の表現',-1.8,-2,2.8,.8,BLUE),box('関係の表現',1.55,-2,2.8,.8,BLUE))
        output=box('検索用の索引',0,-3.1,4,.65,GREEN,size=24)
        self.step('原文から実体を抽出',lambda:[TransformFromCopy(source,n) for n in nodes])
        self.step('実体どうしの関係を接続',lambda:[Create(e) for e in edges])
        self.step('実体と関係に検索用の表現を持たせる',lambda:[TransformFromCopy(VGroup(*nodes),vectors)])
        self.step('グラフと表現を検索に利用する',lambda:[TransformFromCopy(vectors,output)])
        self.keep(*nodes,*edges,vectors,output)

    def mutual(self):
        s=self.s;source=self.keep(box(s['input'],0,2.7,6,.8,ACCENT))
        nodes=[box(l,x,y,1.95,.8,ACCENT) for l,(x,y) in zip(s['nodes'],[(-2,1.1),(1.7,1.1),(-2,-.7),(1.7,-.7)])]
        edges=[link(nodes[a],nodes[b]) for a,b in [(0,1),(0,2),(1,3)]]
        back=[DoubleArrow(source.get_bottom(),n.get_top(),buff=.12,color=BLUE,stroke_width=3) for n in nodes[:2]]
        original=box('原文チャンクへの索引',0,-2.6,6,.85,GREEN)
        self.step('原文から知識を抽出',lambda:[TransformFromCopy(source,n) for n in nodes])
        self.step('知識の関係を整理',lambda:[Create(e) for e in edges])
        self.step('知識と原文を双方向に結ぶ',lambda:[Create(e) for e in back])
        self.step('整理した知識から原文を参照する',lambda:[TransformFromCopy(source,original),pulse_path(back[0],GREEN)])
        self.keep(*nodes,*edges,*back,original)

    def repair(self):
        source=self.keep(box('取得した文書',0,2.7,5.5,.85,ACCENT))
        evaluator=self.keep(box('検索結果の品質評価',0,1.0,5.5,.9,ACCENT))
        kept=box('必要な情報の抽出',-1.95,-.9,3,.9,GREEN)
        web=box('Webで追加取得',1.65,-.9,3,.9,BLUE)
        output=box('補正した根拠',0,-2.8,5,.8,GREEN)
        first=link(source,evaluator,ACCENT);a=link(evaluator,kept,GREEN);b=link(evaluator,web,BLUE)
        self.step('取得した結果を品質評価に渡す',lambda:[Create(first)])
        self.step('品質に応じて追加取得の必要性を判断',lambda:[evaluator[0].animate.set_stroke(RED,5),pulse_path(first,RED)])
        self.step('原文の抽出と追加のWeb検索へ分岐',lambda:[Create(a),Create(b),FadeIn(kept),FadeIn(web)])
        self.step('使う情報を集め直す',lambda:[TransformFromCopy(VGroup(kept,web),output)])
        self.keep(kept,web,output,first,a,b)

    def update(self):
        s=self.s
        nodes=[self.keep(box(l,x,y,1.95,.85,ACCENT)) for l,(x,y) in zip(s['nodes'],[(-2,1.3),(1.6,1.3),(-2,-.5),(1.6,-.5)])]
        edges=[self.keep(link(nodes[a],nodes[b])) for a,b in [(0,1),(0,2),(2,3)]]
        new=self.keep(box(s['input'],0,2.9,5.5,.75,GREEN))
        extra=box('新しい障害',0,-2.4,2.5,.85,GREEN)
        e1=link(nodes[2],extra,GREEN);e2=link(nodes[3],extra,GREEN)
        self.keep(extra,e1,e2);extra.set_opacity(0)
        self.step('新しい文書から知識を抽出',lambda:[TransformFromCopy(new,extra.set_opacity(1))])
        self.step('既存の知識へ接続する',lambda:[Create(e1),pulse_path(edges[1])])
        self.step('対策との関係を追加',lambda:[Create(e2),nodes[3][0].animate.set_stroke(GREEN,4)])
        self.step('更新した知識を検索できる状態へ',lambda:[pulse_path(e1,GREEN),pulse_path(e2,GREEN),extra.animate.scale(1.12)])

    def retrieve(self):
        s=self.s;q=self.keep(box(s['input'],0,2.7,6.4,.9,ACCENT))
        docs=[self.keep(box(l,x,y,2.75,.85)) for l,(x,y) in zip(s['docs'],[(-1.85,1.0),(1.45,1.0),(-1.85,-.6),(1.45,-.6)])]
        result=box('取得した断片',0,-2.55,4,.85,ACCENT)
        paths=[link(q,d,ACCENT) for d in docs[:2]]
        self.step('質問に近い文章を選択',lambda:[d[0].animate.set_stroke(ACCENT,5) for d in docs[:2]])
        self.step('上位の候補へ検索が向かう',lambda:[Create(p) for p in paths])
        self.step('候補の情報を集める',lambda:[TransformFromCopy(VGroup(*docs[:2]),result)])
        self.step('取りこぼした資料を文脈として示す',lambda:[d.animate.set_opacity(.25) for d in docs[:2]]+[d[0].animate.set_stroke(RED,4) for d in docs[2:]])
        self.keep(*paths,result)

    def dual(self):
        s=self.s;q=self.keep(box(s['input'],0,2.65,6.5,.9,ACCENT))
        a=self.keep(box(s['left'],-2,.55,2.9,1.1,ACCENT));b=self.keep(box(s['right'],1.55,.55,2.9,1.1,BLUE))
        out=box(s.get('output','同じ質問の根拠を集める'),-.2,-2.5,6,.9,GREEN)
        left=link(q,a,ACCENT);right=link(q,b,BLUE)
        la=link(a,out,ACCENT);lb=link(b,out,BLUE)
        token=Dot(q.get_bottom(),radius=.14,color=INK)
        token2=token.copy()
        self.step('質問を二つの経路へ分ける',lambda:[Create(left),Create(right),FadeIn(token),FadeIn(token2)])
        self.step('二つの方式が別々に材料を探す',lambda:[MoveAlongPath(token,left),MoveAlongPath(token2,right)])
        self.step('それぞれの経路から根拠を渡す',lambda:[Create(la),Create(lb),FadeIn(out)])
        self.step('二つの経路の出力を照らし合わせる',lambda:[MoveAlongPath(token,la),MoveAlongPath(token2,lb),out[0].animate.set_stroke(GREEN,5)])
        self.keep(out,left,right,la,lb,token,token2)

    def tree(self):
        s=self.s
        leaves=[self.keep(box(l,x,-1.65,1.55,.8,size=23)) for l,x in zip(s['leaves'],[-2.8,-1,.8,2.6])]
        mids=[box('集約・要約',x,.25,2.4,.9,ACCENT) for x in [-1.9,1.7]]
        top=box('上位の要約',-.1,2.3,4,.9,GREEN)
        edges=[link(leaves[i],mids[i//2],ACCENT) for i in range(4)]
        upper=[link(m,top,GREEN) for m in mids]
        self.step('関連する原文をまとめる',lambda:[leaves[i].animate.shift((RIGHT if i%2==0 else LEFT)*.18) for i in range(4)])
        self.step('原文から中間の要約を作る',lambda:[Create(e) for e in edges]+[TransformFromCopy(VGroup(*leaves[2*i:2*i+2]),m) for i,m in enumerate(mids)])
        self.step('要約をさらにまとめる',lambda:[Create(e) for e in upper]+[TransformFromCopy(VGroup(*mids),top)])
        self.step('抽象度の異なる情報を検索の材料にする',lambda:[pulse_path(e,GREEN) for e in upper]+[leaves[0][0].animate.set_stroke(GREEN,4),top[0].animate.set_stroke(GREEN,5)])
        self.keep(*mids,top,*edges,*upper)

    def tree_search(self):
        s=self.s;leaves=[self.keep(box(l,x,-1.6,1.55,.8,size=23)) for l,x in zip(s['leaves'],[-2.8,-1,.8,2.6])]
        mids=[self.keep(box('中間要約',x,.25,2.4,.9,ACCENT)) for x in [-1.9,1.7]]
        top=self.keep(box('上位要約',-.1,2.3,3.7,.85,GREEN))
        edges=[self.keep(link(top,m)) for m in mids]+[self.keep(link(mids[i//2],l)) for i,l in enumerate(leaves)]
        token=Dot(top.get_center(),radius=.16,color=GREEN)
        self.step('上位の要約を参照',lambda:[FadeIn(token),top[0].animate.set_stroke(GREEN,5)])
        self.step('必要な中間の文脈へ向かう',lambda:[MoveAlongPath(token,edges[0]),edges[0].animate.set_color(GREEN)])
        self.step('細部の原文も取り出す',lambda:[MoveAlongPath(token,edges[3]),leaves[1][0].animate.set_stroke(GREEN,5)])
        self.step('細部と要約を同じ回答の材料に',lambda:[TransformFromCopy(leaves[1],box('原文 ＋ 要約',0,-3.0,5,.7,GREEN)),pulse_path(edges[0],GREEN)])
        self.keep(token)

    def gate(self):
        s=self.s;q=self.keep(box(s['input'],0,2.6,6.5,.85,ACCENT))
        tests=[self.keep(box(t,x,.8,2.9,1.0,ACCENT)) for t,x in zip(s['tests'],[-1.9,1.6])]
        yes=box('条件を満たす',-1.9,-1.3,2.9,.9,GREEN)
        no=box('不足・不適合',1.6,-1.3,2.9,.9,RED)
        a=link(q,tests[0],ACCENT);b=link(q,tests[1],ACCENT)
        pa=link(tests[0],yes,GREEN);pb=link(tests[1],no,RED)
        self.step('質問を条件の照合へ渡す',lambda:[Create(a),Create(b)])
        self.step('一つ目の条件を照合',lambda:[pulse_path(a),tests[0][0].animate.set_stroke(GREEN,5)])
        self.step('結果を条件ごとに分岐する',lambda:[Create(pa),Create(pb),FadeIn(yes),FadeIn(no)])
        self.step('不足がある経路では確認へ回す',lambda:[TransformFromCopy(no,box('確認・聞き返し',0,-3,5,.75,RED)),pulse_path(pb,RED)])
        self.keep(yes,no,a,b,pa,pb)

    def correction(self):
        s=self.s;q=self.keep(box(s['input'],0,2.6,6.4,.85,ACCENT))
        labels=s.get('docs',['候補A','候補B','候補C'])
        docs=[self.keep(box(t,x,.55,2.0,1.1)) for t,x in zip(labels,[-2.5,-.15,2.2])]
        accepted=box('確認した根拠',-1.7,-2.1,3,.9,GREEN)
        fresh=box('原文・追加情報',1.6,-2.1,3,.9,ACCENT)
        self.step('候補を評価に渡す',lambda:[Create(link(q,d,ACCENT)) for d in docs])
        self.step('問題のある候補を識別',lambda:[docs[1][0].animate.set_stroke(RED,5),docs[0][0].animate.set_stroke(GREEN,4)])
        self.step('不適切な候補を除外する',lambda:[docs[1].animate.scale(.65).shift(DOWN*.9).set_opacity(.2),TransformFromCopy(docs[0],accepted)])
        self.step('原文や追加の情報で補う',lambda:[TransformFromCopy(docs[2],fresh),Create(link(fresh,accepted,GREEN))])
        self.keep(accepted,fresh)

    def rank(self):
        self.keep(box(self.s['input'],0,2.8,6,.75,ACCENT))
        candidates=[self.keep(box(t,0,y,5.8,.8,GREEN if i==2 else BORDER)) for i,(t,y) in enumerate(zip(
            ['候補 A','候補 B','正しい根拠 C'],[1.4,.05,-1.3]))]
        self.step('検索された候補を収集',lambda:[c.animate.shift(RIGHT*.2) for c in candidates])
        self.step('質問と候補の組を再評価',lambda:[candidates[2][0].animate.set_stroke(GREEN,6),candidates[0][0].animate.set_stroke(RED,3)])
        self.step('正しい根拠の順位が変わる例',lambda:[candidates[2].animate.move_to(pos(.2,1.4)),candidates[0].animate.move_to(pos(.2,-1.3))])
        self.step('並べ替え後の上位を回答へ渡す',lambda:[TransformFromCopy(candidates[2],box('回答に使う根拠',0,-2.9,5,.75,GREEN))])

    def page(self):
        title=self.keep(box(self.s['input'],0,2.9,6.2,.7,ACCENT))
        page=RoundedRectangle(width=3.6,height=3.7,corner_radius=.12,stroke_color=INK,fill_color=PANEL,fill_opacity=1).move_to(pos(-1.55,.2))
        lines=VGroup(*[Line(pos(-2.9,1.3-i*.25),pos(-.3,1.3-i*.25),stroke_color=DIM,stroke_width=2) for i in range(3)])
        table=VGroup(*[Rectangle(width=.68,height=.38,stroke_width=1,stroke_color=ACCENT).move_to(pos(-2.5+c*.68,.1-r*.38)) for r in range(3) for c in range(3)])
        vectors=VGroup(*[Rectangle(width=.35,height=.5,stroke_width=1,stroke_color=ACCENT,fill_color=ACCENT,fill_opacity=.1+i*.12).move_to(pos(.9+(i%3)*.44,.7-(i//3)*.8)) for i in range(6)])
        pagegroup=self.keep(VGroup(page,lines,table))
        query=box('質問',1.6,-1.6,2,.75,GREEN);selected=box('根拠のページ',0,-2.9,5,.75,GREEN)
        self.step('本文だけでなく図表の構造を示す',lambda:[table.animate.scale(1.12).set_stroke(GREEN,2)])
        self.step('ページ情報を索引の表現へ変換',lambda:[TransformFromCopy(pagegroup,vectors)])
        self.step('質問とページの情報を対応付け',lambda:[FadeIn(query),Create(link(query,vectors,GREEN))])
        self.step('一致するページを根拠として取得',lambda:[page.animate.set_stroke(GREEN,5),TransformFromCopy(pagegroup,selected)])
        self.keep(vectors,query,selected)

    def loop(self):
        s=self.s;q=self.keep(box(s['input'],0,2.8,6.5,.75,ACCENT))
        a=self.keep(box(s['steps'][0],-2,1,2.7,1.0,ACCENT))
        b=self.keep(box(s['steps'][1],1.55,1,2.7,1.0,BLUE))
        c=self.keep(box(s['steps'][2],-.2,-1.5,4,.95,GREEN))
        edges=[link(a,b,ACCENT),link(b,c,BLUE),link(c,a,GREEN)]
        token=Dot(a.get_center(),radius=.16,color=INK)
        self.step('最初の処理から次の段階へ渡す',lambda:[Create(edges[0]),FadeIn(token)])
        self.step('取得した材料を推論・評価へ渡す',lambda:[MoveAlongPath(token,edges[0]),Create(edges[1])])
        self.step('次の行動に必要な状態を作る',lambda:[MoveAlongPath(token,edges[1]),Create(edges[2]),c[0].animate.set_stroke(GREEN,5)])
        self.step('結果を使って次の処理へ戻る',lambda:[MoveAlongPath(token,edges[2]),TransformFromCopy(c,box('次の状態へ',0,-3.0,4.5,.75,GREEN))])
        self.keep(*edges,token)

    def pipeline(self):
        s=self.s;title=self.keep(box(s['input'],0,2.8,6,.75,ACCENT))
        boxes=[self.keep(box(l,0,y,5.5,.9,ACCENT if i==0 else BORDER)) for i,(l,y) in enumerate(zip(s['labels'],[1.25,-.35,-1.95]))]
        edges=[link(boxes[i],boxes[i+1],ACCENT) for i in range(2)]
        token=Dot(boxes[0].get_center(),radius=.16,color=GREEN)
        self.step('入力を最初の部品へ渡す',lambda:[Create(link(title,boxes[0],ACCENT)),FadeIn(token)])
        self.step('一つ目の出力を次の部品へ渡す',lambda:[Create(edges[0]),MoveAlongPath(token,edges[0])])
        self.step('部品を接続して出力を得る',lambda:[Create(edges[1]),MoveAlongPath(token,edges[1])])
        self.step('出力を根拠とともに確認する',lambda:[boxes[-1][0].animate.set_stroke(GREEN,5),TransformFromCopy(token,box('出力を確認',0,-3.05,4.5,.65,GREEN,size=24))])
        self.keep(*edges,token)

    def multi(self):
        s=self.s;q=self.keep(box(s['input'],0,2.8,6.3,.8,ACCENT))
        nodes=[self.keep(box(l,x,.5,2.05,1.2,ACCENT if i!=1 else BLUE,size=24)) for i,(l,x) in enumerate(zip(s['labels'],[-2.5,-.15,2.2]))]
        paths=[link(q,n,ACCENT) for n in nodes]
        out=box('用途に合わせて選択・統合',0,-2.3,6,.9,GREEN)
        self.step('最初の表現・方式へ変換',lambda:[Create(paths[0]),nodes[0].animate.shift(UP*.12)])
        self.step('別の表現・方式も利用可能',lambda:[Create(paths[1]),nodes[1].animate.shift(UP*.12)])
        self.step('複数の候補を選択肢にする',lambda:[Create(paths[2]),nodes[2].animate.shift(UP*.12)])
        self.step('目的に合わせて出力を集める',lambda:[TransformFromCopy(VGroup(*nodes),out)])
        self.keep(*paths,out)

    def cost(self):
        s=self.s;q=self.keep(box(s['input'],0,2.8,6.3,.8,ACCENT))
        docs=[self.keep(box(f'文書 {i+1}',-2.3,1.25-i*1.4,2.0,.8)) for i in range(3)]
        stages=[self.keep(box(l,1.3,1.25-i*1.4,3.0,.8,ACCENT)) for i,l in enumerate(s['labels'])]
        self.step('文書から知識を抽出する処理が発生',lambda:[Create(link(docs[0],stages[0],ACCENT))])
        self.step('知識をグラフに整理する処理が発生',lambda:[TransformFromCopy(docs[1],stages[1]),Create(link(stages[0],stages[1],ACCENT))])
        self.step('要約を生成する処理も必要',lambda:[TransformFromCopy(docs[2],stages[2]),Create(link(stages[1],stages[2],ACCENT))])
        self.step('処理の積み重ねを索引の費用として検討',lambda:[TransformFromCopy(VGroup(*stages),box('索引作成の費用',0,-3,5,.75,RED))])

    def evaluate(self):
        s=self.s;self.keep(box(s['input'],0,2.8,6,.75,ACCENT))
        labels=['回答可能','回答不能','曖昧','文脈依存']
        ys=[1.65,.25,-1.15,-2.55]
        nodes=[self.keep(box(l,-1.9,y,2.8,.85)) for l,y in zip(labels,ys)]
        outcome=['回答する','保留する','聞き返す','文脈を参照']
        outputs=[box(l,1.6,y,2.8,.85,GREEN if i==0 else ACCENT) for i,(l,y) in enumerate(zip(outcome,ys))]
        for i in range(4):
            self.step(labels[i]+'の質問に対する行動を区別',lambda i=i:[
                nodes[i][0].animate.set_stroke(GREEN if i==0 else ACCENT,5),
                TransformFromCopy(nodes[i],outputs[i]),Create(link(nodes[i],outputs[i],ACCENT))])
        self.keep(*outputs)


class RagShort(Scene):
    def construct(self):
        pilot=os.environ.get('RAG_PILOT')=='1'
        if pilot:
            timeline=[{'id':'pilot','heading':EP['scenes'][1][0],'caption':EP['scenes'][1][1],
                       'start':0,'end':8,'duration':8}];specs=[SPECS[1]]
        else:
            timeline=json.loads((ROOT/SLUG/'timeline.json').read_text());specs=SPECS
        self.add(text('RAG FIELD NOTES',22,ACCENT).move_to(pos(-1.8,7.05)))
        self.add(text(SLUG[:2]+' / 10',21,DIM).move_to(pos(2.75,7.05)))
        self.add(text(EP['title'],47,INK).move_to(pos(-.2,6.25)))
        self.add(text(EP['tag'],18,DIM).move_to(pos(-.2,5.7)))
        self.add(Line(pos(-3.9,5.25),pos(3.5,5.25),color=BORDER,stroke_width=1))
        self.add(text('出典：付属の台本・一次資料リンク',18,DIM).move_to(pos(-.2,-6.85)))
        self.add(text('音声：VOICEVOX:青山龍星',18,DIM).move_to(pos(-.2,-7.25)))
        plan={'roi':[.065,.275,.835,.43],'beats':[],'holds':[]}
        previous=None
        for index,(cue,spec) in enumerate(zip(timeline,specs)):
            start=self.time
            header=text(cue['heading'],35,INK).move_to(pos(-.2,4.6))
            caption=text(cue['caption'],28,ACCENT).move_to(pos(-.2,-3.95))
            note=text(spec['note'],17,DIM).move_to(pos(-.2,-6.35))
            result=text(spec['result'],25,INK).move_to(pos(-.2,-3.5))
            diagram=Diagrams(spec)
            # Newly built targets start off-scene; only the initial state is added here.
            # Initial members are those already meant to be present, selected by mode.
            initial_counts={'graph':1,'entities':1,'mutual':1,'repair':2,'update':8,'retrieve':5,'dual':3,'tree':4,
              'tree_search':13,'gate':3,'correction':4,'rank':4,'page':2,
              'loop':4,'pipeline':4,'multi':4,'cost':7,'evaluate':5}
            initial=VGroup(*list(diagram.group)[:initial_counts[spec['mode']]])
            if previous:
                self.remove(*previous)
            self.add(header,caption,note,result,initial)
            tracked_before=set(self.mobjects)
            for op,fn in enumerate(diagram.steps):
                animations=fn()
                target_frame=round((cue['start']+(op+1)*cue['duration']/4)*24)
                remaining_frames=target_frame-round(self.time*24)
                active_frames=max(1,round(remaining_frames*.72))
                self.play(*animations,run_time=active_frames/24,rate_func=smooth)
                hold_start=self.time
                hold_frames=target_frame-round(self.time*24)
                if hold_frames>0:self.wait(hold_frames/24)
                plan['holds'].append({'start':hold_start,'end':self.time,'kind':'read',
                      'reason':diagram.descriptions[op]+'：変化後の状態を読み取る'})
            plan['beats'].append({'id':cue['id'],'start':start,'end':self.time,'kind':'mechanism',
                'object':spec['mode']+'-diagram','before':'質問・文書・候補を初期状態に配置',
                'action':' / '.join(diagram.descriptions),'after':spec['result'],
                'meaning':spec['result']})
            # Everything introduced by animations belongs to this diagram and clears together.
            previous=[header,caption,note,result,initial]+list(set(self.mobjects)-tracked_before)
        if not pilot:
            tail=self.time
            self.wait((round((timeline[-1]['end']+2)*24)-round(self.time*24))/24)
            plan['beats'][-1]['end']=self.time
            plan['holds'].append({'start':tail,'end':self.time,'kind':'final','reason':'最終状態とクレジットを読む'})
            (ROOT/SLUG/'motion-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
