# -*- coding: utf-8 -*-

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Configuration
'''

__author__ = 'xy Fan'

import config_default

class Dict(dict):
    '''
    Simple dict but support access as x.y style.
    '''
    def __init__(self, name=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(name, values):
            self[k] = v
    
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)
    
    def __setattr__(self, key, value):
        self[key] = value

def merge(defaults, override):
    r = {}
    for k, v in defaults.items():
        if k in override:
            if isinstance(v, dict):
                r[k] = merge(v, override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = v
    return r

def toDict(d):
    D = Dict()
    for k, v in d.items():
        D[k] = toDict(v) if isinstance(v, dict) else v
    return D

configs = config_default.config

try:
    import config_override
    configs = merge(configs, config_override.config)
except ImportError:
    pass

configs = toDict(configs)


