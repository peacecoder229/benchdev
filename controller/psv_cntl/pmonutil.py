#!/usr/bin/env python
# Maintained by Derek Duterte
"""
PythonSV Pmon Utility
"""

# versioning information
__version__ = '1.0 STABLE'
import pdb
from time import clock
import sys
import itertools
import copy
import events_parser
import pmon_reg_parser
import svtools.logging.toolbox as toolbox
import components.socket as socket
import svtools.common.baseaccess as baseaccess
from libpu import linkNode
from libpu import unitWrapper
from libpu import eventWrapper
from libpu import maskWrapper
from libpu import commonSubString
from libpu import pmonsLink
from components.utils import Frozen
from components.utils import getpysvpath
from events_parser import eventMask
from events_parser import pmonEvent
from libpu import identify_system_type
from libpu import pythonify_name
from libpu import writeReg
from util_exceptions import NoAvailableCountersException
from util_exceptions import InvalidCounterIndexException
from util_exceptions import InvalidRegisterFieldException
from util_exceptions import ExpiredEventCounterHandleException
from util_exceptions import MissingXMLException
import os
import random
import pdb


# globals
XML_PATH_BASE = getpysvpath()
_COMBO_PREFIX = "umask_"
_GENERATE_ALL_COMBOS_FUNCTION_NAME = 'generateAllCombinations'
_DEBUG = False
_COUNTER_MODE = False
ddrt_event = 0
non_ddrt_event = 0


# This has to be done this way to prevent a circular import between gmons and pmons.
# I'll need to figure out a better solution to this as this is definitely a nasty mess that doesn't scale.
def gmonAll():
    try:
        from cascadelakex.gmons.ggui import runAll
    except:
        try:
            from skylakex.users.taschell.gmons.ggui import runAll
        except:
            print "Error: couldn't load skylakex or cascadelakex gmons."
    runAll()

def gmonCboM2mImc():
    try:
        from cascadelakex.gmons.ggui import runCboM2mImc
    except:
        try:
            from skylakex.users.taschell.gmons.ggui import runCboM2mImc
        except:
            print "Error: couldn't load skylakex or cascadelakex gmons."
    runCboM2mImc()

def gmonCbo():
    try:
        from cascadelakex.gmons.ggui import runCbo
    except:
        try:
            from skylakex.users.taschell.gmons.ggui import runCbo
        except:
            print "Error: couldn't load skylakex or cascadelakex gmons."
    runCbo()

def gmonCore():
    try:
        from cascadelakex.gmons.ggui import runCore
    except:
        try:
            from skylakex.users.taschell.gmons.ggui import runCore
        except:
            print "Error: couldn't load skylakex or cascadelakex gmons."
    runCore()

def gmonIIO():
    try:
        from cascadelakex.gmons.ggui import runIIO
    except:
        try:
            from skylakex.users.taschell.gmons.ggui import runIIO
        except:
            print "Error: couldn't load skylakex or cascadelakex gmons."
    runIIO()

def gmonUncore():
    try:
        from cascadelakex.gmons.ggui import runUncore
    except:
        try:
            from skylakex.users.taschell.gmons.ggui import runUncore
        except:
            print "Error: couldn't load skylakex or cascadelakex gmons."
    runUncore()

def gmonKti():
    try:
        from cascadelakex.gmons.ggui import runKti
    except:
        try:
            from skylakex.users.taschell.gmons.ggui import runKti
        except:
            print "Error: couldn't load skylakex or cascadelakex gmons."
    runKti()

def main(** kwargs):
    """
    Main entry point for setting up and starting the pmonutil utility.

    Command line key-worded arguments:

    Argument                    Value
    ========================================================
    debug                        True/False (defaults False)
    logfilename                  Desired name for log file (defaults 'pmonutil_last_run_log.txt')
    log_overwrite                True/False (defaults True)
    events_xml                   Path to file (if default not desired)
    default_events_xml           Path to file (if default not desired)
    registers_xml                Path to file (if default not desired)
    control_xml                  Path to file (if default not desired)
    initialize_all               True if you want all units to be initialized (defaults False)
    initialize_units             List of keywords that will be matched against unit names and then those units
                                 will be initialized. ex) passing in ['cbo','ha'] will initialize all cbos and has.
    counterMode                  True/False (defaults False) - Setting this to True gives very fine grained control
                                 over how counters are setup and allows for multiple instances of the pmon utilility
                                 to be run at the same time. Only use if you know what you are doing.
    """
    # reference globals
    global _DEBUG
    global __version__
    global _COUNTER_MODE
    # check the args and put defaults for missing arguements
    # see if they have a desired name for the log file
    if kwargs.has_key('logfilename') == True:
        logfilename = kwargs['logfilename']
    else:
        logfilename = 'pmonutil_last_run_log.txt'
    # see if log is in overwrite mode
    if kwargs.has_key('log_overwrite') == True:
        log_overwrite = kwargs['log_overwrite']
    else:
        log_overwrite = True
    # set up parts of the log that are indifferent to if we are in debug mode or not
    log = toolbox.getLogger('pmonutil_logger')
    log.setFile(logfilename, overwrite=log_overwrite)
    log.setFileFormat('simple')
    # check if verbose/debug mode is enabled
    if kwargs.has_key('debug') == True and kwargs['debug'] == True:
        _DEBUG = True
        log.setFileLevel('DEBUGALL')
        log.setConsoleLevel('DEBUGALL')
    else:
        log.setFileLevel('INFO')
        log.setConsoleLevel('RESULT')

    # at this point, logging is enabled

    # check if user desires to enter counterMode
    if 'counterMode' in kwargs:
        _COUNTER_MODE = kwargs['counterMode']

    # some debug info
    log.warning("DEV BUILD: Version " + __version__)
    # end debug info

    # give the user some information on the system the utility is running
    # just to make sure
    system_type = identify_system_type()
    log.result("Platform: " + system_type['Core'].upper())
    log.result("Stepping: " + system_type['Stepping'].upper())

    # set up the utility
    myLinker = eventUnitLinker(log)

    # select which xml to load
    xml_select = system_type['Core'].lower()
    print xml_select
    
    # TODO change the way the project names are found, make automatic, see Kevin Patterson's code
    # see if they would like to override the xml files
    if kwargs.has_key('events_xml') == True:
        events_xml = kwargs['events_xml']
    else:
        if xml_select == 'ivt':
            events_xml = os.path.join(XML_PATH_BASE,'ivytown','coverage','ivt_events.xml')
        elif xml_select == 'hsx':
            events_xml = os.path.join(XML_PATH_BASE,'haswellx','coverage','hsx_events.xml')
        elif xml_select == 'hsw':
            events_xml = os.path.join(XML_PATH_BASE,'haswell','coverage','hsw_events.xml')
        elif xml_select == 'bdx':
            #events_xml = os.path.join(XML_PATH_BASE,'haswellx','coverage','hsx_events.xml')
            events_xml = os.path.join(XML_PATH_BASE,'broadwellx','coverage','hsx_events.xml')
            #'\\broadwellx\\coverage\\bdx_events.xml'                
        elif xml_select == 'skx':
            events_xml = os.path.join(XML_PATH_BASE,'skylakex','coverage','skx_events.xml')
        elif xml_select == 'clx':
            events_xml = os.path.join(XML_PATH_BASE,'cascadelakex','coverage','clx_events.xml')
        elif xml_select == 'icx':
            events_xml = os.path.join(XML_PATH_BASE,'icelakex','coverage','icx_events.xml')
        elif xml_select == 'knl':
            events_xml = os.path.join(XML_PATH_BASE,'knightslanding','coverage','knl_events.xml')
        elif xml_select == 'knm':
            events_xml = os.path.join(XML_PATH_BASE,'knightslanding','coverage','knl_events.xml')
        elif xml_select == 'str':
            events_xml = os.path.join(XML_PATH_BASE,'strikeridge','coverage','str_events.xml')
        else:
            log.error("Error - Unable to decide which events XML to load.")
            raise MissingXMLException

    if kwargs.has_key('default_events_xml') == True:
        secondary_events_xml = kwargs['default_events_xml']
    else:
        if xml_select == 'ivt':
            secondary_events_xml = os.path.join(XML_PATH_BASE,'ivytown','coverage','ivt_default_events.xml')
        elif xml_select == 'hsx':
            secondary_events_xml = None
        elif xml_select == 'hsw':
            secondary_events_xml = None
        elif xml_select == 'bdx':
            secondary_events_xml = None
        elif xml_select == 'skx':
            secondary_events_xml = None
        elif xml_select == 'clx':
            secondary_events_xml = None
        elif xml_select == 'icx':
            secondary_events_xml = None
        elif xml_select == 'knl':
            secondary_events_xml = os.path.join(XML_PATH_BASE,'knightslanding','coverage','knl_default_events.xml')
        elif xml_select == 'knm':
            secondary_events_xml = os.path.join(XML_PATH_BASE,'knightslanding','coverage','knl_default_events.xml')
        elif xml_select == 'str':
            secondary_events_xml = os.path.join(XML_PATH_BASE,'strikeridge','coverage','str_default_events.xml')
        else:
            #log.error("Error - Unable to decide which default events XML to load.")
            #raise MissingXMLException
            pass

    if kwargs.has_key('registers_xml') == True:
        registers_xml = kwargs['registers_xml']
    else:
        if xml_select == 'ivt':
            registers_xml = os.path.join(XML_PATH_BASE,'ivytown','coverage','ivt.xml')
        elif xml_select == 'hsw':
            registers_xml = os.path.join(XML_PATH_BASE,'haswell','coverage','hsw.xml')
        elif xml_select == 'hsx':
            # Check if EX or EP
            if (socket.getBySocket(0)).uncore0.capid0.de_sktr1_ex == 1: # EX
                log.debug("Detected EX system.")
                registers_xml = os.path.join(XML_PATH_BASE,'haswellx','coverage','hsx_ex.xml')
            else: # EP
                registers_xml = os.path.join(XML_PATH_BASE,'haswellx','coverage','hsx.xml')
        elif xml_select == 'bdx':
            #registers_xml = os.path.join(XML_PATH_BASE,'haswellx','coverage','hsx.xml')
            registers_xml = os.path.join(XML_PATH_BASE,'broadwellx','coverage','hsx.xml')
            #'\\broadwellx\\coverage\\bdx.xml'                    
        elif xml_select == 'skx':
            registers_xml = os.path.join(XML_PATH_BASE,'skylakex','coverage','skx.xml')
        elif xml_select == 'clx':
            registers_xml = os.path.join(XML_PATH_BASE,'cascadelakex','coverage','clx.xml')
        elif xml_select == 'icx':
            registers_xml = os.path.join(XML_PATH_BASE,'icelakex','coverage','icx.xml')
        elif xml_select == 'knl':
            registers_xml = os.path.join(XML_PATH_BASE,'knightslanding','coverage','knl.xml')
        elif xml_select == 'knm':
            registers_xml = os.path.join(XML_PATH_BASE,'knightslanding','coverage','knl.xml')    
        elif xml_select == 'str':
            registers_xml = os.path.join(XML_PATH_BASE,'strikeridge','coverage','str.xml')
        else:
            log.error("Error - Unable to decide which registers XML to load.")
            raise MissingXMLException

    if kwargs.has_key('control_xml') == True:
        control_registers_xml = kwargs['control_xml']
    else:
        if xml_select == 'ivt':
            control_registers_xml = os.path.join(XML_PATH_BASE,'ivytown','coverage','ivt_control.xml')
        elif xml_select == 'hsx':
            control_registers_xml = None
        elif xml_select == 'hsw':
            control_registers_xml = None
        elif xml_select == 'bdx':
            control_registers_xml = None
        elif xml_select == 'skx':
            control_registers_xml = None
        elif xml_select == 'clx':
            control_registers_xml = None
        elif xml_select == 'icx':
            control_registers_xml = None
        elif xml_select == 'knl':
            control_registers_xml = None
        elif xml_select == 'knm':
            control_registers_xml = None
        elif xml_select == 'str':
            control_registers_xml = None
        else:
            #log.error("Error - Unable to decide which control registers XML to load.")
            #raise MissingXMLException
            pass

    if kwargs.has_key('initialize_all') == True:
        initialize_all = kwargs['initialize_all']
    else:
        initialize_all = False

    # parse in the files and the linking
    myLinker.read_events(events_xml, secondary_events_xml)
    myLinker.read_pmon_regs(registers_xml, control_registers_xml)
    myLinker.link_events_units()

    # see if we need intializing
    if initialize_all == True:
        log.result("Intializing all units.")
        for currentSocket in socket.getList():
            try:
                for unitName, unitHandle in currentSocket.pmons.globalControls._units.iteritems():
                    unitHandle._pmon_controller.initialize_for_first_use()
            except AttributeError as ae:
                pass # ignore, just means no pmons linked to that socket
        log.result("All units initialized.")
    else:
        # see if they want to initialize only some units
        if kwargs.has_key('initialize_units') == True:
            for currentSocket in socket.getList():
                try:
                    for unitName, unitHandle in currentSocket.pmons.globalControls._units.iteritems():
                        for unit_keyword in kwargs['initialize_units']:
                            if unit_keyword.lower() in unitName:
                                unitHandle._pmon_controller.initialize_for_first_use()
                except AttributeError as ae:
                    pass # ignore, means no pmons linked to that socket

    # plugins

    if xml_select == 'ivt':
        pass
    elif xml_select == 'hsx':
        import haswellx.coverage.plugins.tor_mm as tor_mm_plugin
        tor_mm_plugin.load_plugin(log)
    elif xml_select == 'hsw':
        pass
    elif xml_select == 'bdx':
        pass
    elif xml_select == 'skx':
        import skylakex.coverage.plugins.tor_mm as tor_mm_plugin
        tor_mm_plugin.load_plugin(log)
    elif xml_select == 'clx':
        import cascadelakex.coverage.plugins.tor_mm as tor_mm_plugin
        tor_mm_plugin.load_plugin(log)
    elif xml_select == 'knl':
        pass
    elif xml_select == 'knm':
        pass
    # debug info

# main classes

class eventUnitLinker(Frozen):
    """
    This class reads in all the events and pmon registers. Then it creates
    wrappers from the socket level down to the individual event/subevent.
    """

    log = None
    eventsParser = None
    pmonRegParser = None
    eventDictLoaded = None
    pmonRegDictLoaded = None

    def __init__(self, log):
        "Passes in the log and initializes the parsers."
        self.log = log
        self.eventsParser = events_parser.eventsParser(log)
        self.log.debug("Event parser created.")
        self.pmonRegParser = pmon_reg_parser.pmonRegParser(log)
        self.log.debug("Pmon register parser created.")
        # flags to keep track if the dicts are loaded in
        self.eventDictLoaded = False
        self.pmonRegDictLoaded = False
        # more flags
        self.log.debug("Event unit linker created.")

    def read_events(self, main_events_file_name, secondary_events_file_name=None):
        "Reads in the events (default events if passed in)."
        self.eventsParser.parse_main_input(main_events_file_name)
        # second file does not necessarily have to be passed in
        if secondary_events_file_name != None:
            self.eventsParser.parse_secondary_input(secondary_events_file_name)
        # clean up anything that might be corrupted
        self.eventsParser.cleanup_event_dict()
        self.eventDictLoaded = True
        self.log.info("\nRead in events dictionary.")
        #self.eventsParser.dump_events_dict("events_list.txt")

    def read_pmon_regs(self, pmon_reg_file_name, control_reg_file_name):
        "Reads in the pmon registers and the unit names."
        self.pmonRegParser.parse_pmon_regs(pmon_reg_file_name)
        #self.pmonRegParser.dump_all_pmon_regs("register_dump1.txt")

        if control_reg_file_name != None:
            self.pmonRegParser.parse_pmon_control_regs(control_reg_file_name)
        #self.pmonRegParser.dump_all_pmon_regs("register_dump2.txt")

        self.pmonRegDictLoaded = True
        self.log.info("Read in pmon registers and identified units.")

    def link_start_stop_functions_to_unit(self, unit_wrapper):
        "This function is responsible for linking start/stop functions to unts. ex) the start function to core0 for instance."
        # Mark the unit as control, this is so we can do cascading start calls
        # ex) core0.start would call thread0.start and thread1.start
        unit_wrapper._make_control_node()
        # link start function to unit
        def start_function(* args):
            """

            This function is called to start counters. You can pass in a list of counters that you wish to start. If nothing is passed in,
            all counters that are able to be started will be, that means anything in a setup or stopped state, will be started. Keep in mind
            that a counter that is empty will not be started.

            """
            # start pmons at this level if there is a pmon controller
            if unit_wrapper.__dict__.has_key('_pmon_controller') == True:
                if unit_wrapper.__dict__['_pmon_controller'] != None:
                    unit_wrapper._pmon_controller.start_pmons(list(args))
            # call the start functions of sub units
            for subUnitWrapper in unit_wrapper._control_node_list:
                subUnitWrapper.start()

        unit_wrapper._link_to_function('start', start_function)

        def stop_function(* args):
            """

            This function is called to stop counters. You can pass in a list of counters that you wish to stop. If nothing is passed in,
            all counters that are in a BUSY state will be stopped. If this would result in no counters running, then unit level freeze
            is enabled.

            """
            # stop pmons at this level if there is a pmon controller
            if unit_wrapper.__dict__.has_key('_pmon_controller') == True:
                if unit_wrapper.__dict__['_pmon_controller'] != None:
                    unit_wrapper._pmon_controller.stop_pmons(list(args))
            # call the start functions of sub units
            for subUnitWrapper in unit_wrapper._control_node_list:
                subUnitWrapper.stop()

        unit_wrapper._link_to_function('stop', stop_function)

    def link_setup_function_to_mask(self, mask_wrapper):
        "Links the setup function to the mask."

        def setup_function(** kwargs):
            """

            This function is called to setup the selected event in a pmon counter. This means the counter
            control register is ready to measure an event, but is not currently measuring the event. It takes
            the following arguments:

            counter = the number of the counter you desire the event to be programmed into. This acts as only
            a suggestion as sometimes the event will require a certain subset of counters.
            value = A value you wish to preload into the register, defaults to 0 or a unit wide default. Do a .show()
            to confirm after setup.
            valueUpper = A value you wish to preload into the upper half of the counter (if it exists)
            inverted = True/False , defaults to what the XML has for this event.
            edgedetect = True/False, defaults to what the XML has for this event.
            overflow = True/False, defaults to False
            threshold = A value you wish to set, defaults to what the XML has for this event.

            PCU specific:
            occinvert = 0 for "greater than or equal" to threshold or 1 for "less than" to threshold, used with occupancy events
            occedgedetect = 0/1, when asserted enables edge detection on the output of occupancy threshold comparison, used
            with occupancy events

            IIO specific:
            fcmask = 0/1/2   Bit 0 - Posted Requests; Bit 1 - Non-posted Requests; Bit 2 - Completions 
            chnlmask = 0x1/0x2/0x4/0x8/0x10/0x20/0x40/0x80  Channel bits are 1 hot.
            For anything that says "defaults to what the XML has", you can do a .getspec() on the event to see this value.

            An eventCounterHandle object is returned which can be used to start/stop/clear/getValue from the counter that
            the event was assigned to.

            """
            if 'counter' in kwargs:
                counter = kwargs['counter']
            else:
                counter = -1

            # inverted
            if 'inverted' in kwargs:
                inverted = kwargs['inverted']
            else:
                inverted = mask_wrapper._mask.inverted

            # edgedetect
            if 'edgedetect' in kwargs:
                edgedetect = kwargs['edgedetect']
            else:
                edgedetect = mask_wrapper._mask.edgedetect

            # overflow enable
            if 'overflow' in kwargs:
                overflow = kwargs['overflow']
            else:
                overflow = False

            # threshold
            if 'threshold' in kwargs:
                threshold = kwargs['threshold']
            else:
                threshold = mask_wrapper._mask.threshold

            # fcmask
            if 'fcmask' in kwargs:
                fcmask = kwargs['fcmask']
            else:
                fcmask = 'default'

            # chnlmask
            if 'chnlmask' in kwargs:
                chnlmask = kwargs['chnlmask']
            else:
                chnlmask = 'default'

            # start with the mask wrapper and find the first control node
            prevNode = mask_wrapper._prevNode
            while True:
                if prevNode._control_node == True:

                    # counter start value
                    if 'value' in kwargs:
                        value = kwargs['value']
                    else:
                        value = prevNode._pmon_controller.counterDefaultValue

                    # counterUpper start value
                    if 'valueUpper' in kwargs:
                        valueUpper = kwargs['valueUpper']
                    else:
                        valueUpper = prevNode._pmon_controller.counterUpperDefaultValue

                    return prevNode._pmon_controller.setup_event(mask_wrapper, counter, value, valueUpper, inverted, edgedetect, overflow, threshold, fcmask, chnlmask, kwargs)
                else:
                    prevNode = prevNode._prevNode

        mask_wrapper._link_to_function('setup', setup_function)

    def link_dump_functions_to_unit(self, unit_wrapper):
        unit_wrapper._make_control_node()
        def dump_function():
            """

            Invoke to display all the information about registers related to this unit.

            """
            unit_wrapper._pmon_controller.dump_registers()

        unit_wrapper._link_to_function('dump', dump_function)

        def dump_counter_function(* args):
            """

            Invoke with no arguments to dump basic information about all the counters. Or you can
            invoke it with a list of counters you wish to display information about.

            """
            unit_wrapper._pmon_controller.dump_counter(list(args))

        unit_wrapper._link_to_function('show', dump_counter_function)

        def counterStatus(* args):
            """

            Invoke with no arguments for all counters or a list of counters you want information for. Returns
            a list of tuples with info about the counters. Being reworked soon.

            """
            return unit_wrapper._pmon_controller.getCntrStatusValue(list(args))

        unit_wrapper._link_to_function('_counterStatus', counterStatus)

    def link_other_functions_to_unit(self, unit_wrapper):
        unit_wrapper._make_control_node()

        # clear functions

        def clearCounters(* cntrs):
            """

            If invoked with no arguments, all counters will be reset, otherwise just the counters
            specified. Resetting the counter means setting it to the currently defined default value.
            It is normally 0 unless otherwise explicitely changed previously.

            """

            unit_wrapper._pmon_controller.clear_to_default(list(cntrs))

        unit_wrapper._link_to_function('clearCounters', clearCounters)

        def clearConfigs(* cntrs):
	    ddrt_event = 0
            """

            If invoked with no arguments, all counters and their config registers will be reset, otherwise
            just the ones specified. The config registers will have their values wiped and counters will
            be set to defaults. Defaults are normally 0 unless otherwise explictely changed previously.

            """

            unit_wrapper._pmon_controller.clear_cntrs_cnfgs(list(cntrs))

        unit_wrapper._link_to_function('clearConfigs', clearConfigs)

        # set defaults functions

        def setCounterDefault(value):
            """
            Sets the default value for all counters in this unit. This value is loaded up
            when doing a setup and clears.
            """
            unit_wrapper._pmon_controller.counterDefaultValue = value

        def setCounterUpperDefault(value):
            """
            Sets the default value for all upper counters in this unit. This value is loaded up
            when doing a setup and clears.
            """
            unit_wrapper._pmon_controller.counterUpperDefaultValue = value

        def getCounterDefault():
            """
            Returns the default value for all counters in this unit.
            """
            return unit_wrapper._pmon_controller.counterDefaultValue

        def getCounterUpperDefault():
            """
            Returns the default value of all the upper counters in this unit.
            """
            return unit_wrapper._pmon_controller.counterUpperDefaultValue

        def getFixedCounterDefault():
            """
            Returns the default value of fixed counters in this unit. Warning: Not all units have fixed counters.
            """
            return unit_wrapper._pmon_controller.fixedCounterDefaultValue

        def setFixedCounterDefault(value):
            """
            Sets the default value of all fixed counters in this unit. This value is loaded up
            when doing a setup and clears. Warning: Not all units have fixed counters.
            """
            unit_wrapper._pmon_controller.fixedCounterDefaultValue = value

        unit_wrapper._link_to_function('setCounterDefault', setCounterDefault)
        unit_wrapper._link_to_function('_setCounterUpperDefault', setCounterUpperDefault)
        unit_wrapper._link_to_function('getCounterDefault', getCounterDefault)
        unit_wrapper._link_to_function('_getCounterUpperDefault', getCounterUpperDefault)
        unit_wrapper._link_to_function('_getFixedCounterDefault', getFixedCounterDefault)
        unit_wrapper._link_to_function('_setFixedCounterDefault', setFixedCounterDefault)

    def link_combo_custom_to_event(self, event_wrapper):
        "Links function that creates a mask and sets it up."

        def setupCombo(** kwargs):
            """

            This function is called to setup a combination event. This means an event with the masks you select
            ORed with each other. The mask value can be found appended to the name of each sub event ex) sub_event_0xF
            This means the counter control register is ready to measure an event, but is
            not currently measuring the event. It takes the following arguments:

            masks = [0x4,0x2,0x1] , pass in a list with the event masks you wish to OR together and setup, must
            use at least 2 masks.
            counter = the number of the counter you desire the event to be programmed into. This acts as only
            a suggestion as sometimes the event will require a certain subset of counters.
            value = A value you wish to preload into the register, defaults to 0 or a unit wide default. Do a .show()
            to confirm after setup.
            valueUpper = A value you wish to preload into the upper half of the counter (if it exists)
            inverted = True/False , defaults to what the XML has for this event.
            edgedetect = True/False, defaults to what the XML has for this event.
            overflow = True/False, defaults to False
            threshold = A value you wish to set, defaults to what the XML has for this event.

            For anything that says "defaults to what the XML has", you can do a .getspec() on any mask to see this value.

            """
            # validate input
            if 'masks' not in kwargs:
                self.log.error("Error - Must provide which masks you wish to combine.")
                return
            if len(kwargs['masks']) == 0:
                self.log.warning("Warning: No masks selected.")
                return
            if len(kwargs['masks']) == 1:
                self.log.warning("Warning: No combination generated for size 1.")
                return

            # check if they are using counter override
            if 'counter' in kwargs:
                counter = kwargs['counter']
            else:
                counter = -1

            # overflow enable
            if 'overflow' in kwargs:
                overflow = kwargs['overflow']
            else:
                overflow = False

            first = True
            combo_mask = None
            # change later for a more pretty naming scheme
            combo_name = "combination_"
            try:
                for index in kwargs['masks']:
                    maskHolder = event_wrapper._linked_to_dict[index]._mask
                    if first == True:
                        combo_mask = copy.copy(maskHolder)
                        combo_mask.description = ""
                        first = False
                    else:
                        combo_mask.mask = combo_mask.mask | maskHolder.mask
                    # retain the description of each
                    combo_mask.description += str(index) + ") " + maskHolder.description + "\n"
                    combo_name += str(index)
                    combo_mask.name = combo_name
                    # mark as a combo
                    combo_mask.isCombo = True

                mWrapper = maskWrapper(combo_mask, event_wrapper)
                # start with the mask wrapper and find the first control node
                prevNode = mWrapper._prevNode
                while True:
                    if prevNode._control_node == True:

                        # inverted
                        if 'inverted' in kwargs:
                            inverted = kwargs['inverted']
                        else:
                            inverted = mWrapper._mask.inverted

                        # edge detect
                        if 'edgedetect' in kwargs:
                            edgedetect = kwargs['edgedetect']
                        else:
                            edgedetect = mWrapper._mask.edgedetect

                        # threshold
                        if 'threshold' in kwargs:
                            threshold = kwargs['threshold']
                        else:
                            threshold = mWrapper._mask.threshold

                        # fcmask
                        if 'fcmask' in kwargs:
                            fcmask = kwargs['fcmask']
                        else:
                            if hasattr(mWrapper._mask, 'fcmask'):
                                 fcmask = mWrapper._mask.fcmask
                            else:
                                 fcmask = None

                        # chnlmask
                        if 'chnlmask' in kwargs:
                            chnlmask = kwargs['chnlmask']
                        else:
                            if hasattr(mWrapper._mask, 'chnlmask'):
                                 chnlmask = mWrapper._mask.chnlmask
                            else:
                                 chnlmask = None

                        # counter start value
                        if 'value' in kwargs:
                            value = kwargs['value']
                        else:
                            value = prevNode._pmon_controller.counterDefaultValue

                        # counterUpper value
                        if 'counterUpper' in kwargs:
                            valueUpper = kwargs['valueUpper']
                        else:
                            valueUpper = prevNode._pmon_controller.counterUpperDefaultValue

                        return prevNode._pmon_controller.setup_event(mWrapper, counter, value, valueUpper, inverted, edgedetect, overflow, threshold, fcmask, chnlmask, kwargs)

                    else:
                        prevNode = prevNode._prevNode

            except KeyError as ke:
                # catch bad keys that don't exist
                self.log.error("Error: Invalid combo index.")

        event_wrapper._link_to_function('setupCombo', setupCombo)

        def showCombos():
            """

            This function is called to show all possible combinations. The name of each combination will apear as
            umask_ with the sub event masks appended, seperated by an underscore. If you know which subevents you,
            would like to group together, simply call the setupCombo function instead.

            Warning: Calling this function will clutter the console.

            """
            if len(event_wrapper._linked_to_dict) != 1: # combos are possible if more than 1 unit
            # top level loops decides the size of the combinations generated, which we want from 2 to number of masks
            # This means we want all combos of size 2,3,4,....., number of masks
                for combo_size in range(2, len(event_wrapper._linked_to_dict) + 1):
                    # create the iterator
                    itr = itertools.combinations(event_wrapper._linked_to_dict, combo_size)
                    while True:
                        try:
                            dict_keys = itr.next()
                            combo_mask = copy.copy(event_wrapper._linked_to_dict[dict_keys[0]]._mask)
                            combo_mask.description = "\n"
                            combo_name = _COMBO_PREFIX
                            # or the mask bits
                            for specific_dict_key in dict_keys:
                                maskObject = event_wrapper._linked_to_dict[specific_dict_key]._mask
                                combo_mask.mask = combo_mask.mask | maskObject.mask
                                combo_mask.description += "umask " + hex(specific_dict_key) + " = " + maskObject.description + "\n"
                                combo_name += hex(specific_dict_key) + "_"
                            # fix the name
                            combo_name = combo_name.strip('_')
                            combo_mask.name = combo_name
                            # mark as a combo
                            combo_mask.isCombo = True
                            # create the mask wrapper
                            mWrapper = maskWrapper(combo_mask, event_wrapper)
                            event_wrapper._link_to_next(combo_name, mWrapper, -1)
                            # link setup function to it
                            self.link_setup_function_to_mask(mWrapper)

                        except StopIteration as si:
                            break

            # don't want this function called more than once
            event_wrapper._thaw()
            del event_wrapper.__dict__['showCombos']
            event_wrapper._freeze()

        event_wrapper._link_to_function('showCombos', showCombos)
        return

    def link_top_level_wrapper_functions(self, unit_wrapper):
        "Links cascading functions to top level wrappers."

        unit_wrapper._make_control_node()

        def cascadingStartFunction():
            """

            Invoke to start all SETUP/STOPPED counters in all units below.

            """

            for subUnitWrapper in unit_wrapper._control_node_list:
                subUnitWrapper.start()

        def cascadingStopFunction():
            """

            Invoke to stop all MEASURING counters in all units below.

            """

            for subUnitWrapper in unit_wrapper._control_node_list:
                subUnitWrapper.stop()

        def cascadingClearCounters():
            """

            Invoke to clear all counters to default values in all units below.

            """

            for subUnitWrapper in unit_wrapper._control_node_list:
                subUnitWrapper.clearCounters()

        def cascadingClearConfigs():
            """

            Invoke to reset all counters/configs in all units below.

            """

            for subUnitWrapper in unit_wrapper._control_node_list:
                subUnitWrapper.clearConfigs()

        unit_wrapper._link_to_function('start', cascadingStartFunction)
        unit_wrapper._link_to_function('stop' , cascadingStopFunction)
        unit_wrapper._link_to_function('clearCounters', cascadingClearCounters)
        unit_wrapper._link_to_function('clearConfigs', cascadingClearConfigs)

    def link_help_function(self, event_wrapper):
        "Links a detailed help function to show users how combos are to be used."

        def help():
            print "\nInvoke showCombos() if you want to generate all possible combinations."
            print "If you want to manually create a combination, invoke setupCombo(mask=[0x2,0x4,0x6]), where the numbers are "
            print "the umasks for the subevents. They can be found attached to the end of each subevent.\n"

        event_wrapper._link_to_function('help', help)

    def link_filter_functions(self, unit_wrapper):
        "Links a filter obejct to the unit wrapper and populates it with functions."

        # quicker reference
        pmonController = unit_wrapper._pmon_controller

        def getFilters(** kwargs):
            """

            Invoke with no arguments to return all registers as PythonSV objects.
            Invoke with a name="Name I Want" argument to search for filters with
            that sub string in their name.

            Caution: If running this in the command line, it will appear it returns integers, but
            that is not the case, it just shows the values of the registers (even though the objects
            are present, PythonSV is like that)

            """

            # check if the pmon controller has been initialized

            if pmonController.first_use == True:
                pmonController.initialize_for_first_use()

            if 'name' not in kwargs:
                return pmonController.unitFilterReg.values()
            else:
                toReturn = []
                nameToCheck = kwargs['name'].lower()
                for regNum, regName in pmonController.regNames['filter'].iteritems():
                    if nameToCheck in regName:
                        toReturn.append(pmonController.unitFilterReg[regNum])

                return toReturn

        def getFilterNames():
            """

            Invoke this function to return a list of the names of the filters associated
            with this unit.

            """

            # check if the pmon controller has been initialized
            if pmonController.first_use == True:
                pmonController.initialize_for_first_use()

            return pmonController.regNames['filter'].values()

        def showFilters(skipClear=False):
            """

            Invoke this function to show the filter objects under this filter node.
            showFilters() is only callable once.

            """
            # check if the pmon controller has been initialized
            if pmonController.first_use == True:
                pmonController.initialize_for_first_use(skipClear)

            # iterate through the filters and connect them to the filter node
            for filterNum,filter in pmonController.unitFilterReg.iteritems():
                filterNode._link_to_next(pmonController.regNames['filter'][filterNum], filter)

            # don't want this called more than once
            del filterNode.__dict__['showFilters']

        # attach the filter node
        filterNode = linkNode(unit_wrapper)
        # attach the functions to the new filter node
        filterNode._link_to_function('getFilters', getFilters)
        filterNode._link_to_function('getFilterNames', getFilterNames)
        filterNode._link_to_function('showFilters', showFilters)
        # link the filters node to the unit node
        unit_wrapper._link_to_next('filters',filterNode)

    def link_custom_event_func(self, unit_wrapper):
        "This function creates the custom event functions."

        def createCustomEvent(** kwargs):
            """

            This function is used to create custom pmon events that will appear under
            the .events attribute for this unit.

            Argument                    Value
            ========================================================

            eventCode                    Used to select the event you wish to monitor.
            subEventCode                 Code used to select a sub event. Usually 0 if the event has no sub events.
            name                         The name for this custom event.
            description                  Describe what the event measures.
            counterRestrictions          Which counters can measure this event. Entered as a list. This must be specified.
            internal                     True/False, should the internal bit be set(needed for protected events)
            filter                       True/False, should filtering logic be used
            threshold                    Threshold value (typically used for queue occupency and such)
            inverted                     True/False
            edgedetect                   True/False
            setupOnCreate                True/False (defaults to False) , True means the event will be programmed into a counter after being created(but not started)

            Example Usage
            =========================================================

            createCustomEvent(eventCode=0x2,subEventCode=0x7,name='customEvent',description="For Testing", counterRestrictions=[0,1], internal=False, Filter=False)

            """

            # create an event holder and replace the defaults
            # if the user overrides them
            eventHolder = pmonEvent()

            # grab the event code
            if 'eventCode' in kwargs:
                eventHolder.code = kwargs['eventCode']
            else:
                eventHolder.code = 0x0

            # create a subevent holder and replace the defaults
            subEventHolder = eventMask()
            subEventHolder.parentEvent = eventHolder

            # link the subEvent to the parent event
            eventHolder.masks.append(subEventHolder)

            if 'name' in kwargs:
                eventHolder.name = kwargs['name']
                subEventHolder.name = kwargs['name']
            else:
                eventHolder.name = 'nameless'
                subEventHolder.name = 'nameless'

            if 'subEventCode' in kwargs:
                subEventHolder.mask = kwargs['subEventCode']
            else:
                subEventHolder.mask = 0x0

            if 'counterRestrictions' in kwargs:
                subEventHolder.cntr_restrict = kwargs['counterRestrictions']
            else:
                subEventHolder.cntr_restrict = [0]

            if 'description' in kwargs:
                subEventHolder.description = kwargs['description']
            else:
                subEventHolder.description = 'Custom event'

            if 'internal' in kwargs:
                subEventHolder.internal = kwargs['internal']
            else:
                subEventHolder.internal = False

            if 'filter' in kwargs:
                subEventHolder.filter = kwargs['filter']
            else:
                subEventHolder.filter = False

            if 'inverted' in kwargs:
                subEventHolder.inverted = kwargs['inverted']
            else:
                subEventHolder.inverted = False

            if 'threshold' in kwargs:
                subEventHolder.threshold = kwargs['threshold']
            else:
                subEventHolder.threshold = 0

            if 'edgedetect' in kwargs:
                subEventHolder.edgedetect = kwargs['edgedetect']
            else:
                subEventHolder.edgedetect = False

            # create a wrapper for this new event and link it
            mWrapper = maskWrapper(subEventHolder, unit_wrapper.events)
            mName = pythonify_name(subEventHolder.name)
            unit_wrapper.events._link_to_next(mName , mWrapper)
            # link to pmon controller
            event_info_dict = {}
            event_info_dict['handle'] = mWrapper
            event_info_dict['name']   = mName
            event_info_dict['has_sub'] = False
            event_info_dict['is_custom'] = True

            unit_wrapper._pmon_controller.available_events.append(event_info_dict)
            # add setup function to sub event wrapper
            self.link_setup_function_to_mask(mWrapper)

            # some output info
            self.log.debug("Custom event %s created." % eventHolder.name)

            if 'setupOnCreate' in kwargs:
                setupOnCreate = kwargs['setupOnCreate']
            else:
                setupOnCreate = False

            if setupOnCreate == True:
                mWrapper.setup()

        unit_wrapper._link_to_function('createCustomEvent', createCustomEvent)

    def link_pmon_controller_shortcuts(self, unit_wrapper):
        "This function creates functions for a unit that call functions in its pmon controller object."

        def numCountersAvailable():
            "Returns the number of available counters. (Excludes fixed counters)."

            unit_wrapper._pmon_controller.initialize_for_first_use()

            return unit_wrapper._pmon_controller.countersEmpty

        unit_wrapper._link_to_function('numCountersAvailable',numCountersAvailable)

        def getEvents(** kwargs):
            """

            This function is used to retrieve events that can be run on this specific unit. The function
            accepts keyworded arguments to augment what is returned:

            Keyword                Value
            =======                ===============
            name                   An optional string you would like to match in the event's name,
                                   otherwise match on all names.

            type                   Determines if the returned events are events with or without subevents.
                                   'both','single','multiple' are accepted values. 'both' is the default.

            custom_allowed         True or False. Determines if custom events can be returned or not.

            The return value for this function is a list of dictionaries. The dictionary has 3 keys and
            1 optional key.

            Key              Value
            =====            ================
            handle           An object reference to the event itself. This is at the same level as
                             sv.socket0.pmons.cbo.cbo0.events.some_event

            name             A string with containing the name of the event.

            has_sub          A boolean denoting if the event has subevents. If false you would setup
                             the event as, event.setup(). If true, you would need to access a specific
                             subevent.

            is_custom        Always contains True if the key is present.

            """

            if 'name' in kwargs:
                event_name = kwargs['name'].lower()
            else:
                event_name = ''

            if 'custom_allowed' in kwargs:
                custom_allowed = kwargs['custom_allowed']
            else:
                custom_allowed = True

            if 'type' in kwargs:
                type = kwargs['type'].lower()
            else:
                type = 'both'

            return unit_wrapper._pmon_controller.get_events(event_name, type, custom_allowed)

        unit_wrapper._link_to_function('getEvents', getEvents)

    def link_events_units(self):
        "This function creates all of the units we need."

        error = False
        if self.eventDictLoaded == False:
            self.log.error("Attempting to link without an events dictionary.")
            error = True
        if self.pmonRegDictLoaded == False:
            self.log.error("Attempting to link without a pmon register dictionary.")
            error = True
        if error == True:
            return

        # at this point we know both dicts are loaded in
        self.log.info("\nStarting the event/pmon reg linking process.\n")

        # create wrappers for each socket and begin the linking process
        for currentSocket in socket.getAll():
            # determine if the socket is locked or not
            if currentSocket.isunlocked() == True:
                self.log.debug("Socket %d is unlocked." % currentSocket._socketNum)
            else:
                self.log.error('Error: Socket %d is locked. Some units/events may be unaccessible.' % currentSocket._socketNum)

            # make easier aliases to the dictionaries
            eventsDict = self.eventsParser.eventsDict
            pmonRegsDict = self.pmonRegParser.pmonRegs
            
            # add the pmons attribute to the socket
            pmons = pmonsLink(currentSocket)
            currentSocket.__dict__['pmons'] = pmons

            # attach a global controller to the pmons node
            # disable for HSX
            #if identify_system_type()['Core'].lower() != 'hsx':
            try: 
                searchStartPoint = currentSocket.uncore0
            except AttributeError:
                searchStartPoint = currentSocket.uncore
            globalController = global_controller(self.log, pmonRegsDict['global'][0], searchStartPoint)
            pmons._link_to_unit('globalControls', globalController, False)

            # link the unit search function from the global controller to the pmons attribute
            pmons._link_to_function('getUnits', globalController._getUnits)

            # link the program pmons function from the global controller to the pmons attribute
            pmons._link_to_function('programPmons', globalController._programPmons)
            # link the read pmons function from the global controller to the pmons attribute
            pmons._link_to_function('readPmons', globalController._readPmons)

            # link the collect data function from the global controller to pmons attribute

            # link the cores and their events
            if len(currentSocket.getcores()):
                modules = [None]
            elif len(currentSocket.getmodules()):
                # assume module based hieararchy
                modules = currentSocket.getmodules()
            else:
                self.log.error("Did not find cores/modules for core pmon in socket" + str(currentSocket._socketNum))
                modules = [None]
            
            # we need a top level container for cores
            topLevelCoreWrapper = unitWrapper(None, pmons)
            # add a reference from the pmons attribute to the top level core wrapper
            #self.log.result("Notice - Core pmons currently unsupported.")
            pmons._link_to_unit('core', topLevelCoreWrapper, True)
            # link for chained calling
            self.link_top_level_wrapper_functions(topLevelCoreWrapper)
            # iterate through the cores
            for module in modules:
                if module is None:
                    cores = currentSocket.getcores()
                else:
                    cores = module.getcores()
                    moduleWrapper = unitWrapper(module, topLevelCoreWrapper)
                    topLevelCoreWrapper._link_to_next(module._name, moduleWrapper, True)
                    # attach control functions to the thread units
                    self.link_start_stop_functions_to_unit(moduleWrapper)
                    # let the core wrapper know that the thread wrappers are control nodes also
                for core in cores:
                    coreName = core._name
                    if module is None:
                        cWrapper = unitWrapper(core, topLevelCoreWrapper)
                        # add a reference from top level container to this unit
                        topLevelCoreWrapper._link_to_next(coreName, cWrapper, True)
                    else:
                        cWrapper = unitWrapper(core, moduleWrapper)
                        # add a reference from top level container to this unit
                        moduleWrapper._link_to_next(coreName, cWrapper, True)
                    # attach control functions to the units
                    self.link_start_stop_functions_to_unit(cWrapper)
                    self.link_top_level_wrapper_functions(cWrapper)
                    # iterate through the threads
                    for thread in core.threads:
                        threadName = thread._name
                        tWrapper = unitWrapper(thread, cWrapper)
                        cWrapper._link_to_next(threadName, tWrapper, True)
                        # attach control functions to the thread units
                        self.link_start_stop_functions_to_unit(tWrapper)
                        # let the core wrapper know that the thread wrappers are control nodes also
                        cWrapper._control_node_list.append(tWrapper)
                        # attach a pmon controller to the thread
                        #print "currentSocket.%s.%s" % (coreName, threadName)
                        if module is None:
                            searchStartPoint = eval("currentSocket.%s.%s" % (coreName, threadName))
                        else:
                            searchStartPoint = eval("currentSocket.%s.%s.%s" % (module._name, coreName, threadName))
                        pmonController = pmon_controller(self.log, pmonRegsDict['core'],
                                                         searchStartPoint, core._name,
                                                         core._coreid, currentSocket._socketNum)
                        tWrapper._attach_pmon_controller(pmonController)
                        # link pmon controller shortcuts
                        self.link_pmon_controller_shortcuts(tWrapper)
                        # link thread wrapper to globalController
                        #if identify_system_type()['Core'].lower() != 'hsx':
                        if module is None:
                            globalController._addUnit(tWrapper, coreName + '_' + threadName)
                        else:
                            globalController._addUnit(tWrapper, module._name + '_' + coreName + '_' + threadName)
                        # link dump function that allows inspection of pmon registers
                        self.link_dump_functions_to_unit(tWrapper)
                        # link clear/other function
                        self.link_other_functions_to_unit(tWrapper)
                        # link filter functions to unit
                        self.link_filter_functions(tWrapper)
                        # top level events wrapper
                        topLevelEventWrapper = unitWrapper(None, tWrapper)
                        tWrapper._link_to_next('events', topLevelEventWrapper)

                        # link custom event creation function
                        self.link_custom_event_func(tWrapper)

                        # iterate through the events
                        for event in eventsDict['core']:
                            # check if the event has sub events
                            if len(event.masks) == 1:
                                # this is the simple case, we just make a mask wrapper
                                mask = event.masks[0]
                                # create a mask wrapper
                                mWrapper = maskWrapper(mask, topLevelEventWrapper)

                                # check if the name has been modified before
                                if mask.nameFrozen == False:
                                    # figure out what name the mask will have
                                    if event.name == mask.name:
                                        maskName = mask.name
                                    elif event.name == 'nameless' or event.name.strip() == '':
                                        maskName = mask.name
                                    elif event.name != mask.name:
                                        maskName = event.name + '_' + mask.name
                                    else:
                                        self.log.debug("ERROR: NAMING ERROR DETECTED. EventName: %s MaskName: %s" % (event.name,mask.name))
                                        maskName = "NAMING_ERROR"

                                    # make sure it will work
                                    maskName = pythonify_name(maskName)
                                    # mark name as final
                                    mask.nameFrozen = True
                                    # save name for later
                                    mask.name = maskName

                                else:
                                    maskName = mask.name

                                # link events wrapper to mask
                                topLevelEventWrapper._link_to_next(maskName, mWrapper)
                                # link to pmonController
                                event_info_dict = {}
                                event_info_dict['handle'] = mWrapper
                                event_info_dict['name']   = maskName
                                event_info_dict['has_sub'] = False # none of these events have sub events
                                event_info_dict['is_custom'] = False

                                pmonController.available_events.append(event_info_dict)
                                # link setup function to mask wrapper
                                self.link_setup_function_to_mask(mWrapper)
                            else:

                                # come up with a name for the event
                                if event.name == 'nameless' or event.name.strip() == '':
                                    eventName = commonSubString(event.masks[0].name, event.masks[1].name)
                                else:
                                    eventName = event.name

                                # make sure it will work
                                eventName = pythonify_name(eventName)
                                # save the name for later
                                event.name = eventName

                                # debug info
                                #self.log.debug(eventName)

                                # create event wrapper and link it to the unit
                                eWrapper = eventWrapper(event, event.code, topLevelEventWrapper)
                                topLevelEventWrapper._link_to_next(eventName, eWrapper)
                                # link to pmonController
                                event_info_dict = {}
                                event_info_dict['handle'] = eWrapper
                                event_info_dict['name']   = eventName
                                event_info_dict['has_sub'] = True # all of these events have sub events
                                pmonController.available_events.append(event_info_dict)
                                # link the combo function to the event
                                self.link_combo_custom_to_event(eWrapper)
                                # link the help function to the event
                                self.link_help_function(eWrapper)
                                # iterate through the masks
                                # generate the combo indices
                                combo_index = 0
                                for mask in event.masks:

                                    if mask.nameFrozen == False:
                                        # come up with a name for the mask
                                        maskName = mask.name.replace(eventName,'')
                                        # make sure it will work
                                        maskName = pythonify_name(maskName)
                                        # save the name for later
                                        mask.name = maskName
                                        # mark it as processed already
                                        mask.nameFrozen = True
                                    else:
                                        maskName = mask.name

                                    # some linking
                                    mWrapper = maskWrapper(mask, eWrapper)
                                    eWrapper._link_to_next(maskName, mWrapper, combo_index)
                                    # link setup function to mask wrapper
                                    self.link_setup_function_to_mask(mWrapper)
                                    # increment the combo index
                                    combo_index += 1
                                    #self.log.debug("    %s" % maskName)

            self.log.info("Done linking cores and their events to socket" + str(currentSocket._socketNum))

            # link the uncore units and their events
            # first we need to check if we have events AND pmon registers for each unit

            units_with_events = set(eventsDict.keys())
            units_with_pmon_regs = set(pmonRegsDict.keys())
            units_without_regs = units_with_events.symmetric_difference(units_with_pmon_regs)

            # warn that a unit will be ignored
            for reglessUnit in units_without_regs:
                # global isn't really a unit but the registers are passed in the same way
                # as for a unit
                if reglessUnit.lower() == 'global':
                    continue

                eventOk = eventsDict.has_key(reglessUnit)
                regOk = pmonRegsDict.has_key(reglessUnit)
                self.log.debug("Warning: Unit " + str(reglessUnit) + " Has Events: " + str(eventOk) + " Has Registers: " + str(regOk))
                self.log.debug("No events will be shown and linked for unit " + str(reglessUnit))

            # now we can link the units we have registers and events for

            valid_units = units_with_events.intersection(units_with_pmon_regs)
            # already did the ones below
            try:
                valid_units.remove('core')
                #valid_units.remove('cbo')
            except KeyError as ke:
                # not a problem if they not there already
                pass

            for unit in valid_units:

                topLevelUnitWrapper = unitWrapper(None, pmons)
                self.link_top_level_wrapper_functions(topLevelUnitWrapper)
                # make sure the name is valid
                unit_SuperName = unit.replace('/','_')
                pmons._link_to_unit(unit_SuperName, topLevelUnitWrapper, True)

                # we use the registers to identify the unit
                for unit_num, cntr_dict in pmonRegsDict[unit].items():

                    # check if we need to follow any special naming rules
                    if 'imc' in unit_SuperName:
                        unit_name = unit_SuperName + '_c' + str(unit_num)
                    else:
                        unit_name = unit_SuperName + str(unit_num)

                    # link the the pmons object
                    uWrapper = unitWrapper(unit_name, topLevelUnitWrapper)
                    # link top level wrapper to our unit
                    if hasattr(topLevelUnitWrapper, '_link_to_unit'):
                        topLevelUnitWrapper._link_to_unit(unit_name, uWrapper)
                    else:
                        topLevelUnitWrapper._link_to_next(unit_name, uWrapper, True)
                    # link units to globalController
                    #if identify_system_type()['Core'].lower() != 'hsx':
                    globalController._addUnit(uWrapper, unit_name)
                    # attach control functions to the units
                    self.link_start_stop_functions_to_unit(uWrapper)
                    # attach a pmon controller to the unit
                    pmonController = pmon_controller(self.log, pmonRegsDict[unit][unit_num], currentSocket.uncore0, unit, unit_num, currentSocket._socketNum)
                    uWrapper._attach_pmon_controller(pmonController)
                    # link pmon controller shortcuts
                    self.link_pmon_controller_shortcuts(uWrapper)
                    # link dump function that allows inspection of pmon registers
                    self.link_dump_functions_to_unit(uWrapper)
                    # link clear/other functions
                    self.link_other_functions_to_unit(uWrapper)
                    # link filter functions to unit
                    self.link_filter_functions(uWrapper)

                    # top level event container
                    topLevelEventWrapper = unitWrapper(None, uWrapper)
                    # connect the unit to the top level event wrapper
                    uWrapper._link_to_next('events', topLevelEventWrapper)
                    # link custom event creation function
                    self.link_custom_event_func(uWrapper)

                    # iterate through the events
                    for event in eventsDict[unit]:
                        # check for sub events
                        if len(event.masks) == 1:
                            # only 1 event
                            mask = event.masks[0]

                            # check if the name has been modified before
                            if mask.nameFrozen == False:
                                # figure out what name the mask will have
                                if event.name == mask.name:
                                    maskName = mask.name
                                elif event.name == 'nameless' or event.name.strip() == '':
                                    maskName = mask.name
                                elif event.name != mask.name:
                                    maskName = event.name + '_' + mask.name
                                else:
                                    self.log.debug("ERROR: NAMING ERROR DETECTED. EventName: %s MaskName: %s" % (event.name,mask.name))
                                    maskName = "NAMING_ERROR"

                                # make sure it will work
                                maskName = pythonify_name(maskName)
                                # mark name as final
                                mask.nameFrozen = True
                                # save name for later
                                mask.name = maskName

                            else:
                                maskName = mask.name

                            # create mask wrapper and link
                            mWrapper = maskWrapper(mask, topLevelEventWrapper)
                            topLevelEventWrapper._link_to_next(maskName, mWrapper)
                            # save reference to the event in the pmon controller
                            event_info_dict = {}
                            event_info_dict['handle'] = mWrapper
                            event_info_dict['name']   = maskName
                            event_info_dict['has_sub'] = False # none of these events have sub events
                            pmonController.available_events.append(event_info_dict)
                            # link setup function to mask wrapper
                            self.link_setup_function_to_mask(mWrapper)
                            # debug info
                            #self.log.debug("%s  - %s - %s" % (event.name,mask.name,maskName))

                        else:
                            # come up with a name for the event
                            if event.name == 'nameless' or event.name.strip() == '':
                                eventName = commonSubString(event.masks[0].name, event.masks[1].name)
                            else:
                                eventName = event.name

                            # make sure it will work
                            eventName = pythonify_name(eventName)
                            # save the name for later
                            event.name = eventName

                            # debug info
                            #self.log.debug(eventName)

                            # create and link the event wrapper to the unit
                            eWrapper = eventWrapper(event, event.code, topLevelEventWrapper)
                            topLevelEventWrapper._link_to_next(eventName, eWrapper)
                            # save reference to the event in the pmon controller
                            event_info_dict = {}
                            event_info_dict['handle'] = eWrapper
                            event_info_dict['name']   = eventName
                            event_info_dict['has_sub'] = True # all these events have sub events
                            pmonController.available_events.append(event_info_dict)
                            # link the combo function to the event
                            self.link_combo_custom_to_event(eWrapper)
                            # link help function to the event
                            self.link_help_function(eWrapper)
                            # iterate through the masks
                            for mask in event.masks:

                                if mask.nameFrozen == False:
                                    # come up with a name for the mask
                                    maskName = mask.name.replace(eventName,'')
                                    # make sure it will work
                                    maskName = pythonify_name(maskName)
                                    # save the name for later
                                    mask.name = maskName
                                    # mark as processed
                                    mask.nameFrozen = True
                                else:
                                    maskName = mask.name

                                # linking
                                mWrapper = maskWrapper(mask, eWrapper)
                                eWrapper._link_to_next(maskName, mWrapper, mask.mask)
                                # link setup function to mask wrapper
                                self.link_setup_function_to_mask(mWrapper)
                                # debug info
                                #self.log.debug("    %s" % maskName)

            self.log.info("Done linking units and events to their socket" + str(currentSocket._socketNum))
            # extra line for formatting
            self.log.info("")
            # uncomment the break below to only link to 1 socket
            #break
        # done linking
        self.log.info("Done linking all cores, cbos, units, sockets,and events.")

class pmon_controller(Frozen):
    """
    This class keeps track of a unit's pmon registers, which counters are in use, and schedules events to run.
    """

    log = None
    first_use = None # has first time intialization been done
    regDict = None # register dictionary
    searchStartPoint = None # where on the sv node should it begin looking for a register
    regNames = None # dictionary of the names of registers
    unitType = None # type of this unit ex) sbo,cbo,imc
    unitNumber = None # number of the unit ex) cbo1 vs cbo2, only the number
    socketNumber = None # which socket is this unit in
    isCore = None # is it a core unit
    startFromZero = None # determines if fixed counters
    registerCache = None

    # defaults

    counterDefaultValue = None # default value for counters
    counterUpperDefaultValue = None # default value for the upper counter in units with 2 physical counters that form 1 logical counter
    fixedCounterDefaultValue = None # default value for fixed counters

    # normal pmon counters
    counters = None
    countersSize = None
    counterUppers = None
    controlRegs = None
    counterStatus = None
    countersEmpty = None
    eventsSetup = None

    numNormalCounters = None # number of normal pmon counters in this unit
    numFixedCounters  = None # number of fixed pmon counters in this unit

    # control registers

    unitControlReg = None
    unitStatusReg = None
    unitFilterReg = None

    # counter states

    CNTR_EMPTY = 0
    CNTR_SETUP = 1
    CNTR_BUSY = 2
    CNTR_STOPPED = 3

    # event wrappers
    available_events = None # list of dicts of {handle,name,has_sub} and optionally is_custom

    # programmed event counter handles
    programmed_event_handles = None

    def __init__(self, log, regDict, searchStartPoint, unitType, unitNumber, socketNumber = -1):
        self.log = log
        self.first_use = True
        self.regDict = regDict
        self.searchStartPoint = searchStartPoint
        self.counterDefaultValue = 0
        self.counterUpperDefaultValue = 0
        self.numNormalCounters = 0
        self.numFixedCounters  = 0
        self.fixedCounterDefaultValue = 0

        self.unitType   = unitType
        self.unitNumber = unitNumber
        self.socketNumber = socketNumber

        self.registerCache = []

        if 'core' in unitType.lower():
            self.isCore = True
        else:
            self.isCore = False

        # debug info
