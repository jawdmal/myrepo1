#!/usr/bin/env python
"""
Minesweeper with Tk GUI.

For extra fun, you can continue playing after you step on a mine ;-)

See EXERCISE.txt for a detailed exercise in adding a partial Artifical
Intellegence (single-square analisys) to this game.

Site: http://cben-hacks.sf.net/python/smartsweeper/
"""

__author__ = "Beni Cherniavsky-Paskin <cben@users.sf.net>"
__license__ = "Public Domain"


import random, sys, optparse

# defaults to 1000, recursive AI might need more (e.g. 40x40 game)
sys.setrecursionlimit(10000)

import tkinter as Tk


class MineSweeper(object):
    """
    The data structure and basic rules of the game.

    Representation note
    -------------------

    The traditional representation would be a 2D array of squares, with
    each square storing several fields: whether it's contains a mine,
    whether it's flagged, whether it's opened...

    Instead, we store each field separately for the whole board, as a
    set of (x,y) coordinate pairs:

    self._mines
        Set of all squares that contain mines.  Secret - no peeking please!

    self.neighbours[xy]
        Set of squares around `xy` (normally 8, less at the borders).

    self.opened
        Set of squares that have already been opened.
    
    self.flagged
        Set of all flagged squares.

    self.mines_near[xy]
        Defined only for squares you have opened.
        Number of mines around `xy`, or 'mine' if it was a mine.

    The beauty of this scheme is that it allows compact set
    operations, e.g. finding all closed unflagged neighbours of xy::

        self.neighbours[xy] - self.opened - self.flagged

    """

    def __init__(self, columns, rows, mines_density):
        self.columns = columns
        self.rows = rows

        # The whole board
        self.xys = set((x, y)
                       for x in range(self.columns)
                       for y in range(self.rows))
        
        # For each square, gives the set of its neighbours
        self.neighbours = {}
        for (x, y) in self.xys:
            self.neighbours[x, y] = set((nx, ny)
                                        # 3x3 area
                                        for nx in [x-1, x, x+1]
                                        for ny in [y-1, y, y+1]
                                        # except the center
                                        if (nx, ny) != (x, y)
                                        # don't go outside the board
                                        if (nx, ny) in self.xys)

        # Secret data:
        
        mines_number = int(mines_density * columns * rows)
        self._mines = set()
        while len(self._mines) < mines_number:
            self._mines.add((random.randrange(columns),
                             random.randrange(rows)))

        # Public data:
        
        self.empty_remaining = columns * rows - mines_number
        self.opened = set()
        # We don't look at flags, but they're nice for the player / AI.
        self.flagged = set()
        # mines_near[xy] will be populated when you open xy.
        # It it was a mine, it will be 'mine' instead of a number.
        self.mines_near = {}

    def open(self, xy):
        """Open a square.

        The square is added to `self.opened`.

        If you survive, the number of mines around xy is published in
        `self.mines_near[xy]`.

        If you die, the square is also added to `self.flagged`, and
        `self.mines_near[xy]` is set to 'mine' instead of a number.
        """
        if xy in self.opened:
            return
        
        self.opened.add(xy)
        if xy in self._mines:
            self.mines_near[xy] = 'mine'
            self.flag(xy)  # simplifies playing after death logic
            self.lose()
        else:
            self.mines_near[xy] = len(self.neighbours[xy] & self._mines)
            self.flagged.discard(xy)
            self.empty_remaining -= 1
            if self.empty_remaining <= 0:
                self.win()

    def flag(self, xy):
        """Flag a square."""
        self.flagged.add(xy)

    def win(self):
        died = len(self.opened & self._mines)
        if died:
            self.message("You won, after dying only %s times." % died)
        else:
            self.message("You are ALIVE AND VICTORIOUS :-)")

    def lose(self):
        self.message("YOU DIED; game is *not* over!")

    def message(self, string):
        """Show a message to the player."""
        print (string)


