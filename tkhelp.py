"""tkhelp  -- tkinter general assistance module

(c) 2012  Lion Kimbro  -- place note here that LGPLs the code


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

remove_binding  -- remove ONE binding from a widget

print_hierarchy  -- print out the widget hierarchy from a widget

nmt  -- send web browser to documentation for widget or class
"""

import tkinter
import _tkinter


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
GUESS_TKPARSEDVARNAME = "GUESS_TKPARSEDVARNAME"
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
    elif isinstance(identifier, _tkinter.Tcl_Obj) and hasattr(identifier, "typename"):
        if identifier.typename == "parsedVarName":
            return GUESS_TKPARSEDVARNAME
    else:
        return GUESS_UNKNOWN


global_tk = None  # Call setup(...) to initialize

def setup(withdraw=True, title="tkinter"):
    """Establish the global Tk().
    
    Call this method first, before using tkinter.
    
    Returns True on successful setup.
    Returns False if it has already been setup before.
    
    withdraw:  -- set to False, to begin Tk with a window showing
    
    Did you withdraw by mistake?  It's okay, you can get it back:
      find(".").wm_deiconify()
    
    POSSIBLE:
    * scheduling=True  [turn on/off a schedule tracker]
    * fullscreen=False
    """
    global global_tk
    if global_tk is not None:
        return False
    global_tk = tkinter.Tk()
    global_tk.title(title)
    if withdraw:
        global_tk.withdraw()
    annotate_widget_classes()
    return True


def requires_setup():
    """Raise SetupNotCalled if setup hasn't been called."""
    if global_tk is None:
        raise SetupNotCalled()


def find_named(name, origin=None, throw=True, default=None):
    """find a widget by name, by searching the widget hierarchy
    
    name  -- string name of a widget
    
    origin  -- widget to begin search at (default: global Tk)
    
    throw  -- if True, raise ValueError on failure to find a widget
    
    default  -- if not throw, return this on failure
    
    Exceptions:
    * WidgetNotFound  -- no widget found
    """
    requires_setup()
    if origin is None:
        origin = global_tk
    return visit_widgets(origin, lambda w, d, p: w.winfo_name() == name,
                         activity=FIND_NODE)


def find(identifier=None, origin=None, throw=True, default=None):
    """find a widget, given an identifier
    
    identifier  -- may be one of several things:
        None:  -- returns the global Tk widget
        a widget:  -- returns the widget itself
        a path:  -- returns the widget at the path
        a name:  -- returns first widget found with the name
        a Tk id#:  -- returns the widget with the given #
    
    origin  -- where to start searching the widget hierarchy from;
               if None, search the entire widget tree, DFS, from the top
    
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
        return find_named(identifier, origin)
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


def remove_binding(identifier, seq, index=None, funcid=None):
    """Remove a single binding from a widget.
    
    Based on Michael Lange's solution, posted to the tkinter-discuss
    list, Fri, 11 May 2012 11:59:30 +0200, adapted for the tkhelp
    module.
    
    Raises:
    * IndexError  -- if index is out of range.
    * KeyError  -- if funcid is out of range.
    * ValueError  -- if neither index nor funcid specified.
    """
    def _funcid(binding):
        return binding.split()[1][3:]
    w = find(identifier)
    b = [x for x in w.bind(seq).splitlines() if x.strip()]
    if not index is None:
        binding = b[index]
        w.unbind(seq, _funcid(binding))
        b.remove(binding)
    elif funcid:
        binding = None
        for x in b:
            if _funcid(x) == funcid:
                binding = x
                b.remove(binding)
                w.unbind(seq, funcid)
                break
        if not binding:
            raise KeyError('Binding "%s" not defined.' % funcid)
    else:
        raise ValueError('No index or function id defined.')
    for x in b:
        w.bind(seq, '+'+x, 1)


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


def tcl(tcl_code):
    """Execute tcl code string directly & return the result.
    
    Note that you'll probably want to have performed setup WITHOUT withdraw.
    If it's too late, unwithdraw with:
      tkhelp.find(".").wm_deiconify()
    """
    requires_setup()
    return global_tk.tk.eval(tcl_code)


def annotate_widget_classes():
    """Annotate tkinter widget classes with NMT links."""
    for (classname, url) in [entry.split() for entry in """
Button http://infohost.nmt.edu/tcc/help/pubs/tkinter/button.html
Canvas http://infohost.nmt.edu/tcc/help/pubs/tkinter/canvas.html
Checkbutton http://infohost.nmt.edu/tcc/help/pubs/tkinter/checkbutton.html
Entry http://infohost.nmt.edu/tcc/help/pubs/tkinter/entry.html
Frame http://infohost.nmt.edu/tcc/help/pubs/tkinter/frame.html
Label http://infohost.nmt.edu/tcc/help/pubs/tkinter/label.html
LabelFrame http://infohost.nmt.edu/tcc/help/pubs/tkinter/labelframe.html
Listbox http://infohost.nmt.edu/tcc/help/pubs/tkinter/listbox.html
Menu http://infohost.nmt.edu/tcc/help/pubs/tkinter/menu.html
Menubutton http://infohost.nmt.edu/tcc/help/pubs/tkinter/menubutton.html
Message http://infohost.nmt.edu/tcc/help/pubs/tkinter/message.html
OptionMenu http://infohost.nmt.edu/tcc/help/pubs/tkinter/optionmenu.html
PanedWindow http://infohost.nmt.edu/tcc/help/pubs/tkinter/panedwindow.html
Radiobutton http://infohost.nmt.edu/tcc/help/pubs/tkinter/radiobutton.html
Scale http://infohost.nmt.edu/tcc/help/pubs/tkinter/scale.html
Scrollbar http://infohost.nmt.edu/tcc/help/pubs/tkinter/scrollbar.html
Spinbox http://infohost.nmt.edu/tcc/help/pubs/tkinter/spinbox.html
Text http://infohost.nmt.edu/tcc/help/pubs/tkinter/text.html
Toplevel http://infohost.nmt.edu/tcc/help/pubs/tkinter/toplevel.html
"""[1:-1].split("\n")]:
       getattr(tkinter, classname).nmt_url = url


def nmt(identifier=None):
    """Open New Mexico Tech Tkinter 8.4 Reference for an Object.
    
    The object can be:
    * a widget class,
    * an instance of a widget class,
    * an identifier that find(...) can use to resolve a widget
    
    In the future, this will also include many functions, such as
    (widget).bind.
    """
    import webbrowser
    if identifier is None:
        webbrowser.open("http://infohost.nmt.edu/tcc/help/pubs/tkinter/")
    elif hasattr(identifier, "nmt_url"):
       webbrowser.open(identifier.nmt_url)
    else:
       obj = find(identifier)
       if hasattr(obj, "nmt_url"):
           webbrowser.open(obj.nmt_url)
       else:
           raise ValueError(identifier)


def test_tree():
    """TO BE DELETED"""
    setup()
    f = tkinter.Toplevel(name="f")
    f.title(f)
    b = tkinter.Button(f, text="b", name="b")
    b.pack()

