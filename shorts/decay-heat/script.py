"""Reproducible portrait explainer. Frame timing is measured from speech."""
from pathlib import Path
import json
from manim import *
config.frame_width=9
config.frame_height=16
config.background_color='#080f1b'
config.frame_rate=30
ROOT=Path(__file__).resolve().parent
TIMELINE=json.loads((ROOT/'timeline.json').read_text())
FONT='Noto Sans CJK JP'
BG,INK,DIM='#080f1b','#f2f5fb','#91a4b9'
CYAN,ORANGE,RED,PURPLE,STEEL='#65d8f0','#ffb15d','#ff6c69','#c89bfa','#b0c2d8'
CX=-.25

def text(s,size=32,color=INK,max_width=7.4):
    m=Text(s,font=FONT,font_size=size,color=color,line_spacing=.85,disable_ligatures=True)
    if m.width>max_width:m.scale_to_fit_width(max_width)
    return m.set_z_index(30)

def nucleus(radius=.55,variant=0):
    dots=VGroup()
    for i in range(19):
        r=radius*.8*np.sqrt(i/19);a=i*2.39996
        dots.add(Dot([r*np.cos(a),r*np.sin(a),0],radius=radius*.16,color=ORANGE if (i+variant)%2 else PURPLE))
    return VGroup(Circle(radius=radius,stroke_color=ORANGE,stroke_width=1.2,stroke_opacity=.3),dots)

def vessel():
    shell=RoundedRectangle(width=2.8,height=4.35,corner_radius=.7,stroke_color=STEEL,
        stroke_width=3,fill_color='#132134',fill_opacity=1)
    cap=Line([-1.05,2.05,0],[1.05,2.05,0],color=STEEL,stroke_width=2)
    fuel=VGroup(*[RoundedRectangle(width=.19,height=2.3,corner_radius=.06,
        fill_color=ORANGE,fill_opacity=1,stroke_width=0).move_to([x,-.25,0])
        for x in [-.83,-.42,0,.42,.83]])
    rods=VGroup(*[RoundedRectangle(width=.12,height=2.25,corner_radius=.03,
        fill_color=STEEL,fill_opacity=1,stroke_width=0).move_to([x,1.95,0])
        for x in [-.63,-.21,.21,.63]])
    glow=VGroup(*[RoundedRectangle(width=2.1+i*.14,height=2.75+i*.14,corner_radius=.3,
        stroke_color=ORANGE,stroke_width=6+i*4,stroke_opacity=.055*(4-i),fill_opacity=0)
        .move_to([0,-.2,0]) for i in range(4)])
    return VGroup(shell,cap,glow,fuel,rods)

def status(label,value,color,x):
    plate=RoundedRectangle(width=3.48,height=.92,corner_radius=.16,stroke_width=1,
        stroke_color='#2b3b50',fill_color='#101d2c',fill_opacity=1)
    return VGroup(plate,text(label,17,DIM).move_to([0,.21,0]),
        text(value,26,color).move_to([0,-.16,0])).move_to([x,3.68,0]).set_z_index(40)

class DecayHeatShort(Scene):
    def set_header(self,s):
        new=text(s,43,max_width=7.45).move_to([CX,5.78,0])
        if hasattr(self,'header'):self.play(ReplacementTransform(self.header,new),run_time=.4)
        else:self.add(new)
        self.header=new

    def set_status(self,chain,heat):
        new=VGroup(status('連鎖反応',chain,CYAN if chain!='停止' else DIM,-2.08),
            status('燃料の発熱',heat,ORANGE,1.55))
        if hasattr(self,'dashboard'):self.play(ReplacementTransform(self.dashboard,new),run_time=.3)
        else:self.add(new)
        self.dashboard=new

    def caption(self,s):
        if '\n' not in s and len(s)>17:
            split=s.rfind('、',0,17)+1
            if split<6:split=min(16,len(s)//2+1)
            s=s[:split]+'\n'+s[split:]
        if hasattr(self,'cap'):self.remove(self.cap)
        self.cap=text(s,32,max_width=7.05).move_to([CX,-4.7,0]);self.add(self.cap)

    def begin(self,i):
        cue=TIMELINE[i]
        if abs(self.time-cue['start'])>.04:raise RuntimeError(f"Timeline drift at {cue['id']}")
        self.caption(cue['caption']);self.add_sound(str(ROOT/cue['audio']))
        self.target_end=cue['end'];self.beat_start=self.time;self.current_cue=cue

    def wait_for_kana(self,kana,lead=0):
        query=json.loads((ROOT/self.current_cue['audio']).with_suffix('.query.json').read_text())
        utterance='';starts=[];t=query['prePhonemeLength']
        for phrase in query['accent_phrases']:
            for mora in phrase['moras']:
                utterance+=mora['text'];starts.extend([t/query['speedScale']]*len(mora['text']))
                t+=(mora.get('consonant_length') or 0)+mora['vowel_length']
            if phrase.get('pause_mora'):t+=phrase['pause_mora']['vowel_length']
        index=utterance.find(kana)
        if index<0:raise ValueError(f'Kana landmark not found: {kana}')
        remaining=self.beat_start+starts[index]-lead-self.time
        if remaining>1/config.frame_rate:self.wait(remaining)

    def finish(self):
        remain=self.target_end-self.time
        if remain<-.04:raise RuntimeError(f'Beat exceeded cue by {-remain:.3f}s')
        if remain>.001:self.wait(remain)

    def construct(self):
        self.clock=ValueTracker(0);self.clock.add_updater(lambda m,dt:m.increment_value(dt));self.add(self.clock)
        self.add(Line([-3.95,4.83,0],[3.4,4.83,0],stroke_color='#28384b',stroke_width=1))
        self.add(text('NUCLEAR / 仕組みを図で見る',17,CYAN).move_to([CX,7.05,0]))
        self.set_header('停止しても、\n熱は残る。');self.set_status('運転中','発生中')
        reactor=vessel().move_to([CX,.15,0]);self.add(reactor)
        particles=VGroup(*[Dot(radius=.045,color=CYAN) for _ in range(9)])
        def move_neutrons(group):
            for i,m in enumerate(group):
                t=self.clock.get_value()
                m.move_to([CX+.95*np.sin(t*(1.1+i*.05)+i*2),.05+1.2*np.cos(t*1.6+i),0])
        particles.add_updater(move_neutrons);self.add(particles)
        btn=VGroup(RoundedRectangle(width=3.4,height=.75,corner_radius=.16,
            fill_color=RED,fill_opacity=1,stroke_width=0),text('STOP / 停止',25,BG)).move_to([CX,-3.15,0])
        self.add(btn)
        # Stop the chain but preserve the same warm fuel.
        self.begin(0);self.wait_for_kana('オシマス',lead=.08)
        self.play(btn.animate.scale(.95),rate_func=there_and_back,run_time=.28)
        self.play(reactor[4].animate.shift(DOWN*1.65),FadeOut(particles),run_time=.8)
        particles.clear_updaters();self.set_status('停止','残っている');self.finish()
        self.begin(1);self.play(FadeOut(btn),run_time=.3)
        heat_label=text('発熱は、まだある',31,ORANGE).move_to([CX,-3.1,0])
        self.play(FadeIn(heat_label,shift=UP*.1),run_time=.7)
        self.play(reactor[2].animate.set_stroke(opacity=.2),rate_func=there_and_back,run_time=1.3);self.finish()
        # Fuel becomes a close view of a nucleus.
        self.begin(2);self.set_header('まず、熱の生まれ方。');self.set_status('停止前のしくみ','核分裂で発生')
        mini=reactor.copy().scale(.32).move_to([-2.9,2.2,0])
        self.play(Transform(reactor,mini),FadeOut(heat_label),run_time=.65)
        u235=nucleus(.65).move_to([CX,.5,0]);ulabel=text('ウランの原子核',26,DIM).move_to([CX,-.65,0])
        self.play(TransformFromCopy(reactor[3][2],u235),FadeIn(ulabel),run_time=.55)
        neutron=Dot([CX-2.8,.5,0],radius=.075,color=CYAN);self.add(neutron)
        self.play(neutron.animate.move_to(u235.get_center()),run_time=.55)
        fragments=VGroup(nucleus(.43).move_to([CX-1.25,.9,0]),nucleus(.48,1).move_to([CX+1.2,-.05,0]))
        sparks=VGroup(*[Dot(u235.get_center(),radius=.055,color=CYAN) for _ in range(3)]);self.remove(neutron)
        self.play(ReplacementTransform(u235,fragments),FadeOut(ulabel),
            *[s.animate.move_to([CX+2*np.cos(a),.5+1.5*np.sin(a),0]) for s,a in zip(sparks,[.4,2.1,4.6])],run_time=.8)
        self.play(FadeOut(sparks),run_time=.3);self.finish()
        # Absorption and chain interruption.
        self.begin(3);self.set_header('連鎖反応を、止める。')
        control=RoundedRectangle(width=.3,height=2.7,corner_radius=.08,fill_color=STEEL,
            fill_opacity=1,stroke_width=0).move_to([CX,1.4,0])
        ctl_label=text('制御棒',24,STEEL).next_to(control,UP,buff=.18)
        self.play(FadeIn(control,shift=DOWN*.4),FadeIn(ctl_label),run_time=.6)
        for j in range(2):
            n=Dot([CX-1.4,.25+j*.65,0],radius=.075,color=CYAN)
            line=DashedLine(n.get_center(),[CX+1.7,.25+j*.65,0],dash_length=.12,color=CYAN,stroke_opacity=.25)
            self.add(n,line);self.play(n.animate.move_to([CX-.17,.25+j*.65,0]),run_time=.42)
            self.play(FadeOut(n),line.animate.set_opacity(.08),run_time=.23);self.remove(line)
        self.set_status('停止','まだ残る');self.finish()
        # Fission products survive the shutdown.
        self.begin(4);self.set_header('燃料の中に、\n残るもの。')
        self.play(FadeOut(control),FadeOut(ctl_label),reactor.animate.fade(.65),run_time=.4)
        expanded=VGroup(nucleus(.7).move_to([CX-1.4,.65,0]),nucleus(.7,1).move_to([CX+1.3,.65,0]))
        self.play(ReplacementTransform(fragments,expanded),run_time=.8);fragments=expanded
        frag_label=text('核分裂でできた\n不安定な原子核',34,ORANGE).move_to([CX,-1.5,0])
        self.play(FadeIn(frag_label,shift=UP*.1),run_time=.7)
        self.play(Indicate(fragments,color=ORANGE,scale_factor=1.08),run_time=.9);self.finish()
        # Radioactive decay changes a nucleus; it is NOT a second fission.
        self.begin(5);self.set_header('連鎖とは別に、\n崩壊は続く。')
        unstable=fragments[0].copy()
        self.play(FadeOut(fragments),FadeOut(frag_label),unstable.animate.scale(2.1).move_to([CX,.7,0]),run_time=.65)
        name=text('不安定な核',28,ORANGE).move_to([CX,-1.05,0]);self.add(name)
        radiation=Dot(unstable.get_center(),radius=.07,color=ORANGE)
        ray=Line([CX,.7,0],[CX+2.6,1.8,0],color=ORANGE,stroke_width=3);self.add(radiation)
        newname=text('別の原子核へ',28,PURPLE).move_to(name)
        rlabel=text('放射線',23,ORANGE).move_to([CX+2,2.25,0])
        self.play(Transform(unstable,nucleus(1.47,1).move_to([CX,.7,0])),ReplacementTransform(name,newname),
            radiation.animate.move_to([CX+2.6,1.8,0]),Create(ray),FadeIn(rlabel),run_time=1.2)
        self.play(FadeOut(radiation),FadeOut(ray),run_time=.4);self.finish()
        self.begin(6);self.set_header('これが「崩壊熱」。')
        ring=Circle(radius=1.65,stroke_color=ORANGE,stroke_width=6).move_to(unstable)
        self.play(FadeOut(rlabel),Create(ring),run_time=.6)
        self.play(ring.animate.scale(1.55).set_stroke(opacity=0),run_time=1.2)
        heat_word=text('崩壊熱',61,ORANGE).move_to([CX,-2.05,0]);self.wait_for_kana('ホオカイネツ',lead=.1)
        self.play(TransformFromCopy(unstable,heat_word),run_time=.85);self.finish()
        # Qualitative plot: no plant-specific numeric prediction.
        self.begin(7);self.set_header('減っても、\nすぐには消えない。')
        self.play(FadeOut(unstable),FadeOut(newname),FadeOut(heat_word),FadeOut(ring),FadeOut(reactor),run_time=.3)
        axes=Axes(x_range=[0,4.5,1],y_range=[0,3.5,1],x_length=6.2,y_length=3.3,tips=False,
            axis_config={'color':DIM,'stroke_width':2,'include_ticks':False}).move_to([CX,-.05,0])
        curve=axes.plot(lambda x:3.05*np.exp(-.68*x),x_range=[0,4.2],color=ORANGE,stroke_width=5)
        labels=VGroup(text('発熱',23,DIM).next_to(axes.y_axis,UP,buff=.12),
            text('停止後の時間 →',23,DIM).next_to(axes.x_axis,DOWN,buff=.2),
            text('時間・量を再現しない模式図',18,DIM).move_to([CX,-2.6,0]))
        self.play(Create(axes),FadeIn(labels),run_time=.45);self.play(Create(curve),run_time=1.3)
        self.play(Flash(curve.get_end(),color=ORANGE,flash_radius=.18),run_time=.5);self.finish()
        # Return to the SAME fuel: a conceptual heat-removal circuit.
        self.begin(8);self.set_header('熱を、外へ運び出す。')
        self.play(FadeOut(axes),FadeOut(labels),FadeOut(curve),run_time=.3)
        restored=vessel().move_to([CX,.15,0]);restored[4].shift(DOWN*1.65)
        self.play(Transform(reactor,restored),run_time=.55)
        loop=RoundedRectangle(width=5.8,height=4.8,corner_radius=.65,stroke_color=CYAN,stroke_width=5).move_to([CX,0,0])
        flow=ValueTracker(1);beads=VGroup(*[Dot(radius=.065,color=CYAN) for _ in range(14)])
        loop_clock=ValueTracker(0);loop_clock.add_updater(lambda m,dt:m.increment_value(dt*flow.get_value()));self.add(loop_clock)
        def water(g):
            for i,m in enumerate(g):
                q=(loop_clock.get_value()*.14+i/14)%1
                m.move_to(loop.point_from_proportion(q));m.set_color(ORANGE if .1<q<.5 else CYAN)
        beads.add_updater(water)
        exchanger=RoundedRectangle(width=1.3,height=1.8,corner_radius=.2,fill_color='#0e2c3d',
            fill_opacity=1,stroke_color=CYAN,stroke_width=2).move_to([CX+2.9,0,0])
        extlabel=text('放熱先',21,CYAN).next_to(exchanger,DOWN,buff=.2)
        self.play(Create(loop),FadeIn(exchanger),FadeIn(extlabel),FadeIn(beads),run_time=.7)
        heat_route=Arrow([CX,.15,0],[CX+2.2,.15,0],color=ORANGE,buff=.1,stroke_width=4)
        self.play(GrowArrow(heat_route),run_time=.5);self.finish()
        self.begin(9);self.set_header('冷却が失われると…')
        self.play(flow.animate.set_value(0),beads.animate.set_opacity(.2),loop.animate.set_stroke(opacity=.2),
            heat_route.animate.set_opacity(.15),run_time=.8)
        caution=text('停止後も、過熱のおそれ',32,RED).move_to([CX,-3.15,0])
        hot=VGroup(*[RoundedRectangle(width=2.1+i*.17,height=3+i*.17,corner_radius=.3,
            stroke_width=9+i*3,stroke_color=RED,stroke_opacity=.15*(3-i)).move_to([CX,-.05,0]) for i in range(3)])
        self.play(FadeIn(hot),reactor[3].animate.set_color(RED),FadeIn(caution),run_time=1.4)
        self.play(Indicate(hot,color=RED,scale_factor=1.04),run_time=.8);self.finish()
        self.begin(10);self.set_header('止める。\nそして、冷やし続ける。')
        self.play(FadeOut(hot),FadeOut(caution),flow.animate.set_value(1),beads.animate.set_opacity(1),
            loop.animate.set_stroke(opacity=1),heat_route.animate.set_opacity(1),reactor[3].animate.set_color(ORANGE),run_time=.9)
        self.set_status('停止済み','冷却を続ける')
        conclusion=text('停止 ≠ 発熱ゼロ',40,ORANGE).move_to([CX,-3.15,0])
        self.play(FadeIn(conclusion,shift=UP*.12),run_time=.65);self.finish()
        self.begin(11);self.play(Circumscribe(conclusion,color=ORANGE,buff=.18),run_time=.8);self.finish()
        self.add(text('音声：VOICEVOX:青山龍星',17,DIM).move_to([CX,-6.1,0]),
            text('参考：OpenStax University Physics Vol.3\n図は機構を説明する概念図',15,DIM).move_to([CX,-6.7,0]))
        self.wait(2.5);beads.clear_updaters();loop_clock.clear_updaters();self.clock.clear_updaters()