#        print "Unit: " + unitType
#        print type(unitType)
#        print "Number: " + str(unitNumber)
#        print type(unitNumber)

        self.startFromZero = False
        self.available_events = []
        self.programmed_event_handles = {}

    def counter_info(self, cntrNum, returnDict = False):
        "Returns or prints out some info about a counter."

        if self.first_use == True:
            self.initialize_for_first_use()

        cntrValue = hex(self.getCounterValue(cntrNum))

        enabled = self.getCounterStatus(cntrNum)
        event = 'None'
        subevents = 'None'

        toReturn = {}

        if self.counterStatus[cntrNum] != self.CNTR_EMPTY:
            # eventsSetup[cntrNum] is a mask wrapper
            if isinstance(self.eventsSetup[cntrNum]._prevNode, unitWrapper) == True:
                # there are no subevents, just use the mask name
                event = self.eventsSetup[cntrNum]._mask.name
                toReturn['name'] = event
                toReturn['maskval'] = hex(self.eventsSetup[cntrNum]._mask.mask)
                toReturn['cluster'] = str(self.eventsSetup[cntrNum]._mask.parentEvent.cluster)
            else:
                # it is a subevent of some sort
                # event name is already pretty for us
                event = self.eventsSetup[cntrNum]._prevNode._event.name

                if self.eventsSetup[cntrNum]._mask.isCombo == False:
                    # just show the name of the mask minus the event name
                    subevents = self.eventsSetup[cntrNum]._mask.name + '_' + hex(self.eventsSetup[cntrNum]._mask.mask)
                    toReturn['name'] = event + '_' + self.eventsSetup[cntrNum]._mask.name
                    toReturn['maskval'] = hex(self.eventsSetup[cntrNum]._mask.mask)
                    toReturn['cluster'] = str(self.eventsSetup[cntrNum]._mask.parentEvent.cluster)
                else:
                    # many submasks used
                    maskChecker = self.eventsSetup[cntrNum]._mask.mask
                    subevents = ''
                    # get a list of the masks the unit could have
                    dictOfSubEvents = self.eventsSetup[cntrNum]._prevNode._linked_to_dict
                    toReturn['name'] = event
                    toReturn['maskval'] = maskChecker
                    for mask_wrapper in dictOfSubEvents.itervalues():
                        if (mask_wrapper._mask.mask & maskChecker) != 0:
                            # it is in the combo
                            name = mask_wrapper._mask.name
                            subevents += name + '_' + hex(mask_wrapper._mask.mask) + ','
                            toReturn['name'] += '_' + name
                            toReturn['cluster'] = mask_wrapper._mask.parentEvent.cluster

        if returnDict == False:
            self.log.result("Counter %d Config: %s, event=%s, subevents=%s" % (cntrNum, enabled, event, subevents.strip(',')))
            self.log.result("Counter %d Count: %s" % (cntrNum, cntrValue))
        else:
            return toReturn

    def dump_counter(self, counters=[]):
        "Look at certain counters or all of them."
        if self.first_use == True:
            self.initialize_for_first_use()

        #dump the info
        if len(counters) == 0:
            # dump all the counters
            for reg_num, counter in self.counters.iteritems():
                self.counter_info(reg_num)
        else:
            # just dump the ones they want
            for reg_num in counters:
                if reg_num in self.counters:
                    self.counter_info(reg_num)

    def getCounterValue(self, counter_num):
        if len(self.counterUppers) == 0:
            return int(self.counters[counter_num].read())
        else:
             return int((self.counterUppers[counter_num].read() << self.countersSize[counter_num]) | self.counters[counter_num].read())

    def getCounterStatus(self, reg_num):
        if self.counterStatus[reg_num] == self.CNTR_EMPTY:
            return "available"
        elif self.counterStatus[reg_num] == self.CNTR_BUSY:
            return "measuring"
        elif self.counterStatus[reg_num] == self.CNTR_SETUP:
            return "setup"
        elif self.counterStatus[reg_num] == self.CNTR_STOPPED:
            return "stopped"
        else:
            return "unknown_status"

    def getCounterStatusCode(self, reg_num):
        return self.counterStatus[reg_num]

    def getCntrStatusValue(self, cntrs=[]):
        if self.first_use == True:
            self.initialize_for_first_use()
        toReturn = []
        
        if len(cntrs) == 0:
            for reg_num in self.counters.iterkeys():
                toReturn.append((reg_num, self.getCounterStatus(reg_num), self.getCounterValue(reg_num)))
        else:
            for reg_num in cntrs:
                if reg_num in self.counters:
                    toReturn.append((reg_num, self.getCounterStatus(reg_num), self.getCounterValue(reg_num)))

        return toReturn

    def get_events(self, name_string = '', typeIn='any', custom_allowed=True):
        if self.first_use == True:
            self.initialize_for_first_use()

        name_string = name_string.lower()
        toReturn = []
        for event_item in self.available_events:
            if name_string not in event_item['name']:
                continue
            if custom_allowed == False and 'is_custom' in event_item and event_item['is_custom'] == True:
                continue
            if typeIn == 'single' and event_item['has_sub'] == True:
                continue
            if typeIn == 'multiple' and event_item['has_sub'] == False:
                continue
            toReturn.append(event_item)

        return toReturn

    def dump_info(self, cntrNum, asCSV=False):
        "Returns a bunch of information about a counter and which unit it is in."
        if self.first_use == True:
            self.initialize_for_first_use()

        toReturn = {}

        cntr_info = self.counter_info(cntrNum, True)

        toReturn['name'] = cntr_info['name']
        toReturn['maskval'] = cntr_info['maskval']
        toReturn['cluster'] = cntr_info['cluster']
        toReturn['slice']   = self.unitType + str(self.unitNumber)
        toReturn['package'] = self.socketNumber
        toReturn['threshold'] = 0
        toReturn['count'] = self.getCounterValue(cntrNum)
        toReturn['min'] = toReturn['count']
        toReturn['max'] = toReturn['count']
        toReturn['seed_count'] = 1
        toReturn['cycle_count'] = toReturn['count']
        toReturn['instr_count'] = ''
        toReturn['uop_count'] = ''
        toReturn['zero_count'] = ''
        toReturn['Clock'] = 'UCLK'
        toReturn['clock_frequency'] = 1
        toReturn['Source'] = 'Pmons'
        toReturn['ExecutionCounter'] = 1

        if asCSV == True:
            retStr = ''
            retStr += str(toReturn['cluster'])
            retStr += ',' + str(toReturn['name'])
            retStr += ',' + str(toReturn['maskval'])
            retStr += ',' + str(toReturn['slice'])
            retStr += ',' + str(toReturn['package'])
            retStr += ',' + str(toReturn['threshold'])
            retStr += ',' + str(toReturn['count'])
            retStr += ',' + str(toReturn['min'])
            retStr += ',' + str(toReturn['max'])
            retStr += ',' + str(toReturn['seed_count'])
            retStr += ',' + str(toReturn['cycle_count'])
            retStr += ',' + str(toReturn['instr_count'])
            retStr += ',' + str(toReturn['uop_count'])
            retStr += ',' + str(toReturn['zero_count'])
            retStr += ',' + str(toReturn['Clock'])
            retStr += ',' + str(toReturn['clock_frequency'])
            retStr += ',' + str(toReturn['Source'])
            retStr += ',' + str(toReturn['ExecutionCounter'])

            return retStr
        else:
            return toReturn

    def dump_registers(self):
        "Let us look at all the values in the registers."
        if self.first_use == True:
            self.initialize_for_first_use()

        # dump the unit control registers
        for reg_num, unitCtrlReg in self.unitControlReg.iteritems():
            self.log.result("\nControl " + str(reg_num))
            self.log.result("Name: " + self.regNames['unit_control'][reg_num])
            self.log.result("Value: " + hex(unitCtrlReg.read()))
            unitCtrlReg.showfields()

        # dump the unit status registers
        for reg_num, unitStatusReg in self.unitStatusReg.iteritems():
            self.log.result("\nStatus " + str(reg_num))
            self.log.result("Name: " + self.regNames['status'][reg_num])
            self.log.result("Value: " + hex(unitStatusReg.read()))
            unitStatusReg.showfields()

        # dump the filters
        for reg_num, unitFilterReg in self.unitFilterReg.iteritems():
            self.log.result("\nFilter " + str(reg_num))
            self.log.result("Name: " + self.regNames['filter'][reg_num])
            self.log.result("Value: " + hex(unitFilterReg.read()))
            unitFilterReg.showfields()

        self.log.result("")

        # dump the counters and their config regsiters
        for reg_num, counter in self.counters.iteritems():
            self.log.result("Counter %d" % reg_num)
            self.log.result("Name: " + self.regNames['counter'][reg_num])
            self.log.result("Status: " + self.getCounterStatus(reg_num))

            # check if we need to read multiple counters
            if len(self.counterUppers) == 0:
                # just one counter
                self.log.result("Value: %s" % hex(counter.read()))
                # show the fields
                counter.showfields()
            else:
                # multiple counters
                value = self.counters[reg_num].read() + self.counterUppers[reg_num].read()
                self.log.result("Value(lower and upper counters): %s" % hex(value))
                # show the fields
                counter.showfields()
                self.log.result("Name: " + self.counterUppers[reg_num].name)
                self.counterUppers[reg_num].showfields()

            self.log.result("\nConfig Name: " + self.regNames['control'][reg_num])
            self.log.result("Config Value: %s" % hex(self.controlRegs[reg_num].read()))
            self.controlRegs[reg_num].showfields()
            self.log.result("\n")

    def initialize_for_first_use(self, skipClear=False):
        """
        This function allows us to have lazy load. We only find the registers when we need them.

        Intialization Algorithm
        ---------------------------------

        1) Check for ucr access, exit if needed and unavailable.
        2) Check if address is known for status,unit_control, filter registers
            a) Find the name of the register
            b) Get the register object
            c) Make a reference to the register object
            d) Save the name of the register
            e) Write 0 to the register, incase the utility was run prior (unless skipClear is set)
            f) If the register is a unit control register, set the overflowenable and freezeenable bits to 1 if they exist.
            g) Set the freezecounters bit to 1
        3) Check if the address is known for counter and control register (fixed counters are included here also)
            a) Find the name of the register
            b) Get the register object
            c) Make a reference to the register object
            d) Save the name of the register
            e) Save the size of the counter
            e) Write default value to the counter and 0 to the control register, incase the utility was run prior (unless skipClear is set).

        """

        # check if we have already initialized
        if self.first_use == False:
            return

        global _COUNTER_MODE

        self.counters = {}
        self.countersSize = {}
        self.controlRegs = {}
        self.counterStatus = {}
        self.eventsSetup = {}
        self.counterUppers = {}
        self.unitControlReg = {}
        self.unitStatusReg = {}
        self.unitFilterReg = {}
        self.regNames = {}

        # some info
        self.log.debug("Intializing for first use.")
        #print id(self)

        # startFromZero
        # used to determine if when masking fixed counters, if we should account for zero
        self.startFromZero = False

        # find the status registers
        if 'status' not in self.regDict:
            self.log.debug("Notice: No status registers identified for this unit.")
        else:
            self.regNames['status'] = {}
            for reg_index, statusRegHandle in self.regDict['status'].iteritems():
                status_reg_name = statusRegHandle.name

                self.log.debug("Status Register %d name: %s" % (reg_index, status_reg_name))
                self.unitStatusReg[reg_index] = self.searchStartPoint.getregisterobject(status_reg_name)
                self.regNames['status'][reg_index] = status_reg_name

                if _COUNTER_MODE == False:
                    # status registers are write 1 to clear
                    #self.unitStatusReg[reg_index].write(1)
                    writeReg(self.unitStatusReg[reg_index],1,self.unitType,self.log)

            # do not worry about status and unit control registers if in counterMode
            if _COUNTER_MODE == False:
                # find the unit control registers
                if 'unit_control' not in self.regDict:
                    self.log.debug("Notice: No unit control registers identified for this unit. Ok only if the UBOX.")
                else:
                    self.regNames['unit_control'] = {}
                    for reg_index, unitCtrlHandle in self.regDict['unit_control'].iteritems():
                        unitCtrl_reg_name = unitCtrlHandle.name

                        self.log.debug("Unit Control Register %d name: %s" % (reg_index, unitCtrl_reg_name))
                        self.unitControlReg[reg_index] = self.searchStartPoint.getregisterobject(unitCtrl_reg_name)
                        self.regNames['unit_control'][reg_index] = unitCtrl_reg_name

                        # set the values for the unit control registers
                        self.resetUnitControl(reg_index)

        # find the filter registers
        self.regNames['filter'] = {}
        if 'filter' in self.regDict:
            for reg_index, filterRegHandle in self.regDict['filter'].iteritems():
                filter_reg_name = filterRegHandle.name

                self.log.debug("Filter Register %d name: %s" % (reg_index, filter_reg_name))
                self.unitFilterReg[reg_index] = self.searchStartPoint.getregisterobject(filter_reg_name)
                self.regNames['filter'][reg_index] = filter_reg_name
                if _COUNTER_MODE == False:
                    # write 0 to the register
                    #self.unitFilterReg[reg_index].write(0)
                    writeReg(self.unitFilterReg[reg_index],0,self.unitType,self.log)

        # regular pmon registers
        if 'pmon' not in self.regDict:
            self.log.error("Error - No registers of type pmon(counters) identified for this unit.")
            holder = raw_input("Press Enter to exit.")
            exit()

        self.countersEmpty = 0

        self.regNames['counter'] = {}
        self.regNames['control'] = {}

        for reg_num, reg_set in self.regDict['pmon'].iteritems():
            # see if we start from 0 or not, used to mask fixed counters
            if reg_num == 0:
                self.startFromZero = True
            # check which search mode we are using
            cntr_reg_name  = reg_set.cntrName
            cntrl_reg_name = reg_set.cnfgName

            if hasattr(reg_set, 'cntrUpperName'):
                cntrUpper_reg_name = reg_set.cntrUpperName

            # save the names
            self.regNames['counter'][reg_num] = cntr_reg_name
            self.regNames['control'][reg_num] = cntrl_reg_name

            self.log.debug("Register %d counter name: %s" % (reg_num, cntr_reg_name))
            # check for counterUpper
            try:
                self.log.debug("Register %d counterUpper name: %s" % (reg_num, cntrUpper_reg_name))
            except NameError as ne:
                # don't print anything if it isn't relevant
                pass
            self.log.debug("Register %d control name: %s" % (reg_num, cntrl_reg_name))

            self.counters[reg_num] = self.searchStartPoint.getregisterobject(cntr_reg_name)
            self.countersSize[reg_num] = int(reg_set.cntrSize)
            # see if we have to keep track of counterUpps
            try:
                self.counterUppers[reg_num] = self.searchStartPoint.getregisterobject(cntrUpper_reg_name)
                # wrtie 0 to the counterUpper
                #self.counterUppers[reg_num].write(self.counterUpperDefaultValue)
                if not skipClear:
                    writeReg(self.counterUppers[reg_num],self.counterUpperDefaultValue,self.unitType,self.log)
                del cntrUpper_reg_name # this is done to "clean" the variable from each loop iteration, so our try except way of checking for its existance works
            except NameError as ne:
                # we don't worry about it if it doesn't exist
                pass
            self.controlRegs[reg_num] = self.searchStartPoint.getregisterobject(cntrl_reg_name)
            self.counterStatus[reg_num] = self.CNTR_EMPTY
            self.eventsSetup[reg_num] = None
            self.countersEmpty += 1
            self.numNormalCounters += 1

            if _COUNTER_MODE == False:
                # write 0 to the control reg
                #self.controlRegs[reg_num].write(0)
                if not skipClear:
                    writeReg(self.controlRegs[reg_num],0,self.unitType,self.log)
                # write default value to the counter
                #self.counters[reg_num].write(self.counterDefaultValue)
                if not skipClear:
                    writeReg(self.counters[reg_num],self.counterDefaultValue,self.unitType,self.log)

        # find the fixed counters
        # treat the fixed counters like regular counters
        if 'fixed' in self.regDict:
            for reg_index, fixedRegSet in self.regDict['fixed'].iteritems():
                try:
                    # check which search mode is being used
                    fixed_cntr_name  = fixedRegSet.cntrName
                    fixed_cntrl_name = fixedRegSet.cnfgName

                    # create new index
                    index = self.numNormalCounters + reg_index

                    if self.startFromZero == False:
                        index = index + 1

                    # print out the names we found
                    self.log.debug("Fixed control %d (masked as %d) name: %s" % (reg_index, index, fixed_cntrl_name))
                    self.log.debug("Fixed counter %d (masked as %d) name: %s" % (reg_index, index, fixed_cntr_name))

                    # save the names
                    self.regNames['counter'][index] = fixed_cntr_name
                    self.regNames['control'][index] = fixed_cntrl_name

                    # get the register objects
                    self.counters[index] = self.searchStartPoint.getregisterobject(fixed_cntr_name)
                    self.controlRegs[index] = self.searchStartPoint.getregisterobject(fixed_cntrl_name)

                    # set up the registers
                    # write 0 to the control reg
                    if _COUNTER_MODE == False:
                        #self.controlRegs[index].write(0)
                        if not skipClear:
                            writeReg(self.controlRegs[index],0,self.unitType,self.log)
                        #self.counters[index].write(self.fixedCounterDefaultValue)
                        if not skipClear:
                            writeReg(self.counters[index],self.fixedCounterDefaultValue,self.unitType,self.log)

                    # flags
                    self.counterStatus[index] = self.CNTR_EMPTY
                    self.countersEmpty += 1 # treating it as a regular counter
                    self.eventsSetup[index] = None

                    # book keeping
                    self.numFixedCounters += 1

                except IndexError as ie:
                    self.log.debug("Error: No fixed counter register set found for index %d." % reg_index)
                    continue

        self.first_use = False
        # formatting
        self.log.debug("")

    def stop_pmons(self, counterNums=[]):
        """

        Counter Stop Algorithm
        ------------------------------

        1) Determine if the unit has been initialized, return if it has not
        2) If no argument is passed in, all BUSY counters will be stopped.
        3) Check if they are stopping all counters or if no counter will be measuring,
        if either condition is met, enable unit level freeze
        4) Iterate through the counters that need to be stopped, and set their enable
        bit to False.
        5) Mark the status for anything we stopped as STOPPED

        """
        if self.first_use == True:
            return

        # check if the list is empty, if so, populate it all the counter numbers
        if len(counterNums) == 0:
            for reg_num in self.counters.keys():
                counterNums.append(reg_num)

        # total counters in the unit

        total_cntrs = set(self.counters.keys())
        user_desired = set(counterNums)

        # they want to stop all counters
        if total_cntrs.issubset(user_desired) == True:
            # we want to enable unit level freeze
            for UC_num, UC_reg in self.unitControlReg.iteritems():
                self.setUnitLvlFreeze(UC_reg, True)
        else:
            # check if all counters would be stopped
            # find all counters that would be not in a busy state
            still_busy = 0
            for reg_num, cntr_status in self.counterStatus.iteritems():
                if cntr_status == self.CNTR_BUSY and (reg_num not in counterNums):
                    still_busy += 1

            if still_busy == 0:
            # we want to enable unit level freeze
                for UC_num, UC_reg in self.unitControlReg.iteritems():
                    self.setUnitLvlFreeze(UC_reg, True)

        # Iterate through our counters and set the enable bit to false if they desire to stop that counter
        # it must be in a BUSY state

        for reg_num, cntr_status in self.counterStatus.iteritems():
            if (reg_num in counterNums) and (cntr_status == self.CNTR_BUSY):
                self.setEnableBit(reg_num, False)
                self.counterStatus[reg_num] = self.CNTR_STOPPED


    def start_pmons(self, counterList=[]):
        """

        Counter Start Algorithm
        ---------------------------------

        1) Determine if the unit has been initialized, if not, exit the function.
        2) Set the enable bit to 1 for all counters we wish to start.
        3) If unit control registers exist, set their freezecounters bit to false.
        4) Mark the counter as measuring.

        """
        if self.first_use == True:
            return
            #self.initialize_for_first_use()

        # check if the list is empty, and populate it with all the counters if it is
        if len(counterList) == 0:
            for reg_num in self.counters.keys():
                counterList.append(reg_num)

        # iterate through our counters
        for reg_num, cntr_status in self.counterStatus.iteritems():
            # check if it is a counter want to start
            if (reg_num in counterList) and (cntr_status == self.CNTR_SETUP or cntr_status == self.CNTR_STOPPED):
                cntrl_reg = self.controlRegs[reg_num]
                self.log.debug("Value of the counter before: %s" % hex(self.counters[reg_num].read()))
                self.log.debug("Value of control register before: %s" % hex(cntrl_reg.read()))
                if _DEBUG == True:
                    cntrl_reg.showfields()
                # start the counter
                self.setEnableBit(reg_num, True)
                # some info
                self.log.debug("\nValue of control register after: %s" % hex(cntrl_reg.read()))
                if _DEBUG == True:
                    cntrl_reg.showfields()
                # flags
                self.counterStatus[reg_num] = self.CNTR_BUSY
                # value of counter after
                self.log.debug("Value of counter(after enable bit set, before Unit control reg set): %s" % hex(self.counters[reg_num].read()))

        # check if there are unit control registers
        if len(self.unitControlReg) != 0:
            for UC_num, UC_reg in self.unitControlReg.iteritems():
                self.log.debug("Value of unit control %d before: %s" % (UC_num, hex(UC_reg.read())))
                if _DEBUG == True:
                    UC_reg.showfields()
                # disable the freeze
                self.setUnitLvlFreeze(UC_reg, False)
                self.log.debug("Value of unit control %d after: %s" % (UC_num, hex(UC_reg.read())))
                if _DEBUG == True:
                    UC_reg.showfields()

    def markSetupStoppedAsBusy(self):
        "Marks all setup and stopped counters as busy."
        for reg_num, reg_status in self.counterStatus.iteritems():
            if reg_status == self.CNTR_SETUP or reg_status == self.CNTR_STOPPED:
                self.markCntrBusy(reg_num)

    def markBusyAsStopped(self):
        "Mark all busy counters as stopped."
        for reg_num, reg_status in self.counterStatus.iteritems():
            if reg_status == self.CNTR_BUSY:
                self.markCntrStopped(reg_num)

    def markCntrBusy(self, reg_num):
        "Mark a counter as busy."
        self.counterStatus[reg_num] = self.CNTR_BUSY

    def markCntrStopped(self, reg_num):
        "Mark a counter as stopped."
        self.counterStatus[reg_num] = self.CNTR_STOPPED

    def clear_to_default(self, cntrs=[]):
        "Resets the value of a counter or counters to the default value."

        # check if this unit has been initialized
        if self.first_use == True:
            return

        # if empty list passed in, populate it with keys of all counters
        if len(cntrs) == 0:
            for reg_num in self.counters.iterkeys():
                cntrs.append(reg_num)

        for reg_num in cntrs:
            if reg_num in self.counters:
                self.log.debug("Value of counter reg %d before: %s" % (reg_num, hex(self.counters[reg_num].read())))
                if len(self.counterUppers) != 0:
                    self.log.debug("Value of counter upper reg %d before: %s" % (reg_num, hex(self.counterUppers[reg_num].read())))
                # write default to counters
                # check for fixed counter
                if reg_num < self.numNormalCounters:
                    #self.counters[reg_num].write(self.counterDefaultValue)
                    writeReg(self.counters[reg_num],self.counterDefaultValue,self.unitType,self.log)
                else:
                    #self.counters[reg_num].write(self.fixedCounterDefaultValue)
                    writeReg(self.counters[reg_num],self.fixedCounterDefaultValue,self.unitType,self.log)
                # check for counter uppers
                if len(self.counterUppers) != 0:
                    #self.counterUppers[reg_num].write(self.counterUpperDefaultValue)
                    writeReg(self.counterUppers[reg_num],self.counterUpperDefaultValue,self.unitType,self.log)

                # display value of counter after clearing
                self.log.debug("Value of counter reg %d after: %s" % (reg_num, hex(self.counters[reg_num].read())))
                # check for counter uppers
                if len(self.counterUppers) != 0:
                    self.log.debug("Value of counter upper reg %d after: %s" % (reg_num, hex(self.counterUppers[reg_num].read())))

    def clear_cntrs_cnfgs(self, cntrs=[]):
        """

        Counter Clearing Algorithm
        ----------------------------

        1) If not initialized, return
        2) Set enable bit to 0 in the control register
        3) Write 0 to the control register
        4) Reset the counter
        5) Write default value to counter
        6) Write default value to counterUpper if the counter exists
        7) Increment our internal number of available counters
        8) Mark the counter as empty
        9) Disassociate an event with this counter

        """
        # check if they want to clear, even if not used yet.
        if self.first_use == True:
            return

        # if empty list passed in, populate it with keys of all counters
        if len(cntrs) == 0:
            for reg_num in self.counters.iterkeys():
                cntrs.append(reg_num)

        # go through and do the resetting
        for reg_num in cntrs:
            if reg_num in self.counters:
                self.log.debug("Value of control reg %d before: %s " % (reg_num, hex(self.controlRegs[reg_num].read())))
                self.log.debug("Value of counter reg %d before: %s" % (reg_num, hex(self.counters[reg_num].read())))
                if len(self.counterUppers) != 0:
                    self.log.debug("Value of counter upper reg %d before: %s" % (reg_num, hex(self.counterUppers[reg_num].read())))
                self.setEnableBit(reg_num, False)
                self.resetCounter(reg_num)
                #self.controlRegs[reg_num].write(0)
                writeReg(self.controlRegs[reg_num],0,self.unitType,self.log)
                self.log.debug("Value of control reg %d after: %s " % (reg_num, hex(self.controlRegs[reg_num].read())))
                # check for fixed counter
                if reg_num < self.numNormalCounters:
                    #self.counters[reg_num].write(self.counterDefaultValue)
                    writeReg(self.counters[reg_num],self.counterDefaultValue,self.unitType,self.log)
                else:
                    #self.counters[reg_num].write(self.fixedCounterDefaultValue)
                    writeReg(self.counters[reg_num],self.fixedCounterDefaultValue,self.unitType,self.log)
                self.log.debug("Default value written to counter %d" % reg_num)
                if len(self.counterUppers) != 0:
                    #self.counterUppers[reg_num].write(self.counterUpperDefaultValue)
                    writeReg(self.counterUppers[reg_num],self.counterUpperDefaultValue,self.unitType,self.log)
                    self.log.debug("Default value written to counter upper %d" % reg_num)
                if (self.counterStatus[reg_num] == self.CNTR_BUSY) or (self.counterStatus[reg_num] == self.CNTR_STOPPED) or (self.counterStatus[reg_num] == self.CNTR_SETUP):
                    self.countersEmpty = self.countersEmpty + 1
                self.counterStatus[reg_num] = self.CNTR_EMPTY
                self.log.debug("Value of counter %d after: %s" % (reg_num, hex(self.counters[reg_num].read())))
                if len(self.counterUppers) != 0:
                    self.log.debug("Value of counter upper %d after: %s" % (reg_num, hex(self.counterUppers[reg_num].read())))
                self.eventsSetup[reg_num] = None

                # disassociate event counter handles
                if reg_num in self.programmed_event_handles:
                    if self.programmed_event_handles[reg_num] != None:
                            self.programmed_event_handles[reg_num].validHandle = False
                            self.programmed_event_handles[reg_num] = None

        self.log.debug("Note: Filters and status registers were NOT reset.")

    def setAllUnitLvlFreeze(self, value=False):
        "Sets the unit level freeze bit to the value passed in."
        for UC_num, UC_reg in self.unitControlReg.iteritems():
            self.setUnitLvlFreeze(UC_reg, value)

    def setUnitLvlFreeze(self, register, value=False):
        if hasattr(register, 'freezecounters'):
            #register.freezecounters.write(value)
            writeReg(register.freezecounters,value,self.unitType,self.log)
        elif hasattr(register, 'freeze_counters'):
            #register.freeze_counters.write(value)
            writeReg(register.freeze_counters,value,self.unitType,self.log)
        elif hasattr(register, 'freeze'):
            #register.freeze.write(value)
            writeReg(register.freeze,value,self.unitType,self.log)
        elif len(filter(lambda x: x.endswith('_freeze'), register.fields)):
            writeReg(register.getfieldobject(filter(lambda x: x.endswith('_freeze'), register.fields)[0]),value,self.unitType,self.log)
        else:
            self.log.error("Error - Unable to find the counter freeze bit in the unit control register.")

    def setAllEnableBit(self, status_match, valueToSet):
        "Sets all enable bits to the desired value if they match the status we are looking for."
        for reg_num, reg_status in self.counterStatus.iteritems():
            if reg_status == status_match:
                self.setEnableBit(reg_num, valueToSet)

    def setEnableBit(self, cntr_num, valueToSet):
        cntrl_reg = self.controlRegs[cntr_num]
        if cntr_num >= self.numNormalCounters:
            # fixed counter. Check for enable field in fixed ctrl register

            # determine fixed counter index
            fixed_cntr = cntr_num - self.numNormalCounters

            # now look for field matching enable for this counter in the control register
            if len(filter(lambda x: x.startswith('en_ctr%d'%fixed_cntr), cntrl_reg.fields)):  # HSX
                writeReg(cntrl_reg.getfieldobject(filter(lambda x: x.startswith('en_ctr%d'%fixed_cntr), cntrl_reg.fields)[0]),valueToSet,self.unitType,self.log)
            elif len(filter(lambda x: x.endswith('%d_enable'%fixed_cntr), cntrl_reg.fields)):    # KNL
                writeReg(cntrl_reg.getfieldobject(filter(lambda x: x.endswith('%d_enable'%fixed_cntr), cntrl_reg.fields)[0]),valueToSet,self.unitType,self.log)
            else:
                self.log.error("Error - Unable to set enable bit, can't find counter enable field for this fixed counter (%d) in the config register. (%s)"%(fixed_cntr, cntrl_reg.name))
            return

        if hasattr(cntrl_reg, 'counteren'):
            #cntrl_reg.counteren.write(valueToSet)
            writeReg(cntrl_reg.counteren,valueToSet,self.unitType,self.log)
        elif hasattr(cntrl_reg, 'counter_enable'):
            #cntrl_reg.counter_enable.write(valueToSet)
            writeReg(cntrl_reg.counter_enable,valueToSet,self.unitType,self.log)
        elif hasattr(cntrl_reg, 'counterenable'):
            #cntrl_reg.counterenable.write(valueToSet)
            writeReg(cntrl_reg.counterenable,valueToSet,self.unitType,self.log)
        elif hasattr(cntrl_reg, 'enable_bit'):
            #cntrl_reg.enable_bit.write(valueToSet)
            writeReg(cntrl_reg.enable_bit,valueToSet,self.unitType,self.log)
        elif hasattr(cntrl_reg, 'enable_flag'):
            #cntrl_reg.enable_flag.write(valueToSet)
            writeReg(cntrl_reg.enable_flag,valueToSet,self.unitType,self.log)
        elif len(filter(lambda x: x.endswith('_en'), cntrl_reg.fields)):
            #cntrl_reg.counteren.write(valueToSet)
            writeReg(cntrl_reg.getfieldobject(filter(lambda x: x.endswith('_en'), cntrl_reg.fields)[0]),valueToSet,self.unitType,self.log)
        else:
            self.log.error("Error - Unable to set enable bit, can't find counter enable field in the config register. (%s)"%cntrl_reg.name)

    def resetCounter(self, cntr_num):
        cntrl_reg = self.controlRegs[cntr_num]
        if hasattr(cntrl_reg, 'counterreset'):
            #cntrl_reg.counterreset.write(True)
            writeReg(cntrl_reg.counterreset,True,self.unitType,self.log)
        elif hasattr(cntrl_reg, 'counter_reset'):
            #cntrl_reg.counter_reset.write(True)
            writeReg(cntrl_reg.counter_reset,True,self.unitType,self.log)
        elif len(filter(lambda x: x.endswith('_rst'), cntrl_reg.fields)):
            #cntrl_reg.counteren.write(valueToSet)
            writeReg(cntrl_reg.getfieldobject(filter(lambda x: x.endswith('_rst'), cntrl_reg.fields)[0]),True,self.unitType,self.log)
        else:
            self.log.debug("Notice: Unable to reset the counter, can't find counter reset field. Manually setting the value.")

    def resetUnitControl(self, reg_index):
        #write 0 to the register
        #self.unitControlReg[reg_index].write(0)
        writeReg(self.unitControlReg[reg_index],0,self.unitType,self.log)
        # check for overflowenable and set it to 1
        if hasattr(self.unitControlReg[reg_index], 'overflowenable'):
            #self.unitControlReg[reg_index].overflowenable.write(1)
            writeReg(self.unitControlReg[reg_index].overflowenable,1,self.unitType,self.log)
        elif hasattr(self.unitControlReg[reg_index], 'overflow_enable'):
            #self.unitControlReg[reg_index].overflow_enable.write(1)
            writeReg(self.unitControlReg[reg_index].overflow_enable,1,self.unitType,self.log)
        else:
            self.log.debug("Notice: Unit control register has no overflowenable field, treated as 1 logically.")
        # check for freezeenable and set it to 1
        if hasattr(self.unitControlReg[reg_index], 'freezeenable'):
            #self.unitControlReg[reg_index].freezeenable.write(1)
            writeReg(self.unitControlReg[reg_index].freezeenable,1,self.unitType,self.log)
        elif hasattr(self.unitControlReg[reg_index], 'freeze_enable'):
            #self.unitControlReg[reg_index].freeze_enable.write(1)
            writeReg(self.unitControlReg[reg_index].freeze_enable,1,self.unitType,self.log)
        else:
            self.log.debug("Notice: Unit control register has no freezeenable field, treated as 1 logically.")
        # check for the freezecounters bit and set it to 1
        if hasattr(self.unitControlReg[reg_index], 'freezecounters'):
            #self.unitControlReg[reg_index].freezecounters.write(1)
            writeReg(self.unitControlReg[reg_index].freezecounters,1,self.unitType,self.log)
        elif hasattr(self.unitControlReg[reg_index], 'freeze_counters'):
            #self.unitControlReg[reg_index].freeze_counters.write(1)
            writeReg(self.unitControlReg[reg_index].freeze_counters,1,self.unitType,self.log)
        elif len(filter(lambda x: x.endswith('_freeze'), self.unitControlReg[reg_index].fields)):
            #self.unitControlReg[reg_index].freeze_counters.write(1)
            writeReg(self.unitControlReg[reg_index].getfieldobject(filter(lambda x: x.endswith('_freeze'), self.unitControlReg[reg_index].fields)[0]),1,self.unitType,self.log)
        else:
            self.log.debug("Notice: Unit control register has no freezecounters field.")

        # mark the event counter handle
        if reg_index in self.programmed_event_handles:
            if self.programmed_event_handles[reg_index] != None:
                self.programmed_event_handles[reg_index].validHandle = False
                self.programmed_event_handles[reg_index] = None

    def setup_event(self, maskWrapper, counter, value, valueUpper, inverted, edgedetect, overflow, threshold, fcmask, chnlmask, kwargs):
        """

        The steps in setting up a counter are as follows:

        Intialization
        --------------------------------------
        1) check if counters/register have been initialized, if not, call initialize_for_first_use() (within the pmon_controller class)

        Fixed Counter Setup Algorithm
        --------------------------------------
        1) Confirm the event is a fixed event.
        2) Check if the fixed counter is available, raise Exception if not
        3) Write 0 to the control register and default_value to the counter
        4) Mark counter as SETUP
        5) save eventCounterHandle and then return it

        Normal Counter Programming Algorithm
        --------------------------------------

        Counter Selection Algorithm
        ---------------------------------------
        1) check if any counters are available, if not, print error and raise Exception
        2) check if the event/subevent has counter restrictions.
            a) no counter restrictions
                i) check if the user had a preference (counter = -1 means no preference, and is the default function argument value)
                    A) check if the counter they want exists (aka its a valid counter number), print warning and raise Exception if doesn't exist
                    B) check if the counter they want is available
                        I) pick that counter if it is
                        II) if not available, issue a warning, and pick any available counter
                ii) if no preference, just iterate through the counters and pick the first available counter
            b) with counter restrictions
                i) create two sets, one of available counters and one of counters that can accept the event/subevent
                ii) intersect the sets to form a set of available and acceptable counters
                iii) if this intersection is of size 0, report error and raise Exception
                iv) check if the user has a prefered counter
                    A) check if that counter is a real counter, print error and raise Exception if not
                    B) if the user desired counter is in the set, pick that as the counter to be used
                    C) if the desired counter is not available, we arbitrarly pick a counter from the set
                v) no user prefered counter we arbitrarly pick a counter from the set
        3) print out a debug message with the number of the counter chosen

        Counter and Config register Setup Algorithm
        --------------------------------------
        1) Set the enable bit of the control register to 0 (false) which disables the counter. If the counter was already
        stopped nothing happens, if it was counting, it now stops. Done by calling setEnableBit()
        2) Issue a counter reset signal from the control register, done by wrting 1 to counter reset bit field in the
        counter config register. If this field isn't found, just outputs a debug warning, setup process continues. Done
        by calling resetCounter()
        3) We write 0 to the control register, so there is nothing residual from past events programmed into this control
        register.
        4) Write the event code to the control register.
        5) Write the umask to the control register.
        6) Set the edge detect bit field in the control register.
        7) Set the inverted bit field in the control register.
        8) Set the threshold bit field in the control register.
        9) Set the fcmask bit field in the control register.
        10) Set the chnlmask bit field in the control register.
        11) Set the internal bit field in the control register.
        12) Set the overflow enable bit field in the control register.
        13) pmon_controller class marks the counter as CNTR.SETUP
        14) Associate a reference of the maskWrapper ( wrapper that holds a reference the eventMask class, that holds
        all the counter programming information for that event)
        15) pmon_controller decrements the number of available counters.
        16) Set the value of the counter to the value passed in. (Value passed in is either user specificed or a default)
            a) If there is an upper counter associated with this counter, it is set to value passed in. (Value passed in is either user specified or a default)

        17) Save internal reference to eventCounterHandle and then return it

        """

        # _DEBUG is a global, and is set by pu.main()
        global _DEBUG
        global ddrt_event
        global non_ddrt_event
        if self.first_use == True:
            self.initialize_for_first_use()
        
        # quicker reference to the maskHolder
        maskHolder = maskWrapper._mask

        if self.countersEmpty == 0:
            self.log.error("Error - No available counters.")
            raise NoAvailableCountersException("There are no available counters.")

        # check if it is a fixed event
        if maskHolder.parentEvent.type == 'fixed':
            # get the index internal to the utility
            fixedIndex = maskHolder.cntr_restrict[0] + self.numNormalCounters
            if self.startFromZero == False:
                fixedIndex = fixedIndex + 1

            # check if the counter is available
            if self.counterStatus[fixedIndex] != self.CNTR_EMPTY:
                self.log.debug("Error - This event requires certain counters and none are available.")
                raise NoAvailableCountersException("This event requires certain counters and none are available.")

            self.log.debug("Value of control reg before: %s " % hex(self.controlRegs[fixedIndex].read()))
            ctrlReg = self.controlRegs[fixedIndex]
            cntrlReg.write(0)
            self.log.debug("Value of control reg after: %s " % hex(self.controlRegs[fixedIndex].read()))
            self.log.debug("Value of counter before: %s " % hex(self.counters[fixedIndex].read()))
            cntrReg = self.counters[fixedIndex]
            cntrReg.write(self.fixedCounterDefaultValue)
            self.log.debug("Value of counter after: %s " % hex(self.counters[fixedIndex].read()))
            # set some flags
            self.counterStatus[fixedIndex] = self.CNTR_SETUP
            self.eventsSetup[fixedIndex] = maskWrapper
            self.countersEmpty = self.countersEmpty - 1

            # save and return an eventCounterHandle object
            ech = eventCounterHandle(self.log, self, fixedIndex)
            self.programmed_event_handles[fixedIndex] = ech

            return ech

        # check if there are counter restrictions
        if len(maskHolder.cntr_restrict) == 0: # none, we just need to find an open counter
            # see if they had a prefered counter, if so, check it and use it if it is available
            if counter != -1:
                # check if the counter key even exists
                if counter not in self.counters:
                    self.log.error("Error - That counter number does not exist.")
                    raise InvalidCounterIndexException("Counter index %s is invalid." % str(counter))
                # check if the desired counter is available
                if self.counterStatus[counter] == self.CNTR_EMPTY:
                    # good to go, we can use this counter
                    cntr_num_to_use = counter
                else: 
                    self.log.warning("Warning: The counter you wanted is already taken, but we found another that works.")
                    for cntr_num, cntr_status in self.counterStatus.iteritems():
                        if cntr_status == self.CNTR_EMPTY:
                            cntr_num_to_use = cntr_num
                            break
            else: # no prefered counter, just find one
                for cntr_num, cntr_status in self.counterStatus.iteritems():
                    if cntr_status == self.CNTR_EMPTY:
                        cntr_num_to_use = cntr_num
                        break

        else: # we have to go through and see if one of the ones we need is available
            emptyCounters = []
            for cntr_num, cntr_status in self.counterStatus.iteritems():
                if cntr_status == self.CNTR_EMPTY:
                    emptyCounters.append(cntr_num)

            emptyCounters = set(emptyCounters)
            allowedCounters = set(maskHolder.cntr_restrict)

            intersection = emptyCounters.intersection(allowedCounters)

            if len(intersection) == 0:
                self.log.debug("Error - This event requires certain counters and none are available.")
                raise NoAvailableCountersException("This event requires certain counters and none are available.")

            # check if they have a prefered counter
            if counter != -1:
                if counter not in self.counters:
                    self.log.error("Error - That counter number does not exist.")
                    raise InvalidCounterIndexException("Counter index  %s is invalid." % str(counter))
                if counter in intersection:
                    cntr_num_to_use = counter
                else:
                    self.log.warning("Warning: The counter you wanted wasn't available, so we picked another for you.")
                    cntr_num_to_use = intersection.pop()
            else:
                cntr_num_to_use = intersection.pop()

        self.log.debug("Counter %d chosen.\n " % cntr_num_to_use)


        # quicker handle to the control register
