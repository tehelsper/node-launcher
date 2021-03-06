import os
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
from typing import Optional, List

import psutil

from node_launcher.exceptions import ZmqPortsNotOpenError
from node_launcher.services.bitcoin_software import BitcoinSoftware
from node_launcher.services.configuration_file import ConfigurationFile
from node_launcher.constants import BITCOIN_DATA_PATH, OPERATING_SYSTEM, \
    IS_WINDOWS, TESTNET_PRUNE, MAINNET_PRUNE
from node_launcher.services.hard_drives import HardDrives
from node_launcher.utilities import get_random_password, get_zmq_port


class Bitcoin(object):
    file: ConfigurationFile
    hard_drives: HardDrives
    process: Optional[psutil.Process]
    software: BitcoinSoftware
    zmq_block_port: int
    zmq_tx_port: int

    def __init__(self, network: str, configuration_file_path: str):
        self.network = network
        self.hard_drives = HardDrives()
        self.process = self.find_running_node()
        self.software = BitcoinSoftware()
        self.file = ConfigurationFile(configuration_file_path)
        self.process = self.find_running_node()
        self.running = False

        if self.file['server'] is None:
            self.file['server'] = True

        if self.file['disablewallet'] is None:
            self.file['disablewallet'] = True

        if self.file['timeout'] is None:
            self.file['timeout'] = 6000

        if self.file['rpcuser'] is None:
            self.file['rpcuser'] = 'default_user'

        if self.file['rpcpassword'] is None:
            self.file['rpcpassword'] = get_random_password()

        if self.file['datadir'] is None:
            self.autoconfigure_datadir()

        if self.file['prune'] is None:
            should_prune = self.hard_drives.should_prune(self.file['datadir'],
                                                         has_bitcoin=True)
            self.set_prune(should_prune)

        if not self.detect_zmq_ports():
            self.zmq_block_port = get_zmq_port()
            self.zmq_tx_port = get_zmq_port()

        self.file['zmqpubrawblock'] = f'tcp://127.0.0.1:{self.zmq_block_port}'
        self.file['zmqpubrawtx'] = f'tcp://127.0.0.1:{self.zmq_tx_port}'

        # noinspection PyBroadException
        try:
            memory = psutil.virtual_memory()
            free_mb = round(memory.available/1000000)
            free_mb -= int(free_mb * .3)
            self.file['dbcache'] = free_mb
        except:
            self.file['dbcache'] = 1000

    def set_prune(self, should_prune: bool = None):

        if should_prune is None:
            should_prune = self.hard_drives.should_prune(self.file['datadir'],
                                                         has_bitcoin=True)
        if should_prune:
            if self.network == 'testnet':
                prune = TESTNET_PRUNE
            else:
                prune = MAINNET_PRUNE
            self.file['prune'] = prune
        else:
            self.file['prune'] = 0
        self.file['txindex'] = not should_prune

    def autoconfigure_datadir(self):
        default_datadir = BITCOIN_DATA_PATH[OPERATING_SYSTEM]
        big_drive = self.hard_drives.get_big_drive()
        default_is_big_enough = not self.hard_drives.should_prune(default_datadir, True)
        default_is_biggest = self.hard_drives.is_default_partition(big_drive)
        if default_is_big_enough or default_is_biggest:
            self.file['datadir'] = default_datadir
            return

        if not self.hard_drives.should_prune(big_drive.mountpoint, False):
            self.file['datadir'] = os.path.join(big_drive.mountpoint, 'Bitcoin')
            if not os.path.exists(self.file['datadir']):
                os.mkdir(self.file['datadir'])
        else:
            self.file['datadir'] = default_datadir

    def find_running_node(self) -> Optional[psutil.Process]:
        if self.network == 'mainnet':
            ports = [8333, 8332]
        else:
            ports = [18333, 18332]
        for process in psutil.process_iter():
            # noinspection PyBroadException
            try:
                process_name = process.name()
            except:
                continue
            if 'bitcoin' in process_name:
                # noinspection PyBroadException
                try:
                    for connection in process.connections():
                        if connection.laddr.port in ports:
                            self.running = True
                            return process
                except:
                    continue
        self.running = False
        return None

    def detect_zmq_ports(self) -> bool:
        if self.process is None:
            return False
        ports = [c.laddr.port for c in self.process.connections()
                 if 18500 <= c.laddr.port <= 18600]
        ports = set(ports)
        if len(ports) != 2:
            raise ZmqPortsNotOpenError(f'''ZMQ ports are not open on 
{self.network} node, please close Bitcoin Core and launch it with the Node Launcher''')
        self.zmq_block_port = min(ports)
        self.zmq_tx_port = max(ports)
        return True

    def bitcoin_qt(self) -> List[str]:
        conf_arg = f'-conf={self.file.path}'
        if IS_WINDOWS:
            conf_arg = f'-conf="{self.file.path}"'

        command = [
            self.software.bitcoin_qt,
            conf_arg,
        ]

        if self.network == 'testnet':
            command += [
                '-testnet'
            ]
        return command

    @property
    def bitcoin_cli(self) -> str:
        command = [
            f'"{self.software.bitcoin_cli}"',
            f'-conf="{self.file.path}"',
        ]
        if self.network == 'testnet':
            command += [
                '-testnet'
            ]
        return ' '.join(command)

    def launch(self):
        command = self.bitcoin_qt()
        if IS_WINDOWS:
            from subprocess import DETACHED_PROCESS, CREATE_NEW_PROCESS_GROUP
            command[0] = '"' + command[0] + '"'
            cmd = ' '.join(command)
            with NamedTemporaryFile(suffix='-btc.bat', delete=False) as f:
                f.write(cmd.encode('utf-8'))
                f.flush()
                result = Popen(
                    ['start', 'powershell', '-noexit', '-windowstyle', 'hidden',
                     '-Command', f.name],
                    stdin=PIPE, stdout=PIPE, stderr=PIPE,
                    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                    close_fds=True, shell=True)
        else:
            result = Popen(command, close_fds=True, shell=False)

        return result
