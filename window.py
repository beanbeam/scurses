import curses
import locale

class CursesWindow(object):
  def __init__(self, main, w_limit=None, h_limit=None, bg_color=0):
    self._cursor_visible = True
    self._w_limit = w_limit
    self._h_limit = h_limit
    locale.setlocale(locale.LC_ALL, '')
    curses.wrapper(lambda window: self._wrap(main, window, bg_color))

  def _wrap(self, main, window, bg_color):
    self._window = window
    self._window.bkgd(" ", curses.color_pair(bg_color))
    self.cursor_visible = False
    self.mouse_location = (0,0)
    curses.mousemask(1)
    try:
      main(self)
    except KeyboardInterrupt: pass # Exit cleanly on Ctrl-C

  def clear(self):
    self._window.clear()

  def refresh(self):
    if not self.cursor_visible:
      self._window.move(self._real_height-1, self._real_width-1)
    self._window.refresh()

  def draw_string(self, x, y, str, colorp=0, underline=False, bold=False):
    try:
      style = curses.color_pair(colorp)

      if bold:      style = style | curses.A_BOLD
      if underline: style = style | curses.A_UNDERLINE

      self._window.addstr(y, x, str, style)
    except curses.error: pass

  def read_key(self, flush_first=False):
    if flush_first:
      self.flush_input()
    key = self._window.getch()
    if key == curses.KEY_MOUSE:
      try:
        mouse = curses.getmouse()
        if mouse[4] & curses.BUTTON1_RELEASED:
          key = "MOUSE_1RELEASED"
        elif (mouse[4] & curses.BUTTON2_RELEASED        |
              mouse[4] & curses.BUTTON2_CLICKED         |
              mouse[4] & curses.BUTTON2_DOUBLE_CLICKED  |
              mouse[4] & curses.BUTTON2_TRIPLE_CLICKED  |
             mouse[4] & curses.BUTTON2_PRESSED):
          key = "MOUSE_SCROLL_DOWN"
        elif mouse[4] & curses.BUTTON3_RELEASED:
          key = "MOUSE_3RELEASED"
        elif (mouse[4] & curses.BUTTON4_RELEASED        |
              mouse[4] & curses.BUTTON4_CLICKED         |
              mouse[4] & curses.BUTTON4_DOUBLE_CLICKED  |
              mouse[4] & curses.BUTTON4_TRIPLE_CLICKED  |
              mouse[4] & curses.BUTTON4_PRESSED):
          key = "MOUSE_SCROLL_UP"
        else: key = "MOUSE_UNKNOWN"
        self.mouse_location = (mouse[1], mouse[2])
      except:
        key = "MOUSE_UNKNOWN"
    else:
      curses.ungetch(key)
      key = self._window.getkey()
      if key == "KEY_RESIZE": return "WINDOW_RESIZED"
    return key

  def flush_input(self):
    curses.flushinp()

  def sleep(self, sleepms):
    curses.napms(sleepms)

  # PROPERTIES
  ############
  @property
  def _real_width(self):
    return self._window.getmaxyx()[1]

  @property
  def _real_height(self):
    return self._window.getmaxyx()[0]

  @property
  def width(self):
    if self._w_limit is None:
      return self._real_width
    return min(self._real_width, self._w_limit)

  @property
  def height(self):
    if self._h_limit is None:
      return self._real_height
    return min(self._real_height, self._h_limit)

  @property
  def cursor_visible(self):
    return self._cursor_visible

  @cursor_visible.setter
  def cursor_visible(self, show):
    self._cursor_visible = show
    try:
      if show: curses.curs_set(1)
      else:    curses.curs_set(0)
    except: pass

  # CONVENIENCE FUNCTIONS
  #######################
  def draw_string_centered(self, y, str, colorp=0):
    midX = self.width/2
    self.draw_string(midX-(len(str)/2), y, str, colorp)

  def do_text_area(self, lines, title=None, x=0, y=0, w=None, h=None, main_color=0, bar_color=1):
    if w == None: w = self.width
    if h == None: h = self.height
    scroll_amt = 0
    max_scroll = max(0, len(lines)-h+1+(0 if title==None else 1))
    while True:
      for i in range(y if title==None else y+1, y+h-1):
        self.draw_string(x, i, " "*w, main_color)
      for i, l in enumerate(lines):
        if i >= scroll_amt and i < scroll_amt+h-1:
          self.draw_string(x, y-scroll_amt+i+(0 if title==None else 1), l[:w], main_color)

      # Header
      if not title == None:
        self.draw_string(x, y, " "*w, bar_color)
        self.draw_string_centered(y, title, bar_color)

      # Footer
      self.draw_string(x, y+h-1, " "*w, bar_color)
      self.draw_string_centered(y+h-1, "BACK - Space/Enter", bar_color)
      if max_scroll > 0:
        self.draw_string(x, y+h-1, "(%s/%s)" %(scroll_amt, max_scroll), bar_color)

      self.refresh()
      key = self.read_key()
      if key == "KEY_DOWN":
        scroll_amt = min(scroll_amt+1, max_scroll)
      elif key == "KEY_UP":
        scroll_amt = max(scroll_amt-1, 0)
      elif key in (" ", "\n"): break


  def draw_menu(self, top_y, options, selected, select_color, desel_color):
    for i, o in enumerate(options):
      y = (2*i) + top_y
      if selected == i: color = select_color
      else:             color = desel_color
      self.draw_string_centered(y, " "+o+" ", color)
    self.refresh()

  def do_menu(self, top_y, options, selected, select_color, desel_color, smart_jump=True, auto_enter=False, mouse_enter=True):
    typed = ""
    while True:
      self.draw_menu(top_y, options, selected, select_color, desel_color)
      key = self.read_key()
      if key == "KEY_DOWN":
        if not (0 <= selected < len(options)):
          selected = 0
        else:
          selected = (selected + 1) % len(options)
      elif key == "KEY_UP":
        if not (0 <= selected < len(options)):
          selected = len(options) - 1
        else:
          selected = (selected - 1) % len(options)
      elif (key in ("\n", "KEY_RIGHT")   and
            0 <= selected < len(options)):
        return selected
      elif key == "MOUSE_1RELEASED":
        mouse = self.mouse_location
        if mouse[1] in range(top_y, top_y+2*len(options), 2):
          clicked = (mouse[1] - top_y)/2
          label_length = len(options[clicked])+2
          minX = (self.width - label_length)/2
          if mouse[0] >= minX and mouse[0] < minX+label_length:
            selected = clicked
            if mouse_enter: return selected

      elif smart_jump and len(key) == 1:
        typed += key.lower()
        matches = []
        while True:
          matches = []
          for i, o in enumerate(options):
            if o.lower().startswith(typed): matches.append(i)
          # Throw away oldest character until we find a match
          if len(matches) == 0: typed = typed[1:]
          else: break

        # Single match found
        if len(matches) == 1 and auto_enter:
          selected = matches[0]
          if auto_enter: return selected

        # Multiple matches found
        elif len(typed) >= 1:
          jumpto = matches[0]
          for m in matches:
            if m > selected:
              jumpto = m
              break
          selected = jumpto
