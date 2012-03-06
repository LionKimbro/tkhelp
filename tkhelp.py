"""tkhelp  -- tkinter general assistance module

(c) 2012  Lion Kimbro  -- place note here that LGPLs the code

some immediate goals:
* find a widget
* pretty print hierarchy of widgets
* pretty print information about individual widgets


Error  -- base exception
SetupNotCalled  -- exception when global_tk/setup required
WidgetNotFound  -- exception when widget not found

visit_tree  -- general function for visiting trees
visit_widgets  -- visit widgets tree

guess  -- utility fn; estimate type of tkinter value

setup  -- initialize; establish global Tk
requires_setup  -- raise exception if setup not called yet

find_named  -- find a widget in the tree by name
find  -- locate a widget by name, path, ID#, ...

wid  -- return widget ID for a widget
fullpath  -- return full path for a widget
name  -- return name for a widget
wclass  -- return widget class for a widget

widget_str  -- descriptive string for a widget

print_hierarchy  -- print out the widget hierarchy from a widget
"""

import tkinter


class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class SetupNotCalled(Error):
    """Exception raised when setup() required but not called."""

class WidgetNotFound(Error):
    """Exception raised when a widget cannot be found."""


VISIT_ALL = "VISIT_ALL"
FIND_NODE = "FIND_NODE"
FORM_PARATREE = "FORM_PARATREE"

def visit_tree(top, visit_fn, children_fn, activity=VISIT_ALL):
    """Visit every node of a tree, top-down, DFS.
    
    top  -- top node to call
    visit_fn  -- fn(node, depth, parent) -> result
      fn(node...)  -- the node visited
      fn(...depth...)  -- numerical depth from top
      fn(...parent)  -- parent node
    children_fn  -- fn(node) -> children of node
    activity  -- (read further)
    
    Behavior depends on the activity.
    
    VISIT_ALL:
      Call visit_fn(...) for all nodes;  Returns True.
    
    FIND_NODE:
      Return node for first node for which visit_fn(...) evaluates
      True.  If none do, returns None.
    
    FORM_PARATREE:
      Return a tree formed by the result of each call to
      visit_fn(...).  Nodes take the form:
        [result, child-1, child-2, ... child-n].
    """
    def recurse(node, depth, parent):
        result = visit_fn(node, depth, parent)
        if activity == VISIT_ALL:
            pass
        elif activity == FORM_PARATREE:
            forming_node = [result]
        elif activity == FIND_NODE:
            if result:
                return node
        else:
            raise ValueError(activity)
        for child in children_fn(node):
            result = recurse(child, depth+1, node)
            if activity == VISIT_ALL:
                pass
            elif activity == FORM_PARATREE:
                forming_node.append(result)
            elif activity == FIND_NODE:
                if result:
                    return result
            else:
                raise ValueError(activity)
        if activity == VISIT_ALL:
            return True
        elif activity == FIND_NODE:
            return None
        elif activity == FORM_PARATREE:
            return forming_node
        else:
            raise ValueError(activity)
    return recurse(top, 0, None)

def visit_widgets(top, visit_fn, activity=VISIT_ALL):
    """Visit widgets tree.
    
    top  -- identifier for widget (see: "find")
    visit_fn  -- fn(widget, depth, parent) to call for widget & children
    activity  -- (see visit_tree for details)
    """
    return visit_tree(find(top), visit_fn=visit_fn,
                      children_fn=lambda w: w.winfo_children(),
                      activity=activity)


GUESS_TKWIDGET = "GUESS_TKWIDGET"
GUESS_TKPATH = "GUESS_TKPATH"
GUESS_TKNAME = "GUESS_TKNAME"
GUESS_TKID = "GUESS_TKID"
GUESS_TKEVENT = "GUESS_TKEVENT"
GUESS_UNKNOWN = "GUESS_UNKNOWN"

def guess(identifier):
    """Identify type of a tkinter-related identifier.
    
    guess(button)  => GUESS_TKWIDGET
    guess(".foo")  => GUESS_TKPATH
    guess("foo")   => GUESS_TKNAME
    guess(435)     => GUESS_TKID
    guess([])      => GUESS_UNKNOWN
    """
    if isinstance(identifier, tkinter.Misc):
        return GUESS_TKWIDGET
    elif isinstance(identifier, tkinter.Event):
        return GUESS_TKEVENT
    elif isinstance(identifier, str):
        if "." in identifier:
            return GUESS_TKPATH
        else:
            return GUESS_TKNAME
    elif isinstance(identifier, int):
        return GUESS_TKID
    else:
        return GUESS_UNKNOWN


global_tk = None  # Call setup(...) to initialize