#ddrt event selects with programming restriction for A-0
#234 235 236 237 226 225 227 224 230 229 231 228 232 233  
#224 225 226 227 228 229 230 231 232 233 234 235 236 237 
# due to bug in A-0 with scheduleing.  DDRT eventselects mut be programming in the preceeding pmon ctrl register. 
# e.g.  for counter 0 event select is programmed in pmon cntrl 4 reg.
# e.g.  for counter 1 event select is programmed in pmon cntrl 0 reg.
# e.g.  for counter 2 event select is programmed in pmon cntrl 1 reg.
# e.g.  for counter 3 event select is programmed in pmon cntrl 2 reg.
# the only restriction is that DDRT events that follow a non-ddrt event will cause the non-ddrt event not to be setup correctly.
        system_type = identify_system_type()
        mpe=maskHolder.parentEvent.code
        if system_type['Core'].upper() == 'SKX' and ( system_type['Stepping'].upper() in ['A0','A1','A2'] ) and \
                ( mpe > 223 and mpe < 238) and self.isCore == False and maskHolder.parentEvent.cluster.upper() == 'IMC':
            #223 -238 Are DDRT pmon events.
            cntrl_reg = self.controlRegs[cntr_num_to_use]
            cntrl_reg_1 = self.controlRegs[cntr_num_to_use+1]
        else:
            cntrl_reg = self.controlRegs[cntr_num_to_use]

        self.log.debug("Value of counter before anything: %s" % hex(self.counters[cntr_num_to_use].read()))
        if _DEBUG == True:
            self.counters[cntr_num_to_use].showfields()

        if len(self.counterUppers) != 0:
            self.log.debug("Value of counterUpper before anything: %s" % hex(self.counterUppers[cntr_num_to_use].read()))
            if _DEBUG == True:

                self.counterUppers[cntr_num_to_use].showfields()

        if _DEBUG == True:
            self.log.debug("\nValue of control register before setup: %s" % hex(cntrl_reg.read()))
            cntrl_reg.showfields()

        # disable the counter first via the counter control register
        self.setEnableBit(cntr_num_to_use, False)
        # reset the counter
        self.log.debug("\nCounter being reset. Trying to hit the reset bit field in the config register.")
        self.resetCounter(cntr_num_to_use)
       
       
        # check for PCU special case
        if maskHolder.parentEvent.code == 128 and self.isCore == False and maskHolder.parentEvent.cluster.upper() == 'PCU':
            self.log.debug("Event identified as a special PCU event.")

            # occupancy event
            cntrl_reg.eventselect.store(0)
            # set occupancy field properly
            cntrl_reg.useoccupancy.store(1)

            # check if any other ccupancy fields need to be written to
            if 'occinvert' in kwargs:
                cntrl_reg.occinvert.store(kwargs['occinvert'])
            if 'occedgedetect' in kwargs:
                cntrl_reg.occedgedetect.store(kwargs['occedgedetect'])

        else:
            eventStrs = ['evslct','event_select','eventselect','_evsel','event_id']
            eventName = findField(eventStrs,cntrl_reg.fields)

            mpe=maskHolder.parentEvent.code
            if eventName == None:
                self.log.error("Error - Unable to identify the event selection field to program the config register.")
                raise InvalidRegisterFieldException("Unable to identify the event selection field to program the config register.")

            elif eventName == 'eventselect' and system_type['Core'].upper() == 'SKX' and (system_type['Stepping'].upper() in ['A0','A1','A2'] ) and \
                 ( mpe > 223 and mpe < 238) and self.isCore == False and maskHolder.parentEvent.cluster.upper() == 'IMC':
                '''W/A is to program the eventsel in the next counters config
                need to also program it in the current counter so it is not left at 0.
                 if left at 0 that is the event code for ddrclockticks and that event will be counted.
                 instead of the DDRT event.
                cntrl_reg.eventselect = maskHolder.parentEvent.code '''
                cntrl_reg_1.eventselect.write(maskHolder.parentEvent.code)
                cntrl_reg.eventselect.store(maskHolder.parentEvent.code)
            else:
                cntrl_reg.getfieldobject(eventName).store(maskHolder.parentEvent.code)
                
        maskStrs = ['unitmask','unit_mask','event_mask','_umask']
        maskName = findField(maskStrs,cntrl_reg.fields)
        if maskName:
            cntrl_reg.getfieldobject(maskName).store(maskHolder.mask)
        else:
            self.log.debug("Warning - Unable to identify the mask field to program the config register. OK if the PCU.")
            if maskHolder.parentEvent.code == 128 and self.isCore == False and maskHolder.parentEvent.cluster.upper() == 'PCU':
                self.log.debug("Programming occupancy select for PCU.")
                cntrl_reg.occselect.store(maskHolder.mask >> 6)

        edgeStrs = ['edgedet','edge_detect','edgedetect','edge_detect_flag','_ed']
        edgeName = findField(edgeStrs,cntrl_reg.fields)
        if edgeName:
            cntrl_reg.getfieldobject(edgeName).store(edgedetect)
        else:
            self.log.error("Error - Unable to identify the edge detect field to program the config register.")
            raise InvalidRegisterFieldException("Unable to identify the edge detect field to program the config register.")

        invertStrs = ['invert','_inv']
        invertName = findField(invertStrs,cntrl_reg.fields)
        if invertName:
            cntrl_reg.getfieldobject(invertName).store(inverted)
        else:
            self.log.error("Error - Unable to identify the invert field to program the config register.")
            raise InvalidRegisterFieldException("Unable to identify the invert field to program the config register.")

        threshStrs = ['threshold','count_mask','_thresh']
        threshName = findField(threshStrs, cntrl_reg.fields)
        if threshName:
            cntrl_reg.getfieldobject(threshName).store(threshold)
        else:
            self.log.error("Error - Unable to identify the threshold field to program the config register.")
            raise InvalidRegisterFieldException("Unable to identify the threshold field to program the config register.")

        if hasattr(cntrl_reg, 'fcmask'):
            if fcmask == 'default':
                cntrl_reg.fcmask.store(cntrl_reg.fcmask.default)
            else:
                cntrl_reg.fcmask.store(fcmask)

        if hasattr(cntrl_reg, 'chnlmask'):
            if chnlmask == 'default':
                cntrl_reg.chnlmask.store(cntrl_reg.chnlmask.default)
            else:
                cntrl_reg.chnlmask.store(chnlmask)

        if hasattr(cntrl_reg, 'internal'):
            cntrl_reg.internal.store(maskHolder.internal)
        elif maskHolder.internal == True:
                self.log.debug("\nNotice: Event mask specifies internal bit to be set, but the control register has no internal field bit.")
        else:
            pass

        ovfStrs = ['overflowenable','ovfenable','ovfen','overflow_enable','_oven']
        ovfName = findField(ovfStrs, cntrl_reg.fields)
        if ovfName:
            cntrl_reg.getfieldobject(ovfName).store(overflow)
        else:
            self.log.debug("\nNotice: Unable to identify overflow enable field.")

        if 'tidfilterenable' in kwargs:
                if hasattr(cntrl_reg,'tidfilterenable'):
                    cntrl_reg.tidfilterenable.store(kwargs['tidfilterenable'])
                    self.log.debug('Notice: Value of tidfilterenable written to.')

        if self.isCore == True:
            modeStrs = ['usr','user_mode_flag','os_mode_flag']
            modeName = findField(modeStrs, cntrl_reg.fields)
            if modeName:
                cntrl_reg.getfieldobject(modeName).store(1)

        #Due to skx ddrt A-x bug, we use the current counters eventselect from the next counter. so do not clear the register. 
        if system_type['Core'].upper() == 'SKX' and ( system_type['Stepping'].upper() in ['A0','A1','A2'] ):
            if not(( mpe > 223 and mpe < 238) and self.isCore == False and maskHolder.parentEvent.cluster.upper() == 'IMC'):
                # write 0 to the control register in case we forget to default some field
                if kwargs.has_key('modify_ctrl_reg') == True and kwargs['modify_ctrl_reg'] == False:
                    self.log.debug("\n Not clearing control register due to user input")
                    cntrl_reg.flush()
                else:
                    self.log.debug("\n Clearing control register fields merged with field writes")
                    cntrl_reg.flush(skipRead=True)
        else:    
            if kwargs.has_key('modify_ctrl_reg') == True and kwargs['modify_ctrl_reg'] == False:
                self.log.debug("\n Not clearing control register due to user input")
                cntrl_reg.flush()
            else:
                self.log.debug("\n Clearing control registers")
                cntrl_reg.flush(skipRead=True)

        self.log.debug("\nValue of control register after setup: %s" % hex(cntrl_reg))


        if _DEBUG == True:
            self.log.debug("\nValue of control register after setup: %s" % hex(cntrl_reg.read()))
            cntrl_reg.showfields()

        # set the appropriate flags
        self.counterStatus[cntr_num_to_use] = self.CNTR_SETUP
        self.eventsSetup[cntr_num_to_use] = maskWrapper
        self.countersEmpty = self.countersEmpty - 1

        self.counters[cntr_num_to_use].write(value)
        if len(self.counterUppers) != 0:
            self.log.debug("\nCounter Upper set to 0.")
            self.counterUppers[cntr_num_to_use].write(valueUpper)

        self.log.debug("\nValue of counter after setup: %s" % hex(self.counters[cntr_num_to_use].read()))
        if _DEBUG == True:
            self.counters[cntr_num_to_use].showfields()

        if len(self.counterUppers) != 0:
            self.log.debug("Value of counterUppers aftr setup: %s" % hex(self.counterUppers[cntr_num_to_use].read()))
            if _DEBUG == True:
                self.counterUppers[cntr_num_to_use].showfields()


        # save and return an eventCounterHandle
        ech = eventCounterHandle(self.log, self, cntr_num_to_use)
        self.programmed_event_handles[cntr_num_to_use] = ech
        return ech

