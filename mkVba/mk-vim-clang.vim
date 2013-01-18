"=============================================================================
" File:         mkVba/mk-vim-clang.vim                            {{{1
" Author:       Luc Hermitte <EMAIL:hermitte {at} free {dot} fr>
"		<URL:http://code.google.com/p/lh-vim/>
" Version:      001
" Created:      18th Jan 2013
" Last Update:  $Date$
"------------------------------------------------------------------------
" Description:                                                 {{{2
"       VBA builder script for vim-clang
"       Source this script to generate a vimball archive.
" 
" Copying:                                                     {{{2
"   Copyright 2013 Luc Hermitte
"
"    This program is free software: you can redistribute it and/or modify
"    it under the terms of the GNU General Public License as published by
"    the Free Software Foundation, either version 3 of the License, or
"    (at your option) any later version.
"
"    This program is distributed in the hope that it will be useful,
"    but WITHOUT ANY WARRANTY; without even the implied warranty of
"    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
"    GNU General Public License for more details.
"
"    You should have received a copy of the GNU General Public License
"    along with this program.  If not, see <http://www.gnu.org/licenses/>.
" 
"------------------------------------------------------------------------
" }}}1
"=============================================================================

let s:version = '0.0.1'
let s:project = 'vim-clang'
cd <sfile>:p:h
try 
  let save_rtp = &rtp
  let &rtp = expand('<sfile>:p:h:h').','.&rtp
  exe '36,$MkVimball! '.s:project.'-'.s:version
  set modifiable
  set buftype=
finally
  let &rtp = save_rtp
endtry
finish
COPYING
README.md
autoload/clang.vim
ftplugin/c/clang.vim
py/vimclang.py
vim-clang-addon.info.txt
"=============================================================================
" vim600: set fdm=marker:
