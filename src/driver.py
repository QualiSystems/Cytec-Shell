from cloudshell.shell.core.context_utils import get_resource_address, get_attribute_by_name
from cloudshell.shell.core.session.logging_session import LoggingSessionContext
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface

from cytec.tcp_communicator import TcpCommunicator


class CytecShellDriver(ResourceDriverInterface):
    LATENCY_TABLE = {100: 0,
                     200: 1,
                     400: 2,
                     800: 3,
                     1600: 4,
                     3200: 5,
                     6400: 6,
                     12800: 7}

    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        self._communicator = None
        self._latency = 0

    def _obtain_communicator(self, context, logger=None):
        if not logger:
            logger = LoggingSessionContext.get_logger_for_context(context)
        address = get_resource_address(context)
        port = get_attribute_by_name('CLI TCP Port', context)

        if not self._communicator:
            self._communicator = TcpCommunicator(address, port, logger)
        else:
            if self._communicator.address != address or self._communicator.port != port:
                self._communicator.close()
                self._communicator = TcpCommunicator(address, port, logger)
            else:
                self._communicator.logger = logger
        return self._communicator

    def _calculate_ports_for_the_latency(self, latency):
        latency = int(latency)
        result = []
        for lat in sorted(self.LATENCY_TABLE)[::-1]:
            if latency >= lat:
                result.append(self.LATENCY_TABLE[lat])
                latency -= lat
        return result

    def _clear_loops(self, communicator):
        output = communicator.send_command('C')
        if int(output) != 0:
            raise Exception(self.__class__.__name__, 'Cannot clear loops, incorrect output')

    def _set_latency(self, communicator, latency):
        self._clear_loops(communicator)
        for port in self._calculate_ports_for_the_latency(latency):
            command = 'L 0 ' + str(port)
            output = communicator.send_command(command)
            if int(output) != 1:
                raise Exception(self.__class__.__name__, 'Cannot latch port {}, incorrect output'.format(port))
        self._latency = latency

    def initialize(self, context):
        """
        Initialize the driver session, this function is called everytime a new instance of the driver is created
        This is a good place to load and cache the driver configuration, initiate sessions etc.
        :param InitCommandContext context: the context the command runs on
        """
        pass

    def create_loop(self, context, latency):
        """
        Create new loop
        :param context:
        :param latency:
        :return:
        """
        latency = int(latency)
        logger = LoggingSessionContext.get_logger_for_context(context)
        logger.debug('Creating loop for the latency {}'.format(latency))
        communicator = self._obtain_communicator(context, logger)
        self._set_latency(communicator, latency)

    def extend_loop(self, context):
        """
        Extend latency, + 100ft
        :param context:
        :return:
        """
        logger = LoggingSessionContext.get_logger_for_context(context)
        latency = self._latency + 100
        logger.debug('Extending loop to {}'.format(self._latency))
        communicator = self._obtain_communicator(context, logger)
        self._set_latency(communicator, latency)

    def clear_loops(self, context):
        """
        Clear all loops
        :param context:
        :return:
        """
        logger = LoggingSessionContext.get_logger_for_context(context)
        communicator = self._obtain_communicator(context, logger)
        self._clear_loops(communicator)
        self._latency = 0

    # <editor-fold desc="Orchestration Save and Restore Standard">
    def orchestration_save(self, context, cancellation_context, mode, custom_params=None):
        """
        Saves the Shell state and returns a description of the saved artifacts and information
        This command is intended for API use only by sandbox orchestration scripts to implement
        a save and restore workflow
        :param ResourceCommandContext context: the context object containing resource and reservation info
        :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
        :param str mode: Snapshot save mode, can be one of two values 'shallow' (default) or 'deep'
        :param str custom_params: Set of custom parameters for the save operation
        :return: SavedResults serialized as JSON
        :rtype: OrchestrationSaveResult
        """

        # See below an example implementation, here we use jsonpickle for serialization,
        # to use this sample, you'll need to add jsonpickle to your requirements.txt file
        # The JSON schema is defined at: https://github.com/QualiSystems/sandbox_orchestration_standard/blob/master/save%20%26%20restore/saved_artifact_info.schema.json
        # You can find more information and examples examples in the spec document at https://github.com/QualiSystems/sandbox_orchestration_standard/blob/master/save%20%26%20restore/save%20%26%20restore%20standard.md
        '''
        # By convention, all dates should be UTC
        created_date = datetime.datetime.utcnow()

        # This can be any unique identifier which can later be used to retrieve the artifact
        # such as filepath etc.

        # By convention, all dates should be UTC
        created_date = datetime.datetime.utcnow()

        # This can be any unique identifier which can later be used to retrieve the artifact
        # such as filepath etc.
        identifier = created_date.strftime('%y_%m_%d %H_%M_%S_%f')

        orchestration_saved_artifact = OrchestrationSavedArtifact('REPLACE_WITH_ARTIFACT_TYPE', identifier)

        saved_artifacts_info = OrchestrationSavedArtifactInfo(
            resource_name="some_resource",
            created_date=created_date,
            restore_rules=OrchestrationRestoreRules(requires_same_resource=True),
            saved_artifact=orchestration_saved_artifact)

        return OrchestrationSaveResult(saved_artifacts_info)
        '''
        pass

    def orchestration_restore(self, context, cancellation_context, saved_details):
        """
        Restores a saved artifact previously saved by this Shell driver using the orchestration_save function
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
        :param str saved_details: A JSON string representing the state to restore including saved artifacts and info
        :return: None
        """
        '''
        # The saved_details JSON will be defined according to the JSON Schema and is the same object returned via the
        # orchestration save function.
        # Example input:
        # {
        #     "saved_artifact": {
        #      "artifact_type": "REPLACE_WITH_ARTIFACT_TYPE",
        #      "identifier": "16_08_09 11_21_35_657000"
        #     },
        #     "resource_name": "some_resource",
        #     "restore_rules": {
        #      "requires_same_resource": true
        #     },
        #     "created_date": "2016-08-09T11:21:35.657000"
        #    }

        # The example code below just parses and prints the saved artifact identifier
        saved_details_object = json.loads(saved_details)
        return saved_details_object[u'saved_artifact'][u'identifier']
        '''
        pass

    # </editor-fold>

    # <editor-fold desc="Discovery">

    def get_inventory(self, context):
        """
        Discovers the resource structure and attributes.
        :param AutoLoadCommandContext context: the context the command runs on
        :return Attribute and sub-resource information for the Shell resource you can return an AutoLoadDetails object
        :rtype: AutoLoadDetails
        """
        # See below some example code demonstrating how to return the resource structure
        # and attributes. In real life, of course, if the actual values are not static,
        # this code would be preceded by some SNMP/other calls to get the actual resource information
        '''
           # Add sub resources details
           sub_resources = [ AutoLoadResource(model ='Generic Chassis',name= 'Chassis 1', relative_address='1'),
           AutoLoadResource(model='Generic Module',name= 'Module 1',relative_address= '1/1'),
           AutoLoadResource(model='Generic Port',name= 'Port 1', relative_address='1/1/1'),
           AutoLoadResource(model='Generic Port', name='Port 2', relative_address='1/1/2'),
           AutoLoadResource(model='Generic Power Port', name='Power Port', relative_address='1/PP1')]


           attributes = [ AutoLoadAttribute(relative_address='', attribute_name='Location', attribute_value='Santa Clara Lab'),
                          AutoLoadAttribute('', 'Model', 'Catalyst 3850'),
                          AutoLoadAttribute('', 'Vendor', 'Cisco'),
                          AutoLoadAttribute('1', 'Serial Number', 'JAE053002JD'),
                          AutoLoadAttribute('1', 'Model', 'WS-X4232-GB-RJ'),
                          AutoLoadAttribute('1/1', 'Model', 'WS-X4233-GB-EJ'),
                          AutoLoadAttribute('1/1', 'Serial Number', 'RVE056702UD'),
                          AutoLoadAttribute('1/1/1', 'MAC Address', 'fe80::e10c:f055:f7f1:bb7t16'),
                          AutoLoadAttribute('1/1/1', 'IPv4 Address', '192.168.10.7'),
                          AutoLoadAttribute('1/1/2', 'MAC Address', 'te67::e40c:g755:f55y:gh7w36'),
                          AutoLoadAttribute('1/1/2', 'IPv4 Address', '192.168.10.9'),
                          AutoLoadAttribute('1/PP1', 'Model', 'WS-X4232-GB-RJ'),
                          AutoLoadAttribute('1/PP1', 'Port Description', 'Power'),
                          AutoLoadAttribute('1/PP1', 'Serial Number', 'RVE056702UD')]

           return AutoLoadDetails(sub_resources,attributes)
        '''
        pass

    # </editor-fold>

    # <editor-fold desc="Health Check">

    def health_check(self, cancellation_context):
        """
        Checks if the device is up and connectable
        :return: None
        :exception Exception: Raises an error if cannot connect
        """
        pass

    # </editor-fold>

    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files
        """
        pass
