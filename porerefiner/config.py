import yaml
from pathlib import Path
from os import environ
from logging import log

from .notifiers import REGISTRY, NOTIFIERS

config_file = Path(environ.get('POREREFINER_CONFIG', '/etc/porerefiner/config/config.yml'))


#Logging
log = log.getLogger('config')

try:
    with open(config_file, 'r') as conf:
        config = yaml.load(conf)
    log.info(f"Config file loaded from {config_file}")

except OSError:
    log.warning(f'No config file at {config_file}, creating...')
    from collections import defaultdict
    tree = lambda: defaultdict(tree)
    defaults = tree()
    defaults['db'] = '/etc/porerefiner/database.db'
    defaults['socket'] = '/var/run/porerefiner'
    defaults['nanopore_output_path'] = '///gridion/stuff'
    defaults['notifiers'] = [{'class':'ToastNotifier', 'config':dict(name='Default notifier', max=3)}]
    defaults['minknow_api'] = "https://localhost:9999"
    defaults['log_level'] = logging.INFO
    # defaults['']['']
    with open(config_file, 'w') as conf:
        yaml.dump(defaults, conf)

except yaml.YAMLError as e:
    log.error(f"Couldn't read config file at {config_file}, error was:")
    log.error(e)
    quit(1)


#Socket
config['socket'] = Path(environ.get('POREREFINER_SOCK', config['socket']))
log.info(f"PoreRefiner socket at {config['socket']}")

#Notifiers
log.info("Loading notifiers...")
for notifier_config in config['notifiers']:
    log.info(f"Found notifier {notifier_config['config']['name']}")
    notifier = REGISTRY[notifier_config['class']](**notifier_config['config'])
    NOTIFIERS.append(notifier)


def add_notifier_stub(notifier_cls):
    cp = config.copy() #we don't want the stub to actually take effect until reload
    cp['notifiers'].append(notifier_cls.toStub())
    with open(config_file, 'w') as conf:
        yaml.dump(cp, conf)