def setup(withdraw=True):
    """Establish the global Tk().
    
    Call this method first, before using tkinter.
    
    Returns True on successful setup.
    Returns False if it has already been setup before.
    
    withdraw:  -- set to False, to begin Tk with a window showing
    
    POSSIBLE:
    * in future, we might make option here to turn on/off scheduling
    * in future, we might want a fullscreen option here,
      though contradictory to withdraw.
    """
    global global_tk
    if global_tk is not None:
        return False
    global_tk = tkinter.Tk()
    if withdraw:
        global_tk.withdraw()
    return True


def requires_setup():
    """Raise SetupNotCalled if setup hasn't been called."""
    if global_tk is None:
        raise SetupNotCalled()


def find_named(name, start_widget=None, throw=True, default=None):
    """find a widget by name, by searching the widget hierarchy
    
    name  -- string name of a widget
    
    start_widget  -- widget to begin search at (default: global Tk)
    
    throw  -- if True, raise ValueError on failure to find a widget
    
    default  -- if not throw, return this on failure
    
    Exceptions:
    * WidgetNotFound  -- no widget found
    """
    requires_setup()
    if start_widget is None:
        start_widget = global_tk
    return visit_widgets(start_widget, lambda w, d, p: w.winfo_name() == name,
                         activity=FIND_NODE)


def find(identifier=None, throw=True, default=None):
    """find a widget, given an identifier
    
    identifier  -- may be one of several things:
        None:  -- returns the global Tk widget
        a widget:  -- returns the widget itself
        a path:  -- returns the widget at the path
        a name:  -- returns first widget found with the name
        a Tk id#:  -- returns the widget with the given #
    
    throw  -- if True, raise ValueError on failure to find a widget
    
    default  -- if not throw, return this on failure
    
    Exceptions:
    * WidgetNotFound  -- no widget found
    """
    requires_setup()
    if identifier is None:
        return global_tk
    t = guess(identifier)
    if t == GUESS_TKWIDGET:
        return identifier  # This function is idempotent.
    elif t == GUESS_TKPATH:
        try:
            return global_tk.nametowidget(identifier)
        except KeyError:
            raise WidgetNotFound
    elif t == GUESS_TKID:
        return global_tk.nametowidget(global_tk.winfo_pathname(identifier))
    elif t == GUESS_TKNAME:
        return find_named(identifier)
    else:
        raise WidgetNotFound(identifier)


def wid(identifier):
    """Return the widget ID for a widget."""
    w = find(identifier)
    return w.winfo_id()

def fullpath(identifier):
    """Return the full path for a widget."""
    requires_setup()
    _id = wid(identifier)
    return global_tk.winfo_pathname(_id)

def name(identifier):
    """Returns the name for a widget."""
    w = find(identifier)
    return w.winfo_name()

def wclass(identifier):
    """Returns the class for a widget."""
    w = find(identifier)
    return w.winfo_class()


def widget_str(identifier, incl_fullpath=True, incl_id=True, incl_class=True):
    """Display an identifying string for a widget.
    
    {name} [{id}] <{class}>
    
    identifier  -- the widget to display (see: "find")
    incl_fullpath  -- True: display full path to the widget
    incl_id  -- True: include ID# for widget
    incl_class  -- True: show the widget class
    
    TODO:  Would probably be better to make a formatting function out of
           this, with: %i for ID, %p for path, %n for name, %c for class,
           %d for dimensions, ...  (and what have you)
    """
    w = find(identifier)
    parts = [fullpath(w) if not incl_fullpath else name(w)]
    if incl_id:
        parts.append("[" + str(wid(w)) + "]")
    if incl_class:
        parts.append("<" + wclass(w) + ">")
    return " ".join(parts)


def print_hierarchy(top=None, highlight=None, widget_str=widget_str):
    """Print the hierarchy extending from a widget.
    
    top  -- identifier for topmost widget (see: "find")
    highlight  -- if a widget identifier
    
    All child widgets are shown in the hierarchy too.
    """
    def visit_fn(widget, depth, parent):
        spaces = "  "*depth
        content = spaces + widget_str(widget)
        if widget == highlight:
            content = "** {} **".format(content)
        else:
            content = "   {}   ".format(content)
        content = content.ljust(50)
        content = content + widget.winfo_geometry()
        print(content)
    highlight = find(highlight)
    visit_widgets(top, visit_fn)

hr = print_hierarchy  # Alias for quickly typing


def test_tree():
    """TO BE DELETED"""
    setup()
    f = tkinter.Toplevel(name="f")
    f.title(f)
    b = tkinter.Button(f, text="b", name="b")
    b.pack()

