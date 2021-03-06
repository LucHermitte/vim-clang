"=============================================================================
" File:         autoload/clang.vim                                      {{{1
" Author:       Luc Hermitte <EMAIL:hermitte {at} free {dot} fr>
"		<URL:https://github.com/LucHermitte/vim-clang>
" Version:      001
" Created:      07th Jan 2013
" Last Update:  03rd Aug 2017
"------------------------------------------------------------------------
" Description:                                                 {{{2
"       Autoload plugin from vim-lang
"
"------------------------------------------------------------------------
" Installation:                                                {{{2
"       Requires: Vim7+, python, clang_indexer, clang_complete,
"                 lh-vim-lib, lh-dev
"       Optional: BTW
"
" History:                                                     {{{2
"       v0.0.1:
"               Main code extracted from clang_complete fork aimed at
"               clang_indexer
"               (<https://github.com/exclipy/clang_indexer>)
"               (<http://blog.wuwon.id.au/2011/10/vim-plugin-for-navigating-c-with.html>)
"
" TODO:                                                        {{{2
"       Implement the features from lh#dev#cpp and lh#cpp#analysis*
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

let s:cpo_save=&cpo
set cpo&vim
"------------------------------------------------------------------------
" ## Misc Functions     {{{1
" # Version {{{2
let s:k_version = 001
function! clang#version()
  return s:k_version
endfunction

" # Debug   {{{2
let s:verbose = 0
function! clang#verbose(...)
  if a:0 > 0 | let s:verbose = a:1 | endif
  return s:verbose
endfunction

function! s:Verbose(expr)
  if s:verbose
    echomsg a:expr
  endif
endfunction

function! clang#debug(expr)
  return eval(a:expr)
endfunction


"------------------------------------------------------------------------
" ## Exported functions {{{1
" # misc {{{2
" Function: clang#user_options() {{{3
function! clang#user_options()
  let res = exists('g:clang_user_options') ? g:clang_user_options : ''
        \. ' '
        \.  exists('b:clang_user_options') ? b:clang_user_options : ''
  return res
endfunction