class MineSweeperGUI(MineSweeper):
    """
    GUI wrapper.

    Left/right-click calls .open() / flag();
    calling .open() and .flag() also updates GUI.
    """

    # See http://effbot.org/tkinterbook/ for good Tk docs.

    def __init__(self, *args, **kw):
        MineSweeper.__init__(self, *args, **kw)
        self.window = Tk.Tk()
        self.table = Tk.Frame(self.window)
        self.table.pack()
        self.squares = {}
        # Build buttons
        for xy in self.xys:
            self.squares[xy] = button = Tk.Button(self.table, padx=0, pady=0)
            column, row = xy
            # expand button to North, East, West, South
            button.grid(row=row, column=column, sticky="news")
            # We want the buttons to be square, with fixed size.
            # 25x25 seems to be enough.
            self.table.grid_columnconfigure(column, minsize=25)
            self.table.grid_rowconfigure(row, minsize=25)

            # needed to restore bg to default when unflagging
            self._default_button_bg = self.squares[xy].cget("bg")

            def clicked(xy=xy):
                self.open(xy)
            button.config(command=clicked)

            def right_clicked(widget, xy=xy):
                if xy not in self.flagged:
                    self.flag(xy)
                else:
                    # remove flag, but not from
                    if xy in self.opened and xy in self._mines:
                        return
                    self.flagged.remove(xy)
                    self.refresh(xy)
            button.bind("<Button-3>", right_clicked)

            self.refresh(xy)

    def refresh(self, xy):
        """Update GUI for given square."""
        button = self.squares[xy]

        text, fg, bg = self.text_fg_bg(xy)
        button.config(text=text, fg=fg, bg=bg)
        
        if xy in self.opened:
            button.config(relief=Tk.SUNKEN)

        if self.empty_remaining > 0:
            self.message("%d non-mines left to open" %
                         self.empty_remaining)

    def text_fg_bg(self, xy):
        """Helper for .refresh()."""

        if xy in self.opened:
            
            if xy in self._mines:
                return u'\N{SKULL AND CROSSBONES}', None, 'red'
                
            mn = self.mines_near[xy]
            if mn > 0:
                # "standard" minesweeper colors (I think?)
                fg = {1: 'blue', 2: 'dark green', 3: 'red',
                      4: 'dark blue', 5: 'dark red',
                      }.get(mn, 'black')
                return str(mn), fg, 'white'
            else:
                return ' ', None, 'white'

        # unopened
        if self.empty_remaining > 0:
            # during play
            if xy in self.flagged:
                return u'\N{BLACK FLAG}', None, 'yellow'
            else:
                return ' ', None, self._default_button_bg
        else:
            # after victory
            if xy in self.flagged:
                return u'\N{WHITE FLAG}', None, 'green'
            else:
                return ' ', None, 'green'

    def open(self, xy):
        super(MineSweeperGUI, self).open(xy)
        self.refresh(xy)

    def flag(self, xy):
        super(MineSweeperGUI, self).flag(xy)
        self.refresh(xy)

    def win(self):
        super(MineSweeperGUI, self).win()
        # change all unopened mines to victory state
        for xy in self._mines - self.opened:
            self.refresh(xy)

    def message(self, string):
        self.window.title(string)


def main(cls):
    """Parse command-line and run the specified class."""
    parser = optparse.OptionParser()
    parser.add_option('-c', '--columns', type="int", default=16)
    parser.add_option('-r', '--rows', type="int", default=16)
    parser.add_option('-m', '--mines-density', type="float", default=0.2,
                      help="percent of mines: 0.15 is trivial, 0.2 good [default], 0.25 hard")
    (options, args) = parser.parse_args()
    if args:
        parser.error("unexpected arguments: " + " ".join(args))
    
    game = cls(options.columns, options.rows, options.mines_density)
    game.window.mainloop()

if __name__ == '__main__':
    main(MineSweeperGUI)