def findField(possibleStrings, fields):
    for fieldSubStr in possibleStrings:
        for field in fields:
            if fieldSubStr in field:
                return(field)
    return(None)


class eventCounterHandle(Frozen):
    """

    This class is a convenient object wrapper for controlling and accessing a certain event/counter combination.

    """

    _log = None
    _pmonController = None
    _counterNum = None
    _eventName  = None
    _eventMask = None
    validHandle = None

    def __init__(self,log, pmonController, counterNum, eventName = 'Unknown',eventMask='Unknown'):
        self._log = log
        self._pmonController = pmonController
        self._counterNum = counterNum
        self._eventName = eventName
        self._eventMask = eventMask
        self.validHandle = True

    def _checkHandleValid(self):
        "Checks if the eventCounterHandle is valid, throws an exception if it is not."
        if self.validHandle == False:
            self._log.error("Error - Pmon configuration was cleared and this object is now out-dated.")
            raise ExpiredEventCounterHandleException("Pmon configuration was cleared and this object is now out-dated")

    def start(self):
        "Starts the counter and allows measuring of the selected event."
        self._checkHandleValid()
        self._pmonController.start_pmons([self._counterNum])

    def stop(self):
        "Stops the counter from measuring."
        self._checkHandleValid()
        self._pmonController.stop_pmons([self._counterNum])

    def clearCounter(self):
        "Clears the counter to default value, normally 0 unless specifically changed."
        self._checkHandleValid()
        self._pmonController.clear_to_default([self._counterNum])

    def clearConfig(self):
        "Clears the config register and resets the counter to a default value. This object should not be used after this method is called."
        self._checkHandleValid()
        self._pmonController.clear_cntrs_cnfgs([self._counterNum])
        self.validHandle = False

    def isMeasuring(self):
        "Returns TRUE if the counter is measuring, FALSE otherwise."
        self._checkHandleValid()
        if self._pmonController.getCounterStatusCode(self._counterNum) == self._pmonController.CNTR_BUSY:
            return True
        else:
            return False

    def getValue(self):
        "Returns the value currently in the counter."
        self._checkHandleValid()
        return self._pmonController.getCounterValue(self._counterNum)

    def dumpInfo(self):
        "Returns various information about this event/counter as a dictionary."
        self._checkHandleValid()
        return self._pmonController.dump_info(self._counterNum, False)

    def dumpCSV(self):
        "Returns a CSV string for printing to files."
        self._checkHandleValid()
        return self._pmonController.dump_info(self._counterNum, True)

