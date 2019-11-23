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
import vim
import time
import re
import threading
import linecache
from clang.cindex import *
# import clang.cindex

#======================================================================
# Patch to clang_complete cindex.py file
# See Issue#1: https://github.com/LucHermitte/vim-clang/issues/1
def _null_cursor():
  return clang.cindex.conf.lib.clang_getNullCursor()
def _is_null_cursor(self):
  return self == clang.cindex.conf.lib.clang_getNullCursor()

Cursor.nullCursor = staticmethod(_null_cursor)
Cursor.isNull     = _is_null_cursor

def _get_template_cursor_kind(self):
  from clang.cindex import conf
  tk = conf.lib.clang_getTemplateCursorKind(self)
  return CursorKind.from_id(tk)

Cursor.get_template_cursor_kind = _get_template_cursor_kind

#======================================================================
def getCurrentLine():
  return int(vim.eval("line('.')"))

def getCurrentColumn():
  return int(vim.eval("col('.')"))

# Get a tuple (fileName, fileContent) for the file opened in the current
# vim buffer. The fileContent contains the unsafed buffer content.
def getCurrentFile():
  file = "\n".join(vim.eval("getline(1, '$')"))
  return (vim.current.buffer.name, file)

def computeCurrentTranslationUnit(args, currentFile, fileName):
  flags = TranslationUnit.PARSE_PRECOMPILED_PREAMBLE
  tu = index.parse(fileName, args, [currentFile], flags)
  return tu

def getSystemCompilationOptions():
  return vim.eval('clang#system_options()')

def getCompilationDatabase():
  cdb_path = vim.eval('clang#compilation_database_path()')
  if not cdb_path:
    return None
  global debug
  if debug:
    print("Compilation database found in %s" % (cdb_path,))
  return CompilationDatabase.fromDirectory(cdb_path)

def getCompilationOptions(filename):
  global debug
  options = getSystemCompilationOptions()
  user_options = vim.eval("clang#user_options()")
  options += user_options
  if debug:
    print("system options: %s"%(options))
    print("user   options: %s"%(user_options))
  cdb = getCompilationDatabase()
  if cdb:
    cdbOptions = cdb.getCompileCommands(filename)
    if not cdbOptions:
      # TODO: In case this is a header file, need to find options elsewhere
      # -> It seems header files are add into the compilation database
      pass
    else:
      # keep only -i*, -I*, -std*, -D*, --driver
      matcher = re.compile('-[iIDsW]|--driver')
      for cmd in cdbOptions:
        if debug:
          print("cmd: %s"%[arg for arg in cmd.arguments])
          # print("good: %s"%[arg for arg in cmd.arguments if arg and matcher.match(arg)])
        options += [arg for arg in cmd.arguments if arg and matcher.match(arg)]
  return options

# Translation units are cached according to the revision number of the
# associated buffer.
# @todo purge translation units associated to discarded buffers
# @require: exists('*undotree')
tus = {}
def getCurrentTranslationUnit(force_update = False):
  global tus
  global debug
  filename = vim.current.buffer.name
  revnumber = vim.eval('undotree().seq_cur')
  tu_data = tus.get(filename)
  need_to_update = force_update or not tu_data or tu_data['revnumber'] != revnumber
  if debug:
    print("Updating TU for %s: %s (force: %s, revnumber: %s VS %s)"
        % (filename, need_to_update, force_update, revnumber,
          tu_data and tu_data['revnumber']))
  # + need to update if clang compilation DB has been updated
  if not need_to_update:
    return tu_data['tu']

  options = getCompilationOptions(filename)
  if debug:
    print("OPTIONS: %s"%options)
  tu = computeCurrentTranslationUnit(options, getCurrentFile(), filename)
  tus[filename] = {'revnumber': revnumber, 'tu': tu}
  return tu

