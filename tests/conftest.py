import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hn_radar.hn import Story


def make_story(**kw):
    defaults = dict(
        id="1", title="", url=None, points=0, num_comments=0,
        author="a", created_at_i=0, story_text=None, tags=[],
    )
    defaults.update(kw)
    return Story(**defaults)
