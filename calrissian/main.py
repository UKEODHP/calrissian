from calrissian.executor import CalrissianExecutor
from calrissian.context import CalrissianLoadingContext
from calrissian.version import version
from calrissian.podmonitor import delete_pods
from cwltool.main import main as cwlmain
from cwltool.argparser import arg_parser
from cwltool.context import RuntimeContext
import logging
import sys
import signal


def activate_logging():
    loggers = ['executor','context','tool','job', 'k8s']
    for logger in loggers:
        logging.getLogger('calrissian.{}'.format(logger)).setLevel(logging.DEBUG)
        logging.getLogger('calrissian.{}'.format(logger)).addHandler(logging.StreamHandler())


def add_arguments(parser):
    parser.add_argument('--max-ram', type=int, help='Maximum amount of RAM in MB to use')
    parser.add_argument('--max-cores', type=int, help='Maximum number of CPU cores to use')


def print_version():
    print(version())


def parse_arguments(parser):
    args = parser.parse_args()
    # Check for version arg
    if args.version:
        print_version()
        sys.exit(0)
    if not (args.max_ram and args.max_cores):
        parser.print_help()
        sys.exit(1)
    return args


def handle_sigterm(signum, frame):
    print('Received signal {}, deleting pods'.format(signum))
    delete_pods()
    sys.exit(signum)


def install_signal_handler():
    signal.signal(signal.SIGTERM, handle_sigterm)


def main():
    activate_logging()
    parser = arg_parser()
    add_arguments(parser)
    parsed_args = parse_arguments(parser)
    executor = CalrissianExecutor(parsed_args.max_ram, parsed_args.max_cores)
    runtimeContext = RuntimeContext(vars(parsed_args))
    runtimeContext.select_resources = executor.select_resources
    install_signal_handler()
    try:
        result = cwlmain(args=parsed_args,
                         executor=executor,
                         loadingContext=CalrissianLoadingContext(),
                         runtimeContext=runtimeContext,
                         versionfunc=version,
                         )
    finally:
        delete_pods()

    return result


if __name__ == '__main__':
    sys.exit(main())
