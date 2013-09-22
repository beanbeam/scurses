import curses

BLACK   = curses.COLOR_BLACK
RED     = curses.COLOR_RED
GREEN   = curses.COLOR_GREEN
YELLOW  = curses.COLOR_YELLOW
BLUE    = curses.COLOR_BLUE
MAGENTA = curses.COLOR_MAGENTA
CYAN    = curses.COLOR_CYAN
WHITE   = curses.COLOR_WHITE
BROWN   = 88


def colors_supported(): return curses.COLORS
def pairs_supported(): return curses.COLOR_PAIRS
def init(pair_list):
  if len(pair_list) >= pairs_supported():
    raise Exception("Tried to initialize too many color pairs!")
  for i, pair in enumerate(pair_list):
    curses.init_pair(i+1, pair[0], pair[1])
