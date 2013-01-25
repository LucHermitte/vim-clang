# File:       py/vimclang.py                                            {{{1
# Maintainer: Hermitte <EMAIL:hermitte {at} free {dot} fr>
#             <URL:https://github.com/LucHermitte/vim-clang>
# Copying:                                                     {{{2
#   getReferences() and getCurrentUser() functions are courtesy of exclipy.
#         https://github.com/exclipy/clang_complete
#   Copyright 2013 Luc Hermitte
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
# }}}1
#======================================================================
# from clang.cindex import *
import vim
import time
import re
import threading
import bsddb.db as db
import linecache

def getCurrentLine():
  return int(vim.eval("line('.')"))

def getCurrentColumn():
  return int(vim.eval("col('.')"))

#======================================================================
def getCurrentUsr():
  userOptions = splitOptions(vim.eval("clang#user_options()"))
  global debug
  debug = int(vim.eval("g:clang_debug")) == 1
  params = getCompileParams(vim.current.buffer.name)
  timer = CodeCompleteTimer(debug, vim.current.buffer.name, -1, -1, params)
  tu = getCurrentTranslationUnit(
      userOptions, getCurrentFile(),
      vim.current.buffer.name, timer, update = True)
  file = tu.get_file(vim.current.buffer.name)
  loc = tu.get_location(file.name, (getCurrentLine(), getCurrentColumn()))
  cursor = Cursor.from_location(tu, loc)
  ref = cursor.referenced
  if ref is None or ref == Cursor.nullCursor():
    return None
  # print "Cursor:", cursor.displayname
  return ref.get_usr()

#  ref = None
#  while (ref is None or ref == Cursor.nullCursor()):
#    ref = cursor.referenced()
#    nextCursor = cursor.lexical_parent
#    if (nextCursor is None or cursor == nextCursor):
#      return None
#    cursor = nextCursor
#    print "Cursor:", cursor.displayname
#  return ref.get_usr()

#======================================================================
class ClicDB:
  def __init__(self):
    filename = vim.eval("clang#clic_filename()")
    self.clicDb = db.DB()
    try:
      self.clicDb.open(filename, None, db.DB_BTREE, db.DB_RDONLY)
    except db.DBNoSuchFileError:
      self.clicDb.close()
      self.clicDb = None
      raise "DBNoSuchFileError", filename
  def __del__(self):
    if self.clicDb != None:
      self.clicDb.close()

  def getReferencesForUsr(self, usr):
    locations = self.clicDb.get(usr, '')
    return locations.split('\t')

  def getUsrList(self):
    return self.clicDb.keys()

#======================================================================
class QuickFixAdapter:
  def locationToQuickFix(self, location):
    parts = location.split(':')
    if len(parts) != 4:
      return {} # mark invalid items with an empty dict
    filename = parts[0]
    line = int(parts[1])
    column = int(parts[2])
    kind = int(parts[3])
    refKind  = referenceKinds[kind] or kind
    text = linecache.getline(filename, line).rstrip('\n')
    if text is not '':
        text = refKind.rstrip() + ": " + text.strip()
    return {'filename' : filename, 'lnum' : line, 'col' : column, 'text': text, 'kind': kind}

  def uniq_sort(self,quickFixList):
    def locationsMatch(item1, item2):
      return item1['filename'] == item2['filename']\
          and item1['lnum'] == item2['lnum']\
          and item1['col'] == item2['col']
    quickFixList.sort(lambda a, b:
        cmp((a['filename'], a['lnum'], a['col'], a['kind']),
          (b['filename'], b['lnum'], b['col'], b['kind']))
        )
    i = 0
    while i < len(quickFixList):
      if i > 0 and locationsMatch(quickFixList[i], quickFixList[i-1]):
        # In general, a Kind of higher value is more interesting,
        # so we deduplicate the list by removing the Kind of lower value
        # when we see two adjacent items at the same location
        if quickFixList[i-1]['kind'] < quickFixList[i]['kind']:
          quickFixList.pop(i-1)
        else:
          quickFixList.pop(i)
      else:
        i += 1
    return quickFixList


