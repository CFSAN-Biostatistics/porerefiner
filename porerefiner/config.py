import yaml
from pathlib import Path
from os import environ
from logging import log

from .notifiers import REGISTRY, NOTIFIERS

config_file = Path(environ.get('POREREFINER_CONFIG', '/etc/porerefiner/config/config.yml'))

try:
    config = yaml.load(config_file)

except OSError:
    log.warning(f'No config file at {config_file}, creating...')
    from collections import defaultdict
    tree = lambda: defaultdict(tree)
    defaults = tree()
    defaults['db'] = '/etc/porerefiner/database.db'
    defaults['socket'] = '/var/run/porerefiner'
    defaults['notifiers'] = [{'class':'ToastNotifier', 'config':dict(name='Default notifier', max=3)}]
    defaults['minknow_api'] = "https://localhost:9999"
    # defaults['']['']

    yaml.dump(defaults, config_file)

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


