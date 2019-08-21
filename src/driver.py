#!/usr/bin/python
# -*- coding: utf-8 -*-

from cloudshell.devices.driver_helper import get_logger_with_thread_id, get_api, get_cli, \
    parse_custom_commands
from cloudshell.devices.runners.run_command_runner import RunCommandRunner
from cloudshell.devices.runners.state_runner import StateRunner
from cloudshell.devices.standards.firewall.configuration_attributes_structure import \
    create_firewall_resource_from_context as create_resource_from_context
from cloudshell.firewall.firewall_resource_driver_interface import FirewallResourceDriverInterface
from cloudshell.shell.core.driver_context import ResourceCommandContext, \
    AutoLoadCommandContext, AutoLoadDetails
from cloudshell.shell.core.driver_utils import GlobalLock
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface

from cloudshell.checkpoint.gaia.cli.checkpoint_cli_handler import CheckpointCliHandler as CliHandler
from cloudshell.checkpoint.gaia.runners.checkpoint_autoload_runner import CheckpointAutoloadRunner as AutoloadRunner
from cloudshell.checkpoint.gaia.runners.checkpoint_configuration_runner import CheckpointConfigurationRunner as \
    ConfigurationRunner
from cloudshell.checkpoint.gaia.runners.checkpoint_firmware_runner import CheckpointFirmwareRunner as FirmwareRunner
from cloudshell.checkpoint.gaia.snmp.checkpoint_snmp_handler import CheckpointSnmpHandler as SnmpHandler