#======================================================================
def getCurrentCursor():
  global debug
  tu = getCurrentTranslationUnit()
  file = tu.get_file(vim.current.buffer.name)
  loc = tu.get_location(file.name, (getCurrentLine(), getCurrentColumn()))
  cursor = Cursor.from_location(tu, loc)
  if debug:
    print("Location:", loc)
    print("Cursor:", cursor.displayname)
  return cursor

#======================================================================
k_function_kinds = [
    CursorKind.CONSTRUCTOR,
    CursorKind.CONVERSION_FUNCTION,
    CursorKind.CXX_METHOD,
    CursorKind.DESTRUCTOR,
    CursorKind.FUNCTION_DECL,
    CursorKind.FUNCTION_TEMPLATE,
    ]

k_pointer_types = [
    TypeKind.MEMBERPOINTER,
    TypeKind.POINTER,
    ]
k_function_types = [
    TypeKind.FUNCTIONNOPROTO,
    TypeKind.FUNCTIONPROTO,
    ]
k_array_types = [
    TypeKind.CONSTANTARRAY,
    TypeKind.VECTOR,
    TypeKind.INCOMPLETEARRAY,
    TypeKind.VARIABLEARRAY,
    TypeKind.DEPENDENTSIZEDARRAY
    ]

def decodeRefQualifier(kind):
  from clang.cindex import RefQualifierKind
  if kind == RefQualifierKind.NONE:
    return 'none'
  elif kind == RefQualifierKind.LVALUE:
    return 'lvalue'
  elif kind == RefQualifierKind.RVALUE:
    return 'rvalue'

def decodeType(type):
  res = {
      'spelling': type.spelling,
      'kind': typeKinds.get(type.kind, type.kind.name),
      'num_template_arguments': type.get_num_template_arguments(),
      # 'canonical': type.get_canonical(),
      'const': type.is_const_qualified(),
      'volatile': type.is_volatile_qualified(),
      'restrict': type.is_restrict_qualified(),
      'adress_space': type.get_address_space(),
      'typedef_name': type.get_typedef_name(),
      # 'class_type': type.get_class_type(),
      # 'named_type': type.get_named_type(),
      'pod': type.is_pod(),
      'align': type.get_align(),
      'size': type.get_size(),
      'ref_qualifier': decodeRefQualifier(type.get_ref_qualifier())
      }
  if type.kind in k_function_types:
    res['result']        = decodeType(type.get_result())
  elif type.kind in k_array_types:
    res['element_type']  = type.element_type()
    res['element_count'] = type.element_count()
  elif type.kind in k_pointer_types:
    res['pointee']       = decodeType(type.get_pointee())
  return res

def decodeArgument(cursor):
  res = {
      'type': decodeType(cursor.type),
      'spelling': cursor.spelling
      }
  return res

def decodeAccessSpecifier(access_specifier):
  from clang.cindex import AccessSpecifier
  if access_specifier == AccessSpecifier.PUBLIC:
    return 'public'
  elif access_specifier == AccessSpecifier.PROTECTED:
    return 'protected'
  elif access_specifier == AccessSpecifier.PRIVATE:
    return 'private'
  elif access_specifier == AccessSpecifier.NONE:
    return 'none'
  else:
    return '???'

def decodeConstructorKind(cursor):
  if cursor.is_converting_constructor():
    return 'converting'
  elif cursor.is_copy_constructor():
    return 'copy'
  elif cursor.is_move_constructor():
    return 'move'
  elif cursor.is_default_constructor():
    return 'default'
  else:
    return ''

def decodeExceptionSpecificationKind(kind):
  from clang.cindex import ExceptionSpecificationKind
  if kind == ExceptionSpecificationKind.NONE:
    return 'none'
  elif kind == ExceptionSpecificationKind.DYNAMIC_NONE:
    return 'dynamic_none'
  elif kind == ExceptionSpecificationKind.DYNAMIC:
    return 'dynamic'
  elif kind == ExceptionSpecificationKind.MS_ANY:
    return 'ms_any'
  elif kind == ExceptionSpecificationKind.BASIC_NOEXCEPT:
    return 'basic_noexcept'
  elif kind == ExceptionSpecificationKind.COMPUTED_NOEXCEPT:
    return 'computed_noexcept'
  elif kind == ExceptionSpecificationKind.UNEVALUATED:
    return 'unevaluated'
  elif kind == ExceptionSpecificationKind.UNINSTANTIATED:
    return 'uninstantiated'
  elif kind == ExceptionSpecificationKind.UNPARSED:
    return 'unparsed'

