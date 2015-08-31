import luigi
import time
import random
import string

# ==============================================================================

class TargetInfoParameter(luigi.Parameter):
    pass

# ==============================================================================

class TargetInfo(object):
    '''
    Class to be used for sending specification of which target, from which
    task, to use, when stitching workflow tasks' outputs and inputs together.
    '''
    task = None
    path = None
    target = None

    def __init__(self, task, path):
        self.task = task
        self.path = path
        self.target = luigi.LocalTarget(path)

    def open(self, *args, **kwargs):
        return self.target.open(*args, **kwargs)

# ==============================================================================

class DependencyHelpers():
    '''
    Mixin implementing methods for supporting dynamic, and target-based
    workflow definition, as opposed to the task-based one in vanilla luigi.
    '''

    # --------------------------------------------------------
    # Handle inputs
    # --------------------------------------------------------

    def requires(self):
        return self._upstream_tasks()

    def _upstream_tasks(self):
        '''
        Extract upstream tasks from the TargetInfo objects
        or functions returning those (or lists of both the earlier)
        for use in luigi's requires() method.
        '''
        upstream_tasks = []
        for attrname, attrval in self.__dict__.iteritems():
            if 'in_' == attrname[0:3]:
                upstream_tasks = self._parse_inputitem(attrval, upstream_tasks)

        return upstream_tasks

    def _parse_inputitem(self, val, tasks):
        '''
        Recursively loop through lists of TargetInfos, or
        callables returning TargetInfos, or lists of ...
        (repeat recursively) ... and return all tasks.
        '''
        if callable(val):
            val = val()
        if isinstance(val, TargetInfo):
            tasks.append(val.task)
        elif isinstance(val, list):
            for valitem in val:
                tasks = self._parse_inputitem(valitem, tasks)
        return tasks

    # --------------------------------------------------------
    # Handle outputs
    # --------------------------------------------------------

    def output(self):
        return self._output_targets()

    def _output_targets(self):
        outputs = []
        for attrname in dir(self):
            attrval = getattr(self, attrname)
            if attrname[0:4] == 'out_':
                # Function returning list of TargetInfos
                if callable(attrval):
                    val = attrval()
                    if isinstance(val, TargetInfo):
                        outputs.append(val.target)
                    elif isinstance(val, list):
                        for item in val:
                            if callable(item):
                                outputs.append(item().target)
                            elif isinstance(item, TargetInfo):
                                outputs.append(item.target)
                            else:
                                raise Exception('Item in list returned by %s neither function nor TargetInfo!' % attrname)
                else:
                    raise Exception('Attribute %s is not callable!' % attrname)


        return outputs