class CheckPointGaiaFirewallShell2GDriver(ResourceDriverInterface, FirewallResourceDriverInterface,
                                          GlobalLock):
    SUPPORTED_OS = ["Gaia", "checkpoint"]
    SHELL_NAME = "Checkpoint Gaia Firewall Shell 2G"

    def __init__(self):
        super(CheckPointGaiaFirewallShell2GDriver, self).__init__()
        self._cli = None

    def initialize(self, context):
        """Initialize the driver session

        :param context: the context the command runs on
        :rtype: str
        """

        resource_config = create_resource_from_context(self.SHELL_NAME, self.SUPPORTED_OS, context)

        session_pool_size = int(resource_config.sessions_concurrency_limit)
        self._cli = get_cli(session_pool_size)
        return "Finished initializing"

    @GlobalLock.lock
    def restore(self, context, path, configuration_type, restore_method):
        """Restores a configuration file

        :param ResourceCommandContext context: The context object for the command with resource and
            reservation info
        :param str path: The path to the configuration file, including the configuration file name
        :param str restore_method: Determines whether the restore should append or override the
            current configuration
        :param str configuration_type: Specify whether the file should update the startup or
            running config
        """

        logger = get_logger_with_thread_id(context)
        api = get_api(context)

        resource_config = create_resource_from_context(self.SHELL_NAME, self.SUPPORTED_OS, context)
        cli_handler = CliHandler(self._cli, resource_config, logger, api)

        configuration_type = configuration_type or "running"
        restore_method = restore_method or "override"

        configuration_operations = ConfigurationRunner(logger, resource_config, api, cli_handler)
        logger.info("Restore started")
        configuration_operations.restore(path, configuration_type, restore_method)
        logger.info("Restore completed")

    def save(self, context, folder_path, configuration_type):
        """Save a configuration file to the provided destination

        :param ResourceCommandContext context: The context object for the command with resource and
            reservation info
        :param str folder_path: The path to the folder in which the configuration file will be saved
        :param str configuration_type: startup or running config
        :return The configuration file name
        :rtype: str
        """

        logger = get_logger_with_thread_id(context)
        api = get_api(context)

        resource_config = create_resource_from_context(self.SHELL_NAME, self.SUPPORTED_OS, context)
        cli_handler = CliHandler(self._cli, resource_config, logger, api)

        configuration_type = configuration_type or "running"

        configuration_operations = ConfigurationRunner(logger, resource_config, api, cli_handler)
        logger.info("Save started")
        response = configuration_operations.save(folder_path, configuration_type)
        logger.info("Save completed")
        return response

    @GlobalLock.lock
    def load_firmware(self, context, path):
        """Upload and updates firmware on the resource

        :param ResourceCommandContext context: The context object for the command with resource and
            reservation info
        :param str path: path to tftp server where firmware file is stored
        """

        logger = get_logger_with_thread_id(context)
        api = get_api(context)

        resource_config = create_resource_from_context(self.SHELL_NAME, self.SUPPORTED_OS, context)
        cli_handler = CliHandler(self._cli, resource_config, logger, api)

        logger.info("Start Load Firmware")
        firmware_operations = FirmwareRunner(logger, cli_handler)
        response = firmware_operations.load_firmware(path)
        logger.info("Finish Load Firmware: {}".format(response))

    def run_custom_command(self, context, custom_command):
        """Executes a custom command on the device

        :param ResourceCommandContext context: The context object for the command with resource and
            reservation info
        :param str custom_command: The command to run
        :return: the command result text
        :rtype: str
        """

        logger = get_logger_with_thread_id(context)
        api = get_api(context)

        resource_config = create_resource_from_context(self.SHELL_NAME, self.SUPPORTED_OS, context)
        cli_handler = CliHandler(self._cli, resource_config, logger, api)

        command_operations = RunCommandRunner(logger, cli_handler)
        return command_operations.run_custom_command(parse_custom_commands(custom_command))

    def run_custom_config_command(self, context, custom_command):
        """Executes a custom command on the device in configuration mode

        :param ResourceCommandContext context: The context object for the command with resource and
            reservation info
        :param str custom_command: The command to run
        :return: the command result text
        :rtype: str
        """

        logger = get_logger_with_thread_id(context)
        api = get_api(context)

        resource_config = create_resource_from_context(self.SHELL_NAME, self.SUPPORTED_OS, context)
        cli_handler = CliHandler(self._cli, resource_config, logger, api)

        command_operations = RunCommandRunner(logger, cli_handler)
        return command_operations.run_custom_config_command(parse_custom_commands(custom_command))

    def shutdown(self, context):
        """Sends a graceful shutdown to the device

        :param ResourceCommandContext context: The context object for the command with resource and
            reservation info
        """

        logger = get_logger_with_thread_id(context)
        api = get_api(context)

        resource_config = create_resource_from_context(self.SHELL_NAME, self.SUPPORTED_OS, context)
        cli_handler = CliHandler(self._cli, resource_config, logger, api)

        state_operations = StateRunner(logger, api, resource_config, cli_handler)
        return state_operations.shutdown()

    def orchestration_save(self, context, mode, custom_params):
        """Saves the Shell state and returns a description of the saved artifacts and information
        This command is intended for API use only by sandbox orchestration scripts to implement
        a save and restore workflow

        :param ResourceCommandContext context: the context object containing resource and
            reservation info
        :param str mode: Snapshot save mode, can be one of two values "shallow" (default) or "deep"
        :param str custom_params: Set of custom parameters for the save operation
        :return: SavedResults serialized as JSON
        :rtype: OrchestrationSaveResult
        """

        logger = get_logger_with_thread_id(context)
        api = get_api(context)

        resource_config = create_resource_from_context(self.SHELL_NAME, self.SUPPORTED_OS, context)
        cli_handler = CliHandler(self._cli, resource_config, logger, api)

        configuration_operations = ConfigurationRunner(logger, resource_config, api, cli_handler)
        logger.info("Orchestration save started")
        response = configuration_operations.orchestration_save(mode, custom_params)
        logger.info("Orchestration save completed")
        return response

    def orchestration_restore(self, context, saved_artifact_info, custom_params):
        """Restores a saved artifact previously saved by this Shell driver using the
            orchestration_save function
        :param ResourceCommandContext context: The context object for the command with resource and
            reservation info
        :param str saved_artifact_info: A JSON string representing the state to restore including
            saved artifacts and info
        :param str custom_params: Set of custom parameters for the restore operation
        """

        logger = get_logger_with_thread_id(context)
        api = get_api(context)

        resource_config = create_resource_from_context(self.SHELL_NAME, self.SUPPORTED_OS, context)
        cli_handler = CliHandler(self._cli, resource_config, logger, api)

        configuration_operations = ConfigurationRunner(logger, resource_config, api, cli_handler)
        logger.info("Orchestration restore started")
        configuration_operations.orchestration_restore(saved_artifact_info, custom_params)
        logger.info("Orchestration restore completed")

    @GlobalLock.lock
    def get_inventory(self, context):
        """Discovers the resource structure and attributes.

        :param AutoLoadCommandContext context: the context the command runs on
        :return Attribute and sub-resource information for the Shell resource
        :rtype: AutoLoadDetails
        """

        logger = get_logger_with_thread_id(context)
        api = get_api(context)

        resource_config = create_resource_from_context(self.SHELL_NAME, self.SUPPORTED_OS, context)
        cli_handler = CliHandler(cli=self._cli, resource_config=resource_config, logger=logger, api=api)
        snmp_handler = SnmpHandler(resource_config=resource_config, logger=logger, api=api, cli=cli_handler)

        autoload_operations = AutoloadRunner(resource_config=resource_config, logger=logger, snmp_handler=snmp_handler)
        logger.info("Autoload started")
        response = autoload_operations.discover()
        logger.info("Autoload completed")
        return response

    def health_check(self, context):
        """Checks if the device is up and connectable

        :param ResourceCommandContext context: ResourceCommandContext object with all Resource
            Attributes inside
        :return: Success or fail message
        :rtype: str
        """

        logger = get_logger_with_thread_id(context)
        api = get_api(context)

        resource_config = create_resource_from_context(self.SHELL_NAME, self.SUPPORTED_OS, context)
        cli_handler = CliHandler(self._cli, resource_config, logger, api)

        state_operations = StateRunner(logger, api, resource_config, cli_handler)
        return state_operations.health_check()

    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files
        """
        pass