#======================================================================
# searchKind is one of ["declarations", "subclasses", None]
def getCurrentReferences(searchKind = None):
  def filtered(quickFixList):
    quickFixList = filter(lambda x: len(x) > 0 and len(x['text']) > 0, quickFixList) # remove invalid items
    validKinds = []
    if searchKind == None or searchKind == 'all':
      return quickFixList
    elif searchKind == 'declarations':
      validKinds = range(1, 40)
    elif searchKind == 'subclasses':
      validKinds = [44]
    return filter(lambda x: x['kind'] in validKinds, quickFixList)

  # Start of getCurrentReferences():
  clicDb = ClicDB()
  if clicDb is None:
    print "CLIC not loaded"
    return []
  usr = getCurrentUsr()
  if usr is None:
    print "No USR found"
    result = []
  else:
    qfa = QuickFixAdapter()
    result = filtered(map(qfa.locationToQuickFix, clicDb.getReferencesForUsr(usr)))
    result = qfa.uniq_sort(result)
    if not result:
      print "No references to " + usr
    else:
      if searchKind == 'all':
        title = 'References to ' + usr
      else:
        title = searchKind + ' of ' + usr
        result.insert(0, {'text': title} )
  return result

#======================================================================
def getDeclarations(searchKind, pattern):
  clicDb = ClicDB()
  if clicDb is None:
    print "CLIC not loaded"
    return []
  
  result = []
  matcher = re.compile(pattern)
  # todo: fix acces to sub info
  usrs = clicDb.getUsrList()
  for k in usrs:
    lk = k.split('#')[0].split('@')
    if matcher.match(lk[-1]):
      locations = clicDb.getReferencesForUsr(k)
      for loc in locations:
        parts = loc.split(':')
        # print "USR -> ", lk, " in ", parts
        kind = int(parts[3])
        refKind  = referenceKinds[kind] if referenceKinds.has_key(kind) else kind
        # print "kind: ", kind , " -- ref kind:", refKind
        if searchKind == refKind or (searchKind.isdigit() and int(searchKind) == kind):
        # if searchKind == refKind or (int(searchKind) == kind):
          # print "USR -> ", lk, " in ", parts
          # print "FOUND!"
          filename = parts[0]
          line = int(parts[1])
          column = int(parts[2])
          text = linecache.getline(filename, line).rstrip('\n')
          if text is not '':
              text = refKind.rstrip() + ": " + text.strip()
          result . append({'filename' : filename, 'lnum' : line, 'col' : column, 'text': text, 'kind': kind})

  # End of function
  return result

#======================================================================

# Preprocessing                                                                \
referenceKinds = dict({
 1 : 'type declaration',
 2 : 'struct declaration',
 3 : 'union declaration',
 4 : 'class declaration',
 5 : 'enum declaration',
 6 : 'member declaration',
 7 : 'enum constant declaration',
 8 : 'function declaration',
 9 : 'variable declaration',
10 : 'argument declaration',
20 : 'typedef declaration',
21 : 'method declaration',
22 : 'namespace declaration',
24 : 'constructor declaration',
25 : 'destructor declaration',
26 : 'conversion function declaration',
27 : 'template type parameter',
28 : 'non-type template parameter',
29 : 'template template parameter',
30 : 'function template declaration',
31 : 'class template declaration',
32 : 'class template partial specialization',
33 : 'namespace alias',
43 : 'type reference',
44 : 'base specifier',
45 : 'template reference',
46 : 'namespace reference',
47 : 'member reference',
48 : 'label reference',
49 : 'overloaded declaration reference',
100 : 'expression',
101 : 'reference',
102 : 'member reference',
103 : 'function call'
})

# vim: set ts=2 sts=2 sw=2 expandtab tw=80:
