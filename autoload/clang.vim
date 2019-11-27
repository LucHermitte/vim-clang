"=============================================================================
" File:         autoload/clang.vim                                      {{{1
" Author:       Luc Hermitte <EMAIL:hermitte {at} free {dot} fr>
"		<URL:https://github.com/LucHermitte/vim-clang>
" Version:      2.0.0
let s:k_version = 200
" Created:      07th Jan 2013
" Last Update:  26th Nov 2019
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
"       v2.0.0:
"               Reduce dependencies
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
"   Copyright 2013-2019 Luc Hermitte
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
function! clang#version()
  return s:k_version
endfunction

" # Debug   {{{2
let s:verbose = get(s:, 'verbose', 0)
function! clang#verbose(...)
  if a:0 > 0 | let s:verbose = a:1 | endif
  return s:verbose
endfunction

function! s:Log(expr, ...) abort
  call call('lh#log#this',[a:expr]+a:000)
endfunction

function! s:Verbose(expr, ...) abort
  if s:verbose
    call call('s:Log',[a:expr]+a:000)
  endif
endfunction

function! clang#debug(expr) abort
  return eval(a:expr)
endfunction

"------------------------------------------------------------------------
" ## Exported functions {{{1
" Function: clang#can_plugin_be_used() {{{3
function! clang#can_plugin_be_used() abort
  return !empty(clang#libpath())
endfunction

" # options {{{2
" Function: clang#libpath() {{{3
function! clang#libpath() abort
  if !exists('g:clang_library_path')
    " 1- check $LD_LIBRARY_PATH
    if has('unix')
      let libpaths = split($LD_LIBRARY_PATH, has('unix') ? ':' : ',')
      call filter(libpaths, '!empty(glob(v:val."/libclang.so*", 1))')
      if !empty(libpaths)
        let g:clang_library_path = libpaths[0]
      endif
    endif
  endif
  " 2- check $PATH if nothing was found yet
  if !exists('g:clang_library_path')
    " Keeps paths ending in 'bin$'
    let binpaths = filter(split($PATH, has('unix') ? ':' : ','), 'v:val =~ "bin[/\\\\]\\=$"')
    call filter(binpaths, '!empty(glob(v:val[:-4]."lib/libclang.so*", 1))')
    if !empty(binpaths)
      let g:clang_library_path = binpaths[0]
    else
      let g:clang_library_path = ''
    endif
  endif
  return g:clang_library_path
endfunction

" Function: clang#compilation_database() {{{3
function! clang#compilation_database() abort
  let filename = lh#option#get('BTW.compilation_dir')
  if lh#option#is_set(filename)
    let filename .= .'/compile_commands.json'
    let found = filereadable(filename)
    call s:Verbose("Compilation database ".(found ? "found: '%1'" : "not found"), filename)
    return filename
  else
    return ''
  endif
endfunction

" Function: clang#compilation_database_path() {{{3
function! clang#compilation_database_path() abort
  let p = clang#compilation_database()
  return empty(p) ? p : fnamemodify(p, ':p:h')
endfunction

" Function: clang#user_options() {{{3
function! clang#user_options() abort
  let res = get(g:, 'clang_user_options', []) + get(b:, 'clang_user_options', [])
  return res
endfunction

" Function: clang#get_symbol() {{{3
function! clang#get_symbol(...) abort
  " pyx print(getCurrentSymbol())
  let what = get(a:, 1, '')
  let res = pyxeval('getCurrentSymbol(vim.eval("what"))')
  return res
endfunction

" # misc {{{2
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
  call s:Verbose("Importing ".s:clangpy_script)
  pyx << EOF
import sys, vim
plugin_root_path = vim.eval('s:plugin_root_path')
if not plugin_root_path in sys.path:
  sys.path = [ plugin_root_path ] + sys.path
elif int(vim.eval('clang#verbose()')):
  print("sys.path already contains %s" % (plugin_root_path))
EOF
  exe 'pyxfile ' . s:clangpy_script
  pyx initVimClang()
  let s:py_script_timestamp = ts
endfunction

" # python callbacks {{{2
" Function: clang#clic_filename() {{{3
function! clang#clic_filename()
  let Fn = lh#ft#option#get('clic_filename', &ft, expand('%:p:h').'/.clic/index.db')
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
  pythonx print(getCurrentUsr())
endfunction

" Function: clang#get_references(what) {{{3
function! clang#get_references(what) abort
  call s:CheckUseLibrary()
  echo "Searching for references to ".expand('<cword>')."..."
  pythonx vim.command('let list = ' + str(getCurrentReferences(vim.eval('a:what'))))
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
  pythonx vim.command('let list = ' + str(getDeclarations(vim.eval('a:kind'), vim.eval('a:pattern'))))
  call s:DisplayIntoQuickfix(list)
endfunction

"------------------------------------------------------------------------
" ## Internal functions {{{1
" Function: s:CheckUseLibrary() {{{2
function! s:CheckUseLibrary()
  " NB: this plugin requires clang_complete which is in charge of
  " setting g:clang_use_library
  " if ! g:clang_use_library
    " throw "lh-clang: The use of libclang is required to perform this operation"
  " endif
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
" }}}1
let &cpo=s:cpo_save
"------------------------------------------------------------------------
" ## Test functions to move elsewhere eventually {{{1
" Function: clang#parents() {{{2
function! clang#parents() abort
  let symbol = clang#get_symbol()
  let children = get(symbol, 'children', {})
  let parents = get(children, 'CursorKind.CXX_BASE_SPECIFIER', [])
  let res = lh#list#get(parents, 'spelling')
  return res
endfunction
"------------------------------------------------------------------------
" ## Initialize module  {{{1
if empty(lh#python#best_still_avail())
  call lh#notify#once("+python support is required for libclang support")
else
  call clang#_init_python()
endif
" }}}1
"=============================================================================
" vim600: set fdm=marker:
