import slo_generator.cli
import sys
import time
import schedule
from prometheus_client import start_http_server


def calculate_slo(args):
    slo_generator.cli.cli(args)


if __name__ == '__main__':
    args = slo_generator.cli.parse_args(sys.argv[1:])
    start_http_server(9090)
    schedule.every(10).seconds.do(calculate_slo, args)
    while True:
        schedule.run_pending()
        time.sleep(1)
