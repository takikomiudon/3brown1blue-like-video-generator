"""Prepare narration with the saved user-selected VOICEVOX voice."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent
import os, sys
SKILL = Path(os.environ.get('SCIENCE_EXPLAINER_SKILL',
    ROOT.parent.parent / '.agents/skills/science-explainer'))
sys.path.insert(0, str(SKILL / 'scripts'))
from voicevox_audio import prepare_story

if __name__ == '__main__':
    prepare_story(ROOT)