def decodeFunction(cursor):
  # libclang doesn't permit to know
  # - whether it's constexpr
  # - whether it's volatile
  # - whether it has been =deleted 
  res = {}
  assert(cursor.kind in k_function_kinds)
  true_kind = cursor.kind
  res['is_definition']     = cursor.is_definition()
  res['const']             = cursor.is_const_method()
  res['is_default_method'] = cursor.is_default_method()
  res['access_specifier']  = decodeAccessSpecifier(cursor.access_specifier)
  # parameters?
  # print("get_arguments()             : ", [decodeArgument(arg) for arg in cursor.get_arguments()])
  # print("children: ", [decodeCursor(ch) for ch in cursor.get_children()])
  # template?
  if cursor.kind == CursorKind.FUNCTION_TEMPLATE:
    true_kind = cursor.get_template_cursor_kind()

    # From the moment, we obtain a FUNCTION_TEMPLATE, (priority >
    # CONSTRUCTOR...), get_arguments() is empty, and yet
    # get_num_template_arguments() is -1
    # print("def: ", decodeCursor(cursor.get_definition())) <- inf loop!
    # print("parent: ", decodeCursor(cursor.semantic_parent)) <- class e.g.
    # print("walk: ", [decodeCursor(ch) for ch in cursor.walk_preorder() if ch != cursor])
    #nb_tpl = cursor.get_num_template_arguments()
    #print("get_num_template_arguments: ", nb_tpl)
    #for i in range(nb_tpl):
    #  tpl_kind = cursor.get_template_argument_kind(i)
    #  print("  kind[%s]: %s"%(i, tpl_kind))
    #  if   tpl_kind in [TemplateArgumentKind.TYPE]:
    #    print("  type[%s]: %s"%(i, cursor.get_template_argument_type(i)))
    #  elif tpl_kind in [TemplateArgumentKind.INTEGRAL]:
    #    print("  value[%s]: %s"%(i, cursor.get_template_argument_value(i)))

  res['true_kind']         = str(true_kind)

  # Constructor kinds
  if true_kind == CursorKind.CONSTRUCTOR:
    res['constructor_kind'] = decodeConstructorKind(cursor)
    
  # The function type, i.e. its signature somehow
  res['type'] = decodeType(cursor.type)
  # return ?
  res['result_type'] = decodeType(cursor.result_type)
  # exception ?
  res['exception_specification_kind'] = decodeExceptionSpecificationKind(cursor.exception_specification_kind)
  # static/override/final/virtual?
  res['virtual'] = cursor.is_virtual_method()
  res['pure'] = cursor.is_pure_virtual_method()
  res['static'] = cursor.is_static_method()
  # align?
  return res

def decodeCursor(cursor):
  # print(dir(cursor.kind))
  res = {
      "spelling " : cursor.spelling,
      "kind "     : str(cursor.kind)
      }
  if cursor.kind in k_function_kinds:
    res.update(decodeFunction(cursor))
  elif cursor.kind in [CursorKind.PARM_DECL]:
    res.update(decodeArgument(cursor))
  return res

def getCurrentSymbol():
  global debug
  debug = int(vim.eval("clang#verbose()")) == 1
  cursor = getCurrentCursor()
  return decodeCursor(cursor)
  # print("mangled_name ", cursor.mangled_name)

