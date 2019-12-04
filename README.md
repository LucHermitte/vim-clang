# vim-clang [![Last release](https://img.shields.io/github/tag/LucHermitte/vim-clang.svg)](https://github.com/LucHermitte/vim-clang/releases) [![Project Stats](https://www.openhub.net/p/21020/widgets/project_thin_badge.gif)](https://www.openhub.net/p/21020)

Module to interact with libclang (and clang\_indexer DB) from Vim.

Features:
---------
* Provides an [API](doc/API.md) to request information about the symbol under
  the cursor for Vim.
* Inter-operates with clang\_indexer DB
    * Displays the references of the C++ symbol under the cursor with `<leader>r`
    * Displays the declaration(s) of the C++ symbol under the cursor with `<leader>d`
    * Displays the Subclasses of the C++ symbol under the cursor with `<leader>s`
    * Encapsulates the updating of clang\_indexer DB (which requires a project
      configuration compatible with BuildToolsWrappers format).

* Works with custom made installations of libclang, even:
    * when it's installed in a user specific directory instead of `/usr` or
      `/usr/local`,
    * or when the default library is not the usual default or your system (e.g.
      on Linux, I install clang to use libc++ by default instead or libstdc++).
* Licence compatible with code generation.
* Can directly be used as long as clang Python bindings are installed; IOW, no
  need to compile any other library.

Rationale:
----------

While code indexation is already taken care of by LSP servers and plugins like
[COC](https://github.com/neoclide/coc.nvim) when plugged with
[ccls](https://github.com/MaskRay/ccls/), or
[clangd](https://clang.llvm.org/extra/clangd/), the
[Language Server Protocol](https://github.com/Microsoft/language-server-protocol)
doesn't standardize any way to request information about the current code.

From v2 onward, vim-clang new objective is to help building features that need
information about the code. Typical examples are
[lh-cpp](https://github.com/LucHermitte/lh-cpp) following commands and
features that'll be greatly improved by C++ code parsing done by libclang,
instead of being done in pure vimscript:
- [X] [`:DOX`](https://github.com/LucHermitte/lh-cpp/blob/master/doc/Doxygen.md)
  that generates Doxygen comments
- [.] `:GOTOIMPL` that generates a function definition from its declaration
- [X] `:Override` that proposes functions from parent class(es) to override in
  current class.
- [X] `:Ancestors` that lists the parent classes of the current class, even
  from anywhere within a class definition
- [ ] `:Constructor` that defines new constructors or assignment operator based
  on parents and on fields.
    - will need to detect whether parents and fields are copyable, movable...
- [ ] [_switch-enum_](https://github.com/LucHermitte/lh-cpp/blob/master/doc/Enums.md)
  that expands a `switch`-snippet with all the values from an enumeration


Limitations:
------------

### Translation Units
The [inspection API](doc/API.md) provided from V2 can only analyse the current
translation unit. It has no way (1) to know about declarations made in other
translation units. While it should not pose any issues regarding base classes,
fields, functions..., it will not permit to know about other parts of code that
makes use of/references the symbol inspected.

(1) As of now, I won't plan to actively maintain clang-indexer anymore. Other
tools like COC+ccls/clangd/... already provide indexing. It's just that we may
not be able to know more :(

May be there is a way to request references to client code (with COC...), and
inspect the translation units it belongs to... This needs investigation.

### libclang limitations
Libclang has limitations. It only provides information that its maintainer have
needed elsewhere. That why there are projects like
[cppast](https://github.com/foonathan/cppast), or other tools based on
libtooling.

Along the information I've found missing, I've identified so far:
- If a type isn't known (missing include e.g.), libclang won't return symbols
  that depends on that type. This means:
    - it cannot be used to auto-import missing includes
    - it won't return parameters of unknown types
- It doesn't report how parameters are formatted, and thus whether newlines are
  used in between, information I'd need in `:GOTOIMPL`. (may be if we analyse
  tokens...?)

Workarounds:
- `get_arguments()` doesn't work on template functions. Hopefully there is a
  workaround: we can analyse _children_.
- The presence of `final` and `override` keywords can be found in the
  _children_.
- `explicit` constructors can be deduced: they are mono parameters constructors
  without the 'converting' flag.
- The true kind of a template function can be obtained with the
  `clang_getTemplateCursorKind` C function that has no binding in
  `clang.cindex`.

Installation Requirements:
-------------------------
* [Vim 8.0+](http://www.vim.org), compiled with python support,
* Python 3.x (actually, I'll try to support Python 2.7.x, but with no guaranties)
* [lh-vim-lib](http://github.com/LucHermitte/lh-vim), v4.7.1+
* libclang,
* libclang Python bindings,

Optional dependencies:

* [BuildToolsWrappers](http://github.com/LucHermitte/vim-build-tools-wrapper),
  to help detect compilation databases
* And for the clang\_indexer _deprecated_ features:
    * my fork of Michael Geddes' [buffer-menu](http://github.com/LucHermitte/lh-misc/blob/master/plugin/buffermenu.vim)
    * [clang\_indexer](https://github.com/LucHermitte/clang_indexer) if you wish to request information to it -- honestly, I'm using COC+ccls nowadays

With vim-addon-manager, just install `vim-clang`, and let VAM take care of
installing all the vim dependencies. You'll still have to install Vim, Python,
clang Python bindings, **and** optionally clang\_indexer by yourself.

Note: this script hasn't been registered yet to VAM addons list.

Options:
--------
* `g:clang_library_path` to force the version of `libclang.so` to use. By
  default, this library is searched in `$LD_LIBRARY_PATH`, then in `lib/`
  directories alongside `$PATH`.
* The options from clang\_complete apply regarding libclang configuration
  (`[bg]:clang_user_options` that defines how to use libclang)
* `[bg]:_[{ft}_]_clic_filename` that tells where clang\_indexer database is
  located
* `(bpg):BTW.compilation_dir` to look for `compile_commands.json`

* `g:clang_key_usr`, `g:clang_key_declarations`, `g:clang_key_references`, and
  `g:clang_key_subclasses`, to override default choices to trigger vim-clang
  features.

To do list:
-----------
* Interface _à la_ `taglist()`
* Reimplements features from lh-dev and `lh-cpp#analysisLib*`.
* Add unit tests
* Use `$CFLAGS` and `$CXXFLAGS` when there is no compilation database
* Have the system includes be compatible with the `-stdlib` specified, if any

Alternative Solutions:
----------------------
* [libclang-vim](https://github.com/libclang-vim/libclang-vim), which requires
  to compiles a C++ library
* [cppast](https://github.com/foonathan/cppast), which also requires to
  compiles a C++ library. However it's meant to provide more and better results
  than the limited libclang.

  Note: cppast is just an alternative solution to libclang, it doesn't provide
  any Python binding, nor Vim bindings.

Disclaimer:
-----------
This module used to be a fork of @exclipy's fork of
[clang\_complete](<https://github.com/exclipy/clang_complete>).
The functions dedicated to the interaction with clang\_indexer have been extracted,
and a few more have been added.


Licence:
--------
`getReferences()` and `getCurrentUsr()` functions are courtesy of exclipy.

Copyright 2013-2019 Luc Hermitte

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