class global_controller(Frozen):
    """

    This class represents a node for global control and all the
    associated functions needed.

    """

    _log = None
    _regDict = None
    _searchStartPoint = None
    _globalCntrlReg = None
    _gcRegName = None
    _globalStatusReg = None
    _gsRegName = None

    _units = None

    def __init__(self, log, regDict, searchStartPoint):
        "initializes the registers we need for global controls."

        self._log = log
        self._regDict = regDict
        self._searchStartPoint = searchStartPoint
        self._units = {}

        # determine if its called global_control or unit_control
        if 'global_control' in self._regDict:
            access_key = 'global_control'
        else:
            access_key = 'unit_control'

        # we will go ahead and find the registers
        self._gcRegName = self._regDict[access_key][0].name

        self._globalCntrlReg = self._searchStartPoint.getregisterobject(self._gcRegName)
        #self._globalCntrlReg.write(0x0)
        writeReg(self._globalCntrlReg,0x0,'globalControl',self._log)
        self._log.debug("Global Control Name: " + self._gcRegName)
        if _DEBUG:
            self._globalCntrlReg.showfields()

        # get the name of the status register
        self._gsRegName = self._regDict['status'][0].name

        self._globalStatusReg = self._searchStartPoint.getregisterobject(self._gsRegName)
        #self._globalStatusReg.write(0xFFFFFFFF) # write 1 to clear, to all bits
        self._log.debug("Notice: Global status counter NOT being reset.")
        self._log.debug("Global Status Name: " + self._gsRegName)
        if _DEBUG:
            self._globalStatusReg.showfields()

        self._log.debug("Global unfreeze being called to reset state.")
        self._unfreeze()

    def _addUnit(self, unitHandle, unitName):
        "Adds a unit under this global controllers control."
        self._units[unitName] = unitHandle

    def start(self):
        """

        This function is called to globally start all setup counters at the same time. If you
        are using this function, you should NOT be manually starting/stop units/individual counters.
        This is a batch mode start.

        """

        for unit_name, unit in self._units.iteritems():