#======================================================================
def getCurrentUsr():
  global debug
  debug = int(vim.eval("clang#verbose()")) == 1
  tu = getCurrentTranslationUnit()
  file = tu.get_file(vim.current.buffer.name)
  loc = tu.get_location(file.name, (getCurrentLine(), getCurrentColumn()))
  cursor = Cursor.from_location(tu, loc)
  if debug:
    print("Location:", loc)
    print("Cursor:", cursor.displayname)
  ref = cursor.referenced
  if ref is None or ref.isNull():
    return None
  return ref.get_usr()

#  ref = None
#  while (ref is None or ref == Cursor.nullCursor()):
#    ref = cursor.referenced()
#    nextCursor = cursor.lexical_parent
#    if (nextCursor is None or cursor == nextCursor):
#      return None
#    cursor = nextCursor
#    print("Cursor:", cursor.displayname)
#  return ref.get_usr()

#======================================================================
class ClicDB:
  def __init__(self):
    import bsddb.db as db
    filename = vim.eval("clang#clic_filename()")
    self.clicDb = db.DB()
    try:
      self.clicDb.open(filename, None, db.DB_BTREE, db.DB_RDONLY)
    except db.DBNoSuchFileError:
      self.clicDb.close()
      self.clicDb = None
      raise Exception("DBNoSuchFileError", filename)
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
    print("CLIC not loaded")
    return []
  usr = getCurrentUsr()
  if usr is None:
    print("No USR found")
    result = []
  else:
    qfa = QuickFixAdapter()
    result = filtered(map(qfa.locationToQuickFix, clicDb.getReferencesForUsr(usr)))
    result = qfa.uniq_sort(result)
    if not result:
      print("No references to " + usr)
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
    print("CLIC not loaded")
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
        # print("USR -> ", lk, " in ", parts)
        kind = int(parts[3])
        refKind  = referenceKinds[kind] if referenceKinds.has_key(kind) else kind
        # print("kind: ", kind , " -- ref kind:", refKind)
        if searchKind == refKind or (searchKind.isdigit() and int(searchKind) == kind):
        # if searchKind == refKind or (int(searchKind) == kind):
          # print("USR -> ", lk, " in ", parts)
          # print("FOUND!")
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
# CursorKind.* ->
referenceKinds = dict({
 1 : 'type declaration',
 2 : 'struct declaration',
 3 : 'union declaration',
 4 : 'class declaration',
 5 : 'enum declaration',
 6 : 'member variable declaration',
 7 : 'enum constant declaration',
 8 : 'function declaration',
 9 : 'variable declaration',
10 : 'argument declaration',
20 : 'typedef declaration',
21 : 'member function declaration',
22 : 'namespace declaration',
23 : 'linkage specification',
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
34 : 'using directive',
35 : 'using declaration',
36 : 'type alias declaration',
39 : 'access specifier declaration',
43 : 'type reference',
44 : 'base specifier',
45 : 'template reference',
46 : 'namespace reference',
47 : 'member reference',
48 : 'label reference',
49 : 'overloaded declaration reference',
50 : 'variable reference -- in non-expression context',
70 : 'Invalid file',
71 : 'no declaration found',
72 : 'not implemented',
73 : 'invalid code',
100 : 'expression',
101 : 'reference',
102 : 'member reference',
103 : 'function call',
105 : 'block literal',
106 : 'integer literal',
107 : 'float point number literal',
108 : 'imaginary number literal',
109 : 'string literal',
110 : 'character literal',
111 : 'parenthesized expression',
112 : 'unary expressions',
113 : 'array subscripting',
114 : 'builtin binary operation',
115 : 'compound assignment',
116 : 'ternary operator',
117 : 'C style cast expression',
118 : 'compound literal expression',
119 : 'initializer list expression',
122 : 'C11 generic selection expression',
124 : 'static_cast expression',
125 : 'dynamic_cast expression',
126 : 'reinterpret_cast expression',
127 : 'const_cast expression',
128 : 'C++ functional cast expression',
129 : 'C++ typeid expression',
130 : 'C++ boolean literal',
131 : 'C++ pointer literal',
132 : 'C++ this expression',
133 : 'C++ throw expression',
134 : 'new expression',
135 : 'delete expression',
136 : 'unary expression',
142 : 'pack expansion expression',
143 : 'size of pack expression',
144 : 'lambda expression',

200 : 'statement',
201 : 'label statement',
202 : 'compound statement',
203 : 'case statement',
204 : 'default statement',
205 : 'if statement',
206 : 'switch statement',
207 : 'while statement',
208 : 'do statement',
209 : 'for statement',
210 : 'goto statement',
211 : 'indirect goto statement',
212 : 'continue statement',
213 : 'break statement',
214 : 'return statement',
223 : 'catch statement',
224 : 'try statement',
225 : 'for-range statement',
230 : 'null statement',

300 : 'translation unit',

400 : 'unexposed attribute',
404 : 'final attribute',
405 : 'override attribute',
406 : 'annotate attribute',
407 : 'asm label attribute',
408 : 'packed attribute',
409 : 'pure attribute',
410 : 'const attribute',
411 : 'no-duplicate attribute',
417 : 'visibility attribute',
418 : 'DLL export attribute',
419 : 'DLL import attribute',
438 : 'convergent attribute',
439 : 'warning unused attribute',
440 : 'warning unused result attribute',
441 : 'aligned attribute',

500 : 'preprocessing directive',
501 : 'macro definition',
502 : 'macro instanciation',
503 : 'inclusion directive',

600 : 'module import declaration',
601 : 'type alias template declaration',
602 : 'static_assert',
603 : 'friend declaration',
})

