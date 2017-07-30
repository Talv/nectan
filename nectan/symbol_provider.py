from . import ast
from . import definitions
from . import utils
from . import parser
from . import symtable
import json
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler, FileSystemEventHandler
import logging
import time
import glob


class FileEventHandler(FileSystemEventHandler):
    def is_galaxy(self, filename):
        return True

    def on_moved(self, event):
        super(FileEventHandler, self).on_moved(event)

        what = 'directory' if event.is_directory else 'file'
        logging.info("Moved %s: from %s to %s", what, event.src_path,
                     event.dest_path)

    def on_created(self, event):
        super(FileEventHandler, self).on_created(event)

        what = 'directory' if event.is_directory else 'file'
        logging.info("Created %s: %s", what, event.src_path)

    def on_deleted(self, event):
        super(FileEventHandler, self).on_deleted(event)

        what = 'directory' if event.is_directory else 'file'
        logging.info("Deleted %s: %s", what, event.src_path)

    def on_modified(self, event):
        super(FileEventHandler, self).on_modified(event)

        what = 'directory' if event.is_directory else 'file'
        logging.info("Modified %s: %s", what, event.src_path)


class SymbolProvider(object):
    def __init__(self, path):
        self.path = path

    def run(self):
        event_handler = FileEventHandler()
        observer = Observer()
        for x in self.paths:
            observer.schedule(event_handler, x, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    def index(self):
        for filename in glob.glob(self.path + '/**/*.galaxy', recursive=True):
            print(filename)
