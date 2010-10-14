#!/usr/bin/python
 
import os
import sys

import gio

class GioTrash(object):

    def __init__(self, filename):
        self.filename = filename

        if not os.access(filename, os.F_OK):
            print "Not Found!"
            self.filename = None

    def move(self):
        self.is_trashed = False

        file = gio.File(self.filename)
        access = file.query_info('access::*') 
        can_trash = access.get_attribute_boolean('access::can-trash')

        try:
            if can_trash:
                self.is_trashed = False #file.trash()
        except gio.Error as error:
            if error.code == gio.ERROR_NOT_SUPPORTED:
                print "not supported."
        except:
            print sys.exc_info()

        return self.is_trashed

    def remove(self):
        if not self.is_trashed:
            print "sys.remove!"

if __name__ == "__main__":
    #filename = '/home/master/yendo/Documents/abc'
    filename = '/home/yendo/abc'
    #filename = '/home/master/share/test'

    trash = GioTrash(filename)
    
