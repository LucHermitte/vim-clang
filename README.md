vim-clang
=========

Module to Interact with libclang (and clang\_indexer DB) from Vim.

[![Project Stats](https://www.openhub.net/p/21020/widgets/project_thin_badge.gif)](https://www.openhub.net/p/21020)

Features:
---------
* Inter-operates with clang\_indexer DB
* Displays the references of the C++ symbol under the cursor with \<leader\>r
* Displays the declaration(s) of the C++ symbol under the cursor with \<leader\>d
* Displays the Subclasses of the C++ symbol under the cursor with \<leader\>s
* Encapsulates the updating of clang\_indexer DB (which requires a project
  configuration compatible with BuildToolsWrappers format)

Installation Requirements:
-------------------------
* [Vim 7.3+](http://www.vim.org), compiled with python support
* Python 2.x
* [clang\_complete](https://github.com/Rip-Rip/clang_complete)
* [clang\_indexer](https://github.com/LucHermitte/clang_indexer)
* [lh-vim-lib](http://code.google.com/p/lh-vim/wiki/lhVimLib),
  [lh-dev](http://code.google.com/p/lh-vim/source/browse/dev/trunk/lh-dev-addon-info.txt)

Note: this module takes advantage of the following modules when they are
installed:
* [BuildToolsWrappers](http://code.google.com/p/lh-vim/source/browse/BTW/trunk/lh-build-tools-wrapper-addon-info.txt)
* my fork of Michael Geddes' [buffer-menu](http://code.google.com/p/lh-vim/source/browse/misc/trunk/plugin/buffermenu.vim)

With vim-addon-manager, just install vim-clang, and let VAM take care of
installing all the vim dependencies. You'll still have to install Vim, Python,
**and** clang\_indexer by yourself.

Note: this script hasn't been registered yet to VAM addons list.

Options:
--------
* The options from clang\_complete apply regarding libclang configuration
  ([bg]:clang\_user\_options that defines how to use libclang)
* [bg]:_[{ft}\_]_clic\_filename that tells where clang\_indexer database is
  located

* g:clang\_key\_usr, g:clang\_key\_declarations, g:clang\_key\_references, and
  g:clang\_key\_subclasses, to override default choices to trigger vim-clang
  features.

To do list:
-----------
* Interface _à la_ taglist()
* Reimplements features from lh-dev and lh-cpp#analysisLib\*.


Disclaimer:
-----------
This module is a fork of @exclipy's fork of
[clang\_complete](<https://github.com/exclipy/clang_complete>).
The functions dedicated to the interaction with clang\_indexer have been extracted,
and a few more will be added.


Licence:
--------
getReferences() and getCurrentUser() functions are courtesy of exclipy.

Copyright 2013 Luc Hermitte

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