typeKinds = dict({
0 : 'INVALID',
1 : 'UNEXPOSED',
2 : 'VOID',
3 : 'BOOL',
4 : 'CHAR_U',
5 : 'UCHAR',
6 : 'CHAR16',
7 : 'CHAR32',
8 : 'USHORT',
9 : 'UINT',
10 : 'ULONG',
11 : 'ULONGLONG',
12 : 'UINT128',
13 : 'CHAR_S',
14 : 'SCHAR',
15 : 'WCHAR',
16 : 'SHORT',
17 : 'INT',
18 : 'LONG',
19 : 'LONGLONG',
20 : 'INT128',
21 : 'FLOAT',
22 : 'DOUBLE',
23 : 'LONGDOUBLE',
24 : 'NULLPTR',
25 : 'OVERLOAD',
26 : 'DEPENDENT',
27 : 'OBJCID',
28 : 'OBJCCLASS',
29 : 'OBJCSEL',
30 : 'FLOAT128',
31 : 'HALF',
100 : 'COMPLEX',
101 : 'POINTER',
102 : 'BLOCKPOINTER',
103 : 'LVALUEREFERENCE',
104 : 'RVALUEREFERENCE',
105 : 'RECORD',
106 : 'ENUM',
107 : 'TYPEDEF',
108 : 'OBJCINTERFACE',
109 : 'OBJCOBJECTPOINTER',
110 : 'FUNCTIONNOPROTO',
111 : 'FUNCTIONPROTO',
112 : 'CONSTANTARRAY',
113 : 'VECTOR',
114 : 'INCOMPLETEARRAY',
115 : 'VARIABLEARRAY',
116 : 'DEPENDENTSIZEDARRAY',
117 : 'MEMBERPOINTER',
118 : 'AUTO',
119 : 'ELABORATED',
120 : 'PIPE'
  })
#======================================================================
def initVimClang(library_path = None):
  global index
  #if library_path:
  #  Config.set_library_path(library_path)

  #Config.set_compatibility_check(False)
  index = Index.create()
  #global translationUnits
  #translationUnits = dict()
  #global complete_flags
  #complete_flags = int(clang_complete_flags)
  #global libclangLock
  #libclangLock = threading.Lock()


#======================================================================
# vim: set ts=2 sts=2 sw=2 expandtab tw=80:
