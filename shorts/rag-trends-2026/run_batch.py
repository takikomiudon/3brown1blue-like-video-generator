"""Run local containers with networking disabled, then mux/verify final MP4s."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse, json, os, subprocess, time

ROOT=Path(__file__).resolve().parent
def render(slug):
    folder=ROOT/slug
    while not (folder/'timeline.json').exists():time.sleep(2)
    args=['docker','run','--rm','--network','none','--cpus','2',
      '--mount',f'type=bind,src={ROOT},dst=/manim',
      '--mount','type=bind,src=/usr/share/fonts/opentype/noto,dst=/usr/local/share/fonts/noto,readonly',
      '--user',f'{os.getuid()}:{os.getgid()}','-w','/manim',
      '-e','XDG_CACHE_HOME=/tmp/cache','-e','MPLCONFIGDIR=/tmp/matplotlib','-e',f'RAG_EPISODE={slug}',
      'decay-heat-manim:0.20.1','manim','-qh','-r','1080,1920','--fps','24','--disable_caching',
      '--media_dir',f'/manim/work/{slug}','render.py','RagShort']
    print('RENDER',slug,flush=True)
    with (folder/'outputs/render.log').open('w') as log:subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True)
    subprocess.run(['python',str(ROOT/'finish.py'),slug],check=True)
    subprocess.run(['python',str(ROOT/'finish.py'),slug,'--sheets'],check=True)
    print('READY FOR REVIEW',slug,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=2);ap.add_argument('--only',nargs='*');a=ap.parse_args()
    slugs=a.only or [e['slug'] for e in json.loads((ROOT/'episodes.json').read_text())]
    with ThreadPoolExecutor(max_workers=a.workers) as ex:list(ex.map(render,slugs))
