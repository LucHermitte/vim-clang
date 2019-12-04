vim-clang API:
--------------

### Vim functions
The following functions are provided in the hope to simplify definition of other
plugins

#### `clang#can_plugin_be_used()`
Returns whether `libclang` library has been found and can be used from this
plugin.

#### `clang#libpath()`
Used internally to know where the library has been found.

#### `clang#compilation_database()`
Used internally to know where the JSON compilation database has been found, if
any.

__Note:__ The `compile_commands.json` file is generated automatically by
`CMake` in the build directory. Usually, when we use `CMake`, we use
out-of-source building. This means, that the JSON compilation database will be
in a directory that depends on the current compilation directory/compilation
mode.

Most LSP plugins and LSP compatible IDEs expect that file in the root sources
directory. This means, you'll have to either copy the file after each call to
`cmake` or `make` that updates the database, or to create a symbolic link from
a chosen compilation directory to the source directory.

This is clumsy.

If you chose to install my
[build-tools-wrapper (BTW)](http://github.com/LucHermitte/vim-build-tools-wrapper)
vim plugin, you won't have to create this symbolic link for vim-clang -- but
you'll still need to do it for other LSP plugins like
[COC](https://github.com/neoclide/coc.nvim). _BTW_ is able to compile `CMake`
based projects. It permits to select the current compilation directory (that
corresponds to a compilation mode: _Release_, _Debug_, _Sanitized_...). The
current compilation directory will be automatically stored in
`(bpg):BTW.compilation_dir` variable.

vim-clang, will try to find the compilation database, first in
`(bpg):BTW.compilation_dir`, then in the source root directory.

If you're not using CMake, but still have complex projects made of many files,
you'll be interested in [Bear](https://github.com/rizsotto/Bear). Having a
compilation database will also help with static analysers like `clang-tidy` and
all the C&C++ LSP servers.

#### `clang#compilation_database()`
Used internally to fetch user specified options from `g:clang_user_options` and
`b:clang_user_options`.

This mechanism has been inherited from clang-complete to pass important options
like where are the included files.

While it's still useful with pet projects where we manually inject options into
`$CFLAGS` or `$CXXXFLAGS`, this is not as important in vim-clang for two
reasons:

- first vim-clang is able to automatically find compilation databases from
  where it'll extract the relevant compilation options,
- then vim-clang always asks `clang++` where the system includes are installed
  with:

    ```sh
    clang++ -E -xc++ - -Wp,-v < /dev/null
    ```

  For some reason, when clang is installed manually, while it knows where its
  system includes are, libclang doesn't. This can be really annoying. In
  particular if we also change the usual standard library implementation used
  on the system.

#### `clang#getsymbol({kind})`
Returns complete information for the current outer symbol of the required kind.

Possible values for symbol kind are:

- ""
- "function"
- "class"
- "namespace"

This function wraps python `getCurrentSymbol()` function.

#### `clang#parents()`
Returns the parents of the current class.

Wraps Python `getParents(findClass(), True)`.

Used by lh-cpp `:Ancestors` command.

#### `clang#functions()`
Returns the functions of the current scope (class/namespace).

Wraps Python `getFunctions(findScope())`.

#### `clang#non_overriden_virtual_functions()`
Returns the inherited virtual functions that can be overridden, and that
haven't been already overridden in the current class.

Wraps Python `getNonOverriddenVirtualFunctions(findClass())`.

Used by lh-cpp `:Override` command.

### Python functions
The following functions are available from vim through
[`:pyx`](http://vimhelp.appspot.com/if_pyth.txt.html#%3apyx) and
[`pyxeval()`](http://vimhelp.appspot.com/eval.txt.html#pyxeval%28%29).

List to be completed...