" Function: clang#update_clic() {{{3
function! clang#update_clic(project_name) abort
  " Assert type(a:project) == type({})
  " echomsg string(a:project_name)
  let project = eval('g:'.a:project_name)
  let source_dir = project.paths.trunk

  let clic_path = fnamemodify(clang#clic_filename(), ":h")
  let build_path = project.paths._build
  if ! isdirectory(clic_path)
    let r = mkdir(clic_path)
    if ! r
      throw "CLIC directory ``".clic_path."'' does not exist, and it cannot be created."
    endif
  endif
  let compile_command_filename = b:BTW_compilation_dir.'/compile_commands.json'
  if !file_readable(compile_command_filename)
    call lh#common#error_msg(compile_command_filename ." hasn't been generated")
    return
  endif
  " $CFLAGS
  let cflags = lh#option#get('clang_compile_options', '')
  let lCFLAGS = type(cflags) == type([]) ? copy(cflags) : split(cflags)
  let lCFLAGS = map(lCFLAGS, '" -c ".fnameescape(v:val)')
  let sCFLAGS = join(lCFLAGS, '')
  if !empty(g:clang_library_path)
    let sCFLAGS .= ' -l '.fnameescape(g:clang_library_path)
  endif
  " Files to exclude when determining the options global to all files in a
  " directory
  let excluded = lh#option#get('clang_compile_excluded_files_for_dir_options', '')
  let lExcluded= type(excluded) == type([]) ? copy(excluded) : split(excluded)
  let lExcluded= map(lExcluded, '" -x ".fnameescape(v:val)')
  if !empty(lExcluded)
    let sExcluded= join(lExcluded, '')
    let sCFLAGS .= sExcluded
  endif
  " The final command + execute
  let cmd = "cd ".fnameescape(clic_path).
        \ ' && clic_update.py '. fnameescape(source_dir).' '.fnameescape(compile_command_filename)
        \ . sCFLAGS
  try
    let makeprg_save = &makeprg
    let &makeprg = cmd
    make
    Copen
  finally
    let &makeprg = makeprg_save
  endtry
endfunction

" # python module init {{{2
" Function: clang#_init_python() {{{3
" The Python module will be loaded only if it has changed since the last time
" this autoload plugin has been sourced. It is of course loaded on the first
" time. Note: this feature is to help me maintain vim-clang.
let s:py_script_timestamp = 0
let s:plugin_root_path    = expand('<sfile>:p:h:h')
let s:clangpy_script      = s:plugin_root_path . '/py/vimclang.py'

function! clang#_init_python() abort
  if !filereadable(s:clangpy_script)
    throw "Cannot find vim-clang python script: ".s:clangpy_script
  endif
  let ts = getftime(s:clangpy_script)
  if s:py_script_timestamp >= ts
    return
  endif
  " clang_complete python part is expected to be already initialized
  call clang#verbose("Importing ".s:clangpy_script)
  python import sys
  exe 'python sys.path = ["' . s:plugin_root_path . '"] + sys.path'
  exe 'pyfile ' . s:clangpy_script
  let s:py_script_timestamp = ts
endfunction

" # python callbacks {{{2
" Function: clang#clic_filename() {{{3
function! clang#clic_filename()
  let Fn = lh#dev#option#get('clic_filename', &ft, expand('%:p:h').'/.clic/index.db')
  if type(Fn) == type(function('has'))
    return Fn()
  elseif type(Fn) == type({}) " BTW dictionnary
    return Fn.clic()
  else
    return expand(Fn)
  endif
endfunction

" # query functions {{{2
" Function: clang#get_currentusr() {{{3
function! clang#get_currentusr() abort
  call s:CheckUseLibrary()
  python print getCurrentUsr()
endfunction

" Function: clang#get_references(what) {{{3
function! clang#get_references(what) abort
  call s:CheckUseLibrary()
  echo "Searching for references to ".expand('<cword>')."..."
  python vim.command('let list = ' + str(getCurrentReferences(vim.eval('a:what'))))
  return list
endfunction

" Function: clang#display_references(what) {{{3
function! clang#display_references(what) abort
  let list = clang#get_references(a:what)
  call s:DisplayIntoQuickfix(list)
endfunction

" Function: clang#list(kind, pattern) {{{3
function! clang#list(kind, pattern)
  call s:CheckUseLibrary()
  python vim.command('let list = ' + str(getDeclarations(vim.eval('a:kind'), vim.eval('a:pattern'))))
  call s:DisplayIntoQuickfix(list)
endfunction

"------------------------------------------------------------------------
" ## Internal functions {{{1
" Function: s:CheckUseLibrary() {{{2
function! s:CheckUseLibrary()
  " NB: this plugin requires clang_complete which is in charge of
  " setting g:clang_use_library
  if ! g:clang_use_library
    throw "lh-clang: The use of libclang is required to perform this operation"
  endif
endfunction

" Function: s:QueryAndDisplayIntoQuickfix(command) {{{2
if !exists(':Copen')
  " :Copen originally comes from BuildToolsWrapper, it's a smart :copen
  "   command that check whether there are errors, and the number of
  "   required lines for the quickfix windows
  " :cd . is used to avoid absolutepaths in the quickfix window
  function! s:Copen()
    call lh#path#cd_without_sideeffects('.')
    copen
  endfunction
  command! Copen call s:Copen()
endif

function! s:DisplayIntoQuickfix(list)
  if !empty(a:list)
    let title = a:list[0].text
    call setqflist(a:list)
    Copen
    let w:quickfix_title = "[CLIC] ".title
  else
    cclose
  endif
endfunction

"------------------------------------------------------------------------
" ## Initialize module  {{{1
call clang#_init_python()
"------------------------------------------------------------------------
" }}}1
let &cpo=s:cpo_save
"=============================================================================
" vim600: set fdm=marker:
