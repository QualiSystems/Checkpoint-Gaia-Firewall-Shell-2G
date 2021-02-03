#!/usr/bin/python
# -*- coding: utf-8 -*-

from cloudshell.shell.core.driver_context import ResourceCommandContext, AutoLoadDetails
from cloudshell.shell.core.driver_utils import GlobalLock

from cloudshell.checkpoint.gaia.cli.checkpoint_cli_configurator import CheckpointCliConfigurator
from cloudshell.checkpoint.gaia.flows.checkpoint_autoload_flow import CheckpointSnmpAutoloadFlow
from cloudshell.checkpoint.gaia.flows.checkpoint_configuration_flow import CheckpointConfigurationFlow
from cloudshell.checkpoint.gaia.flows.checkpoint_enable_disable_snmp_flow import CheckpointEnableDisableSnmpFlow
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext

from cloudshell.checkpoint.gaia.flows.checkpoint_load_firmware_flow import CheckpointLoadFirmwareFlow
from cloudshell.checkpoint.gaia.flows.checkpoint_state_flow import CheckpointStateFlow
from cloudshell.cli.service.cli import CLI
from cloudshell.cli.service.session_pool_manager import SessionPoolManager
from cloudshell.shell.flows.command.basic_flow import RunCommandFlow
from cloudshell.shell.standards.firewall.autoload_model import FirewallResourceModel
from cloudshell.shell.standards.firewall.driver_interface import FirewallResourceDriverInterface
from cloudshell.shell.standards.firewall.resource_config import FirewallResourceConfig
from cloudshell.snmp.snmp_configurator import EnableDisableSnmpConfigurator


class CheckPointGaiaFirewallShell2GDriver(ResourceDriverInterface, FirewallResourceDriverInterface):
    SUPPORTED_OS = ["Gaia", "checkpoint", ".2620."]
    SHELL_NAME = "Checkpoint Gaia Firewall Shell 2G"

    def __init__(self):
        super(CheckPointGaiaFirewallShell2GDriver, self).__init__()
        self._cli = None

    def initialize(self, context):
        """Initialize the driver session

        :param context: the context the command runs on
        :rtype: str
        """
        resource_config = FirewallResourceConfig.from_context(self.SHELL_NAME, context)
        session_pool_size = int(resource_config.sessions_concurrency_limit)
        self._cli = CLI(SessionPoolManager(max_pool_size=session_pool_size, pool_timeout=100))
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
        with LoggingSessionContext(context) as logger:
            api = CloudShellSessionContext(context).get_api()

            resource_config = FirewallResourceConfig.from_context(self.SHELL_NAME, context, api, self.SUPPORTED_OS)

            cli_configurator = CheckpointCliConfigurator(self._cli, resource_config, logger)

            configuration_flow = CheckpointConfigurationFlow(logger, resource_config, cli_configurator)
            configuration_type = configuration_type or "running"
            restore_method = restore_method or "override"
            return configuration_flow.restore(path, configuration_type, restore_method)

    def save(self, context, folder_path, configuration_type, vrf_management_name):
        """Save a configuration file to the provided destination

        :param ResourceCommandContext context: The context object for the command with resource and
            reservation info
        :param str folder_path: The path to the folder in which the configuration file will be saved
        :param str configuration_type: startup or running config
        :param vrf_management_name:
        :return The configuration file name
        :rtype: str
        """

        with LoggingSessionContext(context) as logger:
            api = CloudShellSessionContext(context).get_api()

            resource_config = FirewallResourceConfig.from_context(self.SHELL_NAME, context, api, self.SUPPORTED_OS)

            cli_configurator = CheckpointCliConfigurator(self._cli, resource_config, logger)

            configuration_flow = CheckpointConfigurationFlow(logger, resource_config, cli_configurator)
            configuration_type = configuration_type or "running"
            return configuration_flow.save(folder_path, configuration_type, vrf_management_name)

    @GlobalLock.lock
    def load_firmware(self, context, path):
        """Upload and updates firmware on the resource

        :param ResourceCommandContext context: The context object for the command with resource and
            reservation info
        :param str path: path to tftp server where firmware file is stored
        """

        with LoggingSessionContext(context) as logger:
            state_flow = CheckpointLoadFirmwareFlow(logger)
            return state_flow.load_firmware(path)

    def run_custom_command(self, context, custom_command):
        """Executes a custom command on the device

        :param ResourceCommandContext context: The context object for the command with resource and
            reservation info
        :param str custom_command: The command to run
        :return: the command result text
        :rtype: str
        """
        with LoggingSessionContext(context) as logger:
            api = CloudShellSessionContext(context).get_api()

            resource_config = FirewallResourceConfig.from_context(self.SHELL_NAME, context, api, self.SUPPORTED_OS)

            cli_configurator = CheckpointCliConfigurator(self._cli, resource_config, logger)

            run_command_flow = RunCommandFlow(logger, cli_configurator)
            return run_command_flow.run_custom_command(custom_command)

    def run_custom_config_command(self, context, custom_command):
        """Executes a custom command on the device in configuration mode

        :param ResourceCommandContext context: The context object for the command with resource and
            reservation info
        :param str custom_command: The command to run
        :return: the command result text
        :rtype: str
        """

        with LoggingSessionContext(context) as logger:
            api = CloudShellSessionContext(context).get_api()

            resource_config = FirewallResourceConfig.from_context(self.SHELL_NAME, context, api, self.SUPPORTED_OS)

            cli_configurator = CheckpointCliConfigurator(self._cli, resource_config, logger)

            run_command_flow = RunCommandFlow(logger, cli_configurator)
            return run_command_flow.run_custom_config_command(custom_command)

    def shutdown(self, context):
        """Sends a graceful shutdown to the device

        :param ResourceCommandContext context: The context object for the command with resource and
            reservation info
        """
        with LoggingSessionContext(context) as logger:
            api = CloudShellSessionContext(context).get_api()

            resource_config = FirewallResourceConfig.from_context(self.SHELL_NAME, context, api, self.SUPPORTED_OS)

            cli_configurator = CheckpointCliConfigurator(self._cli, resource_config, logger)

            state_flow = CheckpointStateFlow(logger, resource_config, cli_configurator, api)
            return state_flow.shutdown()

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

        with LoggingSessionContext(context) as logger:
            api = CloudShellSessionContext(context).get_api()

            resource_config = FirewallResourceConfig.from_context(self.SHELL_NAME, context, api, self.SUPPORTED_OS)

            cli_configurator = CheckpointCliConfigurator(self._cli, resource_config, logger)

            configuration_flow = CheckpointConfigurationFlow(logger, resource_config, cli_configurator)
            return configuration_flow.orchestration_save(mode, custom_params)

    def orchestration_restore(self, context, saved_artifact_info, custom_params):
        """Restores a saved artifact previously saved by this Shell driver using the
            orchestration_save function
        :param ResourceCommandContext context: The context object for the command with resource and
            reservation info
        :param str saved_artifact_info: A JSON string representing the state to restore including
            saved artifacts and info
        :param str custom_params: Set of custom parameters for the restore operation
        """

        with LoggingSessionContext(context) as logger:
            api = CloudShellSessionContext(context).get_api()

            resource_config = FirewallResourceConfig.from_context(self.SHELL_NAME, context, api, self.SUPPORTED_OS)

            cli_configurator = CheckpointCliConfigurator(self._cli, resource_config, logger)

            configuration_flow = CheckpointConfigurationFlow(logger, resource_config, cli_configurator)
            return configuration_flow.orchestration_restore(saved_artifact_info, custom_params)

    @GlobalLock.lock
    def get_inventory(self, context):
        """Discovers the resource structure and attributes.

        :param ResourceCommandContext context: ResourceCommandContext object with all Resource Attributes inside
        :return Attribute and sub-resource information for the Shell resource
        :rtype: AutoLoadDetails
        """
        with LoggingSessionContext(context) as logger:
            api = CloudShellSessionContext(context).get_api()

            resource_config = FirewallResourceConfig.from_context(self.SHELL_NAME, context, api, self.SUPPORTED_OS)

            cli_configurator = CheckpointCliConfigurator(self._cli, resource_config, logger)
            enable_disable_snmp_flow = CheckpointEnableDisableSnmpFlow(cli_configurator, logger)
            snmp_configurator = EnableDisableSnmpConfigurator(enable_disable_snmp_flow, resource_config, logger)

            resource_model = FirewallResourceModel.from_resource_config(resource_config)

            autoload_operations = CheckpointSnmpAutoloadFlow(logger, snmp_configurator)
            logger.info('Autoload started')
            response = autoload_operations.discover(self.SUPPORTED_OS, resource_model)
            logger.info('Autoload completed')
            return response

    def health_check(self, context):
        """Checks if the device is up and connectable

        :param ResourceCommandContext context: ResourceCommandContext object with all Resource
            Attributes inside
        :return: Success or fail message
        :rtype: str
        """
        with LoggingSessionContext(context) as logger:
            api = CloudShellSessionContext(context).get_api()

            resource_config = FirewallResourceConfig.from_context(self.SHELL_NAME, context, api, self.SUPPORTED_OS)

            cli_configurator = CheckpointCliConfigurator(self._cli, resource_config, logger)

            state_flow = CheckpointStateFlow(logger, resource_config, cli_configurator, api)
            return state_flow.health_check()

    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files
        """
        pass
