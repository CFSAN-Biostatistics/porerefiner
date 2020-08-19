import yaml
from collections import defaultdict
from pathlib import Path
from os import environ, makedirs
import logging

#from porerefiner.notifiers import REGISTRY, NOTIFIERS
import porerefiner.notifiers as notifiers
import porerefiner.jobs as jobs
import porerefiner.jobs.submitters as submitters

# config_file = Path(environ.get('POREREFINER_CONFIG', '/Users/justin.payne/.porerefiner/config.yml'))

def c(d):
    "Recursively convert this defaultdict to a dict"
    if isinstance(d, defaultdict):
        return {k:c(v) for k,v in d.items()}
    elif isinstance(d, Path):
        return str(d)
    else:
        return d


class Config:

    the_config = None

    # config_file = Path(environ.get('POREREFINER_CONFIG', '/Users/justin.payne/.porerefiner/config.yml'))

    @classmethod
    def __call__(cls, *args, **kwargs):
        if not cls.the_config:
            cls.the_config = super().__call__(cls, *args, **kwargs)
        return cls.the_config

    def __init__(self, config_file, client_only=False):

        self.config_file = config_file = Path(config_file)

        #Logging
        log = logging.getLogger('porerefiner.config')

        try:
            with open(config_file, 'r') as conf:
                self.config = yaml.safe_load(conf)
            log.info(f"Config file loaded from {config_file}")

        except OSError:
            log.warning(f'No config file at {config_file}, creating...')


            self.config = Config.new_config_file(config_file, client_only)

        except yaml.YAMLError as e:
            log.error(f"Couldn't read config file at {config_file}, error was:")
            log.error(e)
            quit(1)


        #Socket
        self.config['server']['socket'] = Path(environ.get('POREREFINER_SOCK', self.config['server']['socket']))
        log.info(f"PoreRefiner socket at {self.config['server']['socket']}")

        #Notifiers
        log.info("Loading notifiers...")
        for notifier_config in self.config.get('notifiers', []):
            log.info(f"Found notifier {notifier_config['config']['name']}")
            notifiers.REGISTRY[notifier_config['class']](**notifier_config['config'])
            #NOTIFIERS.append(notifier)

        #Submitters
        submitters.SUBMITTER = None
        log.info("Loading job submitters...")
        for submitter_config in self.config.get('submitters', []):
            log.info(f"Found submitter {submitter_config['class']}")
            submitter = submitters.REGISTRY[submitter_config['class']](**submitter_config['config'])
            #jobs
            log.info("Loading jobs...")
            for job_config in submitter_config.get('jobs', []):
                clss = jobs.CLASS_REGISTRY[job_config['class']]
                log.info(f"Found job {clss.__name__}")
                job = clss(submitter=submitter, **job_config['config'])

    @staticmethod
    def new_config_file(config_file, client_only=False, nanopore_path='/data', database_path=False, socket_path=False):

        porerefiner_dir = Path(config_file).parent


        tree = lambda: defaultdict(tree) #this is a trick for defining a recursive defaultdict
        defaults = tree()

        defaults['server']['socket'] = socket_path or porerefiner_dir / 'socket' # '/Users/justin.payne/.porerefiner/socket'
        defaults['server']['use_ssl'] = False

        if not client_only:
            defaults['porerefiner']['log_level'] = logging.INFO
            defaults['porerefiner']['run_polling_interval'] = 600
            defaults['porerefiner']['job_polling_interval'] = 1800
            defaults['database']['path'] = database_path or porerefiner_dir / 'database.db' # '/Users/justin.payne/.porerefiner/database.db'
            defaults['database']['pragmas']['foreign_keys'] = 1
            defaults['database']['pragmas']['journal_mode'] = 'wal'
            defaults['database']['pragmas']['cache_size'] = 1000
            defaults['database']['pragmas']['ignore_check_constraints'] = 0
            defaults['database']['pragmas']['synchronous'] = 0
            defaults['nanopore']['path'] = nanopore_path
            defaults['nanopore']['api'] = "localhost:9501"

            try:
                from pynotifier import Notification
                defaults['notifiers'] = [{'class':'ToastNotifier', 'config':dict(name='Default notifier', max=3)}]
            except ImportError: # pynotifier not installed, so no need to create a Toast notifier
                pass

# {'class':'HpcSubmitter', 'config':dict(login_host="login1-raven2.fda.gov",
#                                                                             username="nanopore",
#                                                                             private_key_path=".ssh/id_rsa",
#                                                                             known_hosts_path=".ssh/known_hosts",
#                                                                             scheduler="uge",
#                                                                             queue="service.q"),
#                                         'jobs':[{'class':'GuppyJob', 'config':dict(num_cores=16)}]
#                                         },
#                                     {'class':'Epi2meSubmitter', 'config':dict(api_key=''),
#                                     'jobs':[{'class':'EpiJob', 'config':dict()}]
#                                     }

            defaults['submitters'] = []




        defaults = c(defaults)

        makedirs(config_file.parent, exist_ok=True)

        # defaults['']['']
        with open(config_file, 'w') as conf:
            yaml.dump(defaults, conf)

        return defaults

#Jobs
# log.info("Loading jobs...")
# for job_config in config.get('jobs', []):
#     log.info(f"Found job {job_config['class']}")
#     jobs.REGISTRY[job_config['class']](**job_config['config'])

# def add_notifier_stub(notifier_cls):
#     cp = config.copy() #we don't want the stub to actually take effect until reload
#     cp['notifiers'].append(notifier_cls.toStub())
#     with open(config_file, 'w') as conf:
#         yaml.dump(cp, conf)