#            if 'core' in unit_name:
#                self._log.debug("Skipping setting unit lvl freeze for core.")
#                continue

            # quicker refernece
            PC = unit._pmon_controller

            if PC.first_use == False:
                self._log.debug("Setting unit level freeze to FALSE for unit: " + unit_name)
                PC.setAllUnitLvlFreeze(False)

        # freeze so we can set the enables without the counters starting
        self._freeze()

        for unit_name, unit in self._units.iteritems():
#            if 'core' in unit_name:
#                self._log.debug("Skipping starting cores.")
#                continue

            # quicker refernece
            PC = unit._pmon_controller

            if PC.first_use == False:
                self._log.debug("Setting enables and status for unit: " + unit_name)
                PC.setAllEnableBit(PC.CNTR_SETUP, True)
                PC.setAllEnableBit(PC.CNTR_STOPPED, True)
                PC.markSetupStoppedAsBusy()

        self._unfreeze()

    def stop(self):
        """

        This function is called to globally stop all setup counters at the same time. If you
        are using this function, you should NOT be manually starting/stop units/individual counters.
        This is a batch mode stop.

        """

        self._freeze()

        for unit_name, unit in self._units.iteritems():
            if 'core' in unit_name:
                self._log.debug("Skipping stopping cores.")
                continue

            # quicker refernece
            PC = unit._pmon_controller

            if PC.first_use == False:
                self._log.debug("Setting enables and status for unit: " + unit_name)
                PC.setAllEnableBit(PC.CNTR_BUSY, False)
                PC.markBusyAsStopped()
                self._log.debug("Setting unit level freeze to TRUE for unit: " + unit_name)
                PC.setAllUnitLvlFreeze(True)

    def _freeze(self):
        """

        Invoke to freeze all counters. It is not advised you call this function directly,
        it just writes to the global control registers, software consistancy is NOT
        maintained.

        """

        # debug info
        self._log.debug("Global freeze being asserted.")

        # freeze the counters
        #self._globalCntrlReg.frzcountr.write(1)
        writeReg(self._globalCntrlReg.frzcountr,1,'globalControl',self._log)

    def _unfreeze(self):
        """

        Invoke to unfreeze all counters. It is not advised you call this function directly,
        it just writes to the global control registers, software consistancy is NOT
        maintained.

        """

        # debug info
        self._log.debug("Global unfreeze being asserted.")

        try:
            #self._globalCntrlReg.unfrzcountr.write(1)
            writeReg(self._globalCntrlReg.unfrzcountr,1,'globalControl',self._log)
        except AttributeError as ae:
            # for HSW
            #self._globalCntrlReg.pmongen.write(1)
            writeReg(self._globalCntrlReg.pmongen,1,'globalControl',self._log)

    def _showStatus(self):
        """

        Prints out the contents of the global status register.

        """

        self._globalStatusReg.showfields()

    def _dumpControlRegisters(self):
        """

        Invoke this function to dump all registers associated with global control.

        """

        # dump the global control register
        self._log.result("Global Control")
        self._log.result("Name: " + self._gcRegName)
        self._log.result("Value: " + hex(self._globalCntrlReg.read()))
        self._globalCntrlReg.showfields()

        print ""

        # dump the global status register
        self._log.result("Status")
        self._log.result("Name: " + self._gsRegName)
        self._log.result("Value: " + hex(self._globalStatusReg.read()))
        self._globalStatusReg.showfields()

    def _getUnits(self, name='', number = -1):
        """

        Usage: getUnits() to return all units or getUnits('unitName') or getUnits('unitName', unitNumber)

        This function is used to search through the available units and return object handles to them.

        If you were in the command line and accessed:

        socket0.pmons.ha.ha0

        This function would be equivalent to returning the object handle for ha0, which you can then access
        events for and so on.

        Return Value: Returns a dictionary of the results. The key is the name of the unit and the value is
        the object handle.

        """

        toReturn = {}
        name = name.lower()

        for unit_name, unit_handle in self._units.iteritems():
            if name in unit_name:
                if number == -1:
                    toReturn[unit_name] = unit_handle
                elif str(number) in unit_name:
                    toReturn[unit_name] = unit_handle

        return toReturn

    def _readPmons(self, callFreeze = False):
        """

        Call this function to go through and retrieve data for all pmons that have been programmed.
        By default this function reads without freezing the pmons before doing a read. To cause
        a freeze/unfreeze process to occur, invoke as:

        readPmons(True)

        Returns a list of CSV's containing information about all programmed/active pmons.

        """

        if callFreeze:
            self._freeze()

        toReturn = []

        units_dict = self._getUnits()

        for unit_name, unit_handle in units_dict.iteritems():
            eventHandlers = unit_handle._pmon_controller.programmed_event_handles
            for reg_num, eventHandle in eventHandlers.iteritems():
                # expired handles are set to None
                if eventHandle != None:
                    toReturn.append(eventHandle.dumpCSV())

        if callFreeze:
            self._unfreeze()

        return toReturn

    def _programPmons(self, * args):
        """

        Call this function to randomize which pmons are programmed. Pass in a list of units
        that you do NOT wish to be programmed automatically.

        Ex) programPmons('imc','ha') will result in all imc and ha units NOT being programmed.

        """

        units_dict = self._getUnits()

        for unit_name, unit_handle in units_dict.iteritems():
            if 'core' in unit_name:
                self._log.debug("Skipping core unit for setting up events.")
                continue

            # check if we need to skip these units
            toContinue = False
            for check in args:
                if check.lower() in unit_name.lower():
                    toContinue = True
                    break

            if toContinue == True:
                continue

            events_list = unit_handle.getEvents()
            random.shuffle(events_list)

            for event_info_dict in events_list:
                if unit_handle.numCountersAvailable() <= 0:
                    break
                try:
                    if event_info_dict['has_sub'] == True:
                        dictHolder = event_info_dict['handle']._linked_to_dict
                        subeventHolder = []
                        # create a local copy so we can randomize
                        for subevent_index, subevent_handle in dictHolder.iteritems():
                            subeventHolder.append(subevent_handle)

                        # randomize the subevents
                        random.shuffle(subeventHolder)

                        # program in the subevent
                        subeventHolder[0].setup()

                    else:
                        # program in the event
                        event_info_dict['handle'].setup()

                except NoAvailableCountersException as e:
                    pass # that counter might just not be available
