from .ParserC import *
from Redy.Tools.PathLib import Path
import os
from linq import Flow

RBNF_HOME = 'RBNF_HOME'
_root_dir = Path(__file__).parent()
home = Path(os.environ.get(RBNF_HOME, '~/.rbnf'))
if RBNF_HOME not in os.environ:
    os.environ[RBNF_HOME] = home.__str__()

if not home.exists():
    Flow(_root_dir.into('rbnf_libs').list_dir()).Each(lambda it: it.move_to(home))
