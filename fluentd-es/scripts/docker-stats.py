import potsdb
import time
import os
from docker import Client
from pyformance.registry import MetricsRegistry
from pyformance import histogram
from pyformance.meters import Gauge
from pyformance.reporters.reporter import Reporter
import traceback

cli = Client(base_url='unix:///var/run/dockerhost/docker.sock', version='auto')

metrics_registry = MetricsRegistry()


class OpentsdbReporter(Reporter):
    def __init__(self,
                 registry,
                 reporting_interval,
                 hostname='localhost',
                 portno=4242,
                 clock=None):
        super(OpentsdbReporter, self).__init__(registry, reporting_interval,
                                               clock)
        self.metrics = potsdb.Client(host=hostname,
                                     port=portno,
                                     qsize=1000,
                                     host_tag=True,
                                     mps=100,
                                     check_host=True)

    def report_now(self, registry=None, timestamp=None):
        try:
            self.save_metrics(registry or self.registry)
        except Exception, err:
            print("Caught exception: " + traceback.format_exc())

    def save_metrics(self, registry):
        metrics_dump = registry.dump_metrics()
        for metric in metrics_dump:
            self.metrics.send(metric, metrics_dump[metric]['value'])


def human_readable(value):
    return float("{0:.3f}".format(value / (1000000)))


def format_percent(value):
    return float("{0:.2f}".format(value))


def getDockerStats():
    cpu_usages = {}
    system_cpu_usages = {}
    reporter = OpentsdbReporter(registry=metrics_registry,
                                reporting_interval=60,
                                hostname=os.environ['OPENTSDB_HOST'],
                                portno=int(os.environ['OPENTSDB_PORT']))
    reporter.start()
    print "Docker metrics reporter started"
    while True:
        try:
            container_list = cli.containers(quiet=True)
            for container_id in container_list:
                inspect_result = cli.inspect_container(container_id)
                labels = inspect_result['Config']['Labels']
                container_name = None
                if 'name' in labels:
                    container_name = labels['name']
                else:
                    continue
                stats_obj = cli.stats(container=container_id, stream=False)
                prev_cpu_usage = cpu_usages[
                    container_name] if container_name in cpu_usages else 0
                prev_system_cpu_usage = system_cpu_usages[
                    container_name] if container_name in system_cpu_usages else 0
                cur_cpu_usage = stats_obj['cpu_stats']['cpu_usage'][
                    'total_usage']
                cur_system_cpu_usage = stats_obj['cpu_stats'][
                    'system_cpu_usage']
                delta_cpu_usage = cur_cpu_usage - prev_cpu_usage
                delta_system_cpu_usage = cur_system_cpu_usage - prev_system_cpu_usage
                if delta_system_cpu_usage > 0 and delta_cpu_usage > 0:
                    cpu_pcnt = delta_cpu_usage * 1.0 / delta_system_cpu_usage * len(
                        stats_obj['cpu_stats']['cpu_usage'][
                            'percpu_usage']) * 100
                else:
                    cpu_pcnt = 0.0
                cpu_usages[container_name] = cur_cpu_usage
                system_cpu_usages[container_name] = cur_system_cpu_usage
                mem_usage = stats_obj['memory_stats']['usage']
                mem_limit = stats_obj['memory_stats']['limit']
                mem_pcnt = mem_usage * 1.0 / mem_limit

                network_input = network_output = None
                if 'networks' in stats_obj:
                    network_input = 0.0
                    network_output = 0.0

                cpu_usage_gauge = metrics_registry.gauge(
                    key=container_name + ".cpu_usage")
                mem_usage_gauge = metrics_registry.gauge(
                    key=container_name + ".mem_usage")
                # Setting metric gauges
                cpu_usage_gauge.set_value(format_percent(cpu_pcnt))
                mem_usage_gauge.set_value(format_percent(mem_pcnt))

                if network_input != None and network_output != None:
                    network_input_gauge = metrics_registry.gauge(
                        key=container_name + ".network_input")
                    network_output_gauge = metrics_registry.gauge(
                        key=container_name + ".network_output")
                    for k, v in stats_obj['networks'].items():
                        network_input += v['rx_bytes']
                        network_output += v['tx_bytes']
                    network_input_gauge.set_value(human_readable(
                        network_input))
                    network_output_gauge.set_value(human_readable(
                        network_output))

            metrics_dump = metrics_registry.dump_metrics()
            # for metric in metrics_dump:
            #     print "{0} = {1}".format(metric, metrics_dump[metric])
            time.sleep(45)
        except Exception, err:
            print("Caught exception: " + traceback.format_exc())


if __name__ == "__main__":
    getDockerStats()

