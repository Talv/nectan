import sys
from nectan.linter import Linter
from nectan.lexer import tokenize
from nectan.index import Index
from timeit import default_timer as timer
from glob import glob
# import threading

# filename = sys.argv[1]
# filename = 'testdir/asd.galaxy'
# with open(filename) as f:
#     tokens = list(tokenize(f.read()))
#     print(tokens)

ind = Index()
ind.addFile('testdir/inc.galaxy')
ind.addFile('testdir/asd.galaxy')
# print(ind.lint('testdir/asd.galaxy'))
print(ind.provideDefinition('idx'))
# for f in glob('sc2-sources/**/*.galaxy', recursive=True):
#     ind.addFile(f)

# for x in ind.getCompletions(list(ind.documents.keys())[0], 1, 1):
#     print(x)

# defs = ind.getDefinitions()
# for x in defs:
#     print(defs[x].serialize())

# start = timer()

# # filename = sys.argv[1]

# # l = Linter()
# # l.lintFile(sys.argv[1])

# end = timer()
# print(end - start)    