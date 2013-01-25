"=============================================================================
" File:         ftplugin/c/clang.vim                                    {{{1
" Author:       Luc Hermitte <EMAIL:hermitte {at} free {dot} fr>
"		<URL:https://github.com/LucHermitte/vim-clang>
" Version:      001
" Created:      10th Jan 2013
" Last Update:  $Date$
" License:      GPLv3 with exceptions
"               <URL:http://code.google.com/p/lh-vim/wiki/License>
"------------------------------------------------------------------------
" Description:                                                 {{{2
"       Minimum set of functions to integrate clang indexer with vim.
"       As clang_complete and clang_indexer follow two different paths,
"       maintaining a merged solution has become quite difficult hence this
"       minimal solution.
" 
"------------------------------------------------------------------------
" Installation:                                                {{{2
"       Requires: clang_indexer, Vim7+, python, clang_complete, lh-dev, lh-vim-lib
"       Optional: BTW
"       
"       Instead of g:clic_filename, this plugin uses, by order of preference:
"       1- b:clic_filename
"       2- g:clic_filename
"       3- {current_path}/.index.db
" History:                                                     {{{2
"       v0.0.1:
"               Main code extracted from clang_complete fork aimed at
"               clang_indexer
"               (<https://github.com/exclipy/clang_indexer>)
"               (<http://blog.wuwon.id.au/2011/10/vim-plugin-for-navigating-c-with.html>)
"
" TODO:                                                        {{{2
"       Find classes with name matching pattern
"       List of classes
"       List of members of classes
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
" }}}1
"=============================================================================

let s:k_version = 001
" Buffer-local Definitions {{{1
" Avoid local reinclusion {{{2
if &cp || (exists("b:loaded_ftplug_lh_clang")
      \ && (b:loaded_ftplug_lh_clang >= s:k_version)
      \ && !exists('g:force_reload_ftplug_lh_clang'))
  finish
endif
let b:loaded_ftplug_lh_clang = s:k_version
let s:cpo_save=&cpo
set cpo&vim
" Avoid local reinclusion }}}2
"------------------------------------------------------------------------
" Menus, commands and mappings {{{2
let s:key_usr          = lh#option#get('clang_key_usr'         , '<leader>u')
let s:key_declarations = lh#option#get('clang_key_declarations', '<leader>d')
let s:key_references   = lh#option#get('clang_key_references'  , '<leader>r')
let s:key_subclasses   = lh#option#get('clang_key_subclases'   , '<leader>s')

if has('gui_running') && has ('menu')
    amenu 50.89 &Project.----<sep>---- Nop
endif
call lh#menu#make("n", '50.90', '&Project.See &USR', s:key_usr,
            \ '<buffer>', ":call clang#get_currentusr()<cr>")
call lh#menu#make("n", '50.91', '&Project.See &Declarations', s:key_declarations,
            \ '<buffer>', ":call clang#display_references('declarations')<cr>")
call lh#menu#make("n", '50.92', '&Project.See &References',   s:key_references,
            \ '<buffer>', ":call clang#display_references('all')<cr>")
call lh#menu#make("n", '50.93', '&Project.See &Sub-classes',  s:key_subclasses,
            \ '<buffer>', ":call clang#display_references('subclasses')<cr>")

"=============================================================================
" Global Definitions {{{1
" Avoid global reinclusion {{{2
if &cp || (exists("g:loaded_ftplug_lh_clang")
      \ && (g:loaded_ftplug_lh_clang >= s:k_version)
      \ && !exists('g:force_reload_ftplug_lh_clang'))
  let &cpo=s:cpo_save
  finish
endif
let g:loaded_ftplug_lh_clang = s:k_version
" Avoid global reinclusion }}}2
"------------------------------------------------------------------------
" Functions {{{2
" Note: most filetype-global functions are best placed into
" autoload/«your-initials»/c/«lh_clang».vim
" Keep here only the functions are are required when the ftplugin is
" loaded, like functions that help building a vim-menu for this
" ftplugin.
" Functions }}}2
"------------------------------------------------------------------------
let &cpo=s:cpo_save
"=============================================================================
" vim600: set fdm=marker:
