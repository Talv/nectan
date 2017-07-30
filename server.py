import sys
from nectan.linter import Linter
from nectan.lexer import tokenize
from nectan.index import Index
from nectan.definitions import ParseError
from timeit import default_timer as timer
# import threading
import pprint
from glob import glob

from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple
from jsonrpc import JSONRPCResponseManager, dispatcher

pp = pprint.PrettyPrinter(indent=2, width=80)

class Server(object):
    def __init__(self):
        self.project = Index()
        dispatcher.add_method(self.init)
        dispatcher.add_method(self.lint)
        dispatcher.add_method(self.provideDocumentSymbols)
        dispatcher.add_method(self.provideCompletionItems)
        dispatcher.add_method(self.provideSignatureHelp)
        dispatcher.add_method(self.provideDefinition)

    def init(self, **kwargs):
        self.project = Index(kwargs['workspace'])
        for f in glob('./sc2-sources/**/*.galaxy', recursive=True):
            self.project.addFile(f)
        for f in glob(kwargs['workspace'] + '/**/*.galaxy', recursive=True):
            self.project.addFile(f)
        return True

    def lint(self, **kwargs):
        if not kwargs['filename'] in self.project.documents:
            self.project.addFile(kwargs['filename'])
        return {
            'reports': self.project.lint(kwargs['filename'])
        }

    def provideDocumentSymbols(self, **kwargs):
        symbols = []
        if not kwargs['filename'] in self.project.documents:
            self.project.addFile(kwargs['filename'])
        raw = self.project.getDefinitions(kwargs['filename'])
        for x in raw:
            symbols.append(raw[x].serialize())
        return {
            'symbols': symbols
        }
    
    def provideCompletionItems(self, **kwargs):
        return {
            'completions': self.project.getCompletions(kwargs['filename'], kwargs['position']['line'], kwargs['position']['pos'])
        }

    def provideSignatureHelp(self, **kwargs):
        # kwargs['filename']
        return {
            'signatures': self.project.getSignatures(kwargs['symbolName'])
        }

    def provideDefinition(self, **kwargs):
        return self.project.provideDefinition(kwargs['symbolName'])

    def run(self):
        @Request.application
        def application(request):
            response = JSONRPCResponseManager.handle(
                request.data, dispatcher)
            return Response(response.json, mimetype='application/json')

        run_simple('localhost', 3689, application)

Server().run()