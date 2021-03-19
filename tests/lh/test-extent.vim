"=============================================================================
" File:         addons/vim-clang/tests/lh/test-extent.vim         {{{1
" Author:       Luc Hermitte <EMAIL:luc {dot} hermitte {at} gmail {dot} com>
"		<URL:http://github.com/LucHermitte/vim-clang>
" Version:      0.0.3
let s:k_version = 003
" Created:      19th Mar 2021
" Last Update:  19th Mar 2021
"------------------------------------------------------------------------
" Description:
"       Test extent related functions
" }}}1
"=============================================================================

UTSuite [vim-clang] Testing extent functions

runtime autoload/clang.vim

let s:cpo_save=&cpo
set cpo&vim

" ## Fixtures {{{1
function! s:BeforeAll() abort
  call lh#window#create_window_with('sp foo.bar')
endfunction

function! s:AfterAll() abort
  silent bw! foo.bar
endfunction

"------------------------------------------------------------------------
function! s:Test_extent_bla_1l()
  SetBufferContent trim << EOF
  bla{ }
  EOF
  let e = {'filename': 'foo.bar', 'start': {'lnum': 1, 'col': 4}, 'end': {'lnum': 1, 'col': 7}}
  let lines = clang#extract_from_extent(e, 'get')
  AssertEquals(lines, ['{ }'])
  let lines = clang#cut_extent(e, 'cut')
  AssertEquals(lines, ['{ }'])
  AssertBufferMatch trim << EOF
  bla
  EOF
endfunction

function! s:Test_extent_bla_bli_1l()
  SetBufferContent trim << EOF
  bla{ }bli
  EOF
  let e = {'filename': 'foo.bar', 'start': {'lnum': 1, 'col': 4}, 'end': {'lnum': 1, 'col': 7}}
  let lines = clang#extract_from_extent(e, 'get')
  AssertEquals(lines, ['{ }'])
  let lines = clang#cut_extent(e, 'cut')
  AssertEquals(lines, ['{ }'])
  AssertBufferMatch trim << EOF
  blabli
  EOF
endfunction

function! s:Test_extent_bla_2l()
  SetBufferContent trim << EOF
  bla{
  }
  EOF
  let e = {'filename': 'foo.bar', 'start': {'lnum': 1, 'col': 4}, 'end': {'lnum': 2, 'col': 2}}
  let lines = clang#extract_from_extent(e, 'get')
  AssertEquals(lines, ['{','}'])
  let lines = clang#cut_extent(e, 'cut')
  AssertEquals(lines, ['{','}'])
  AssertBufferMatch trim << EOF
  bla
  EOF
endfunction

function! s:Test_extent_bla_bli_2l()
  SetBufferContent trim << EOF
  bla{
  }bli
  EOF
  let e = {'filename': 'foo.bar', 'start': {'lnum': 1, 'col': 4}, 'end': {'lnum': 2, 'col': 2}}
  let lines = clang#extract_from_extent(e, 'get')
  AssertEquals(lines, ['{','}'])
  let lines = clang#cut_extent(e, 'cut')
  AssertEquals(lines, ['{','}'])
  AssertBufferMatch trim << EOF
  bla
  bli
  EOF
endfunction

function! s:Test_extent_1l()
  SetBufferContent trim << EOF
  { }
  EOF
  let e = {'filename': 'foo.bar', 'start': {'lnum': 1, 'col': 1}, 'end': {'lnum': 1, 'col': 4}}
  let lines = clang#extract_from_extent(e, 'get')
  AssertEquals(lines, ['{ }'])
  let lines = clang#cut_extent(e, 'cut')
  AssertEquals(lines, ['{ }'])
  AssertBufferMatch trim << EOF
  EOF
endfunction

function! s:Test_extent_bli_1l()
  SetBufferContent trim << EOF
  { }bli
  EOF
  let e = {'filename': 'foo.bar', 'start': {'lnum': 1, 'col': 1}, 'end': {'lnum': 1, 'col': 4}}
  let lines = clang#extract_from_extent(e, 'get')
  AssertEquals(lines, ['{ }'])
  let lines = clang#cut_extent(e, 'cut')
  AssertEquals(lines, ['{ }'])
  AssertBufferMatch trim << EOF
  bli
  EOF
endfunction

function! s:Test_extent_2l()
  SetBufferContent trim << EOF
  {
  }
  EOF
  let e = {'filename': 'foo.bar', 'start': {'lnum': 1, 'col': 1}, 'end': {'lnum': 2, 'col': 2}}
  let lines = clang#extract_from_extent(e, 'get')
  AssertEquals(lines, ['{', '}'])
  let lines = clang#cut_extent(e, 'cut')
  AssertEquals(lines, ['{', '}'])
  AssertBufferMatch trim << EOF
  EOF
endfunction

function! s:Test_extent_bli_2l()
  SetBufferContent trim << EOF
  {
  }bli
  EOF
  let e = {'filename': 'foo.bar', 'start': {'lnum': 1, 'col': 1}, 'end': {'lnum': 2, 'col': 2}}
  let lines = clang#extract_from_extent(e, 'get')
  AssertEquals(lines, ['{', '}'])
  let lines = clang#cut_extent(e, 'cut')
  AssertEquals(lines, ['{', '}'])
  AssertBufferMatch trim << EOF
  bli
  EOF
endfunction

"------------------------------------------------------------------------
let &cpo=s:cpo_save
"=============================================================================
" vim600: set fdm=marker:
