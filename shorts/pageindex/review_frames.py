"""Extract semantic review frames inside the same Docker render environment."""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
source = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT/'outputs/pageindex-short-ja.mp4'
cues = json.loads((ROOT/'timeline.json').read_text())
out = ROOT/'review-frames'
out.mkdir(exist_ok=True)
samples = []
for i, cue in enumerate(cues):
    seconds = cue['end'] - .35
    path = out/f'beat-{i:02}.jpg'
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(seconds),'-i',str(source),
                    '-frames:v','1','-q:v','2',str(path)],check=True)
    samples.append({'id':cue['id'],'seconds':seconds,'file':path.name})
subprocess.run(['ffmpeg','-v','error','-y','-framerate','1','-i',str(out/'beat-%02d.jpg'),
                '-vf','scale=360:640,tile=3x3','-frames:v','1',str(out/'contact-sheet.jpg')],check=True)
for cue in [cues[2], cues[3], cues[5]]:
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(cue['start']+1.1),'-i',str(source),
                    '-frames:v','1','-q:v','2',str(out/f'transition-{cue["id"]}.jpg')],check=True)
(out/'samples.json').write_text(json.dumps(samples,indent=2)+'\n')
print('Extracted 9 semantic landings and 3 transitions:',out)
