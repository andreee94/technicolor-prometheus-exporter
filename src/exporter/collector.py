from prometheus_client.core import *
from gateway import TechnicolorGateway

class TechnicolorCollector(object):

    def __init__(self, gateway: TechnicolorGateway):
        self.gateway = gateway
        self.gateway.srp6authenticate()

    def init_metrics(self):
        self.technicolor_broadband_max_line_rate = GaugeMetricFamily('technicolor_broadband_max_line_rate', 'Nominal Bandwidth', labels=['direction'], unit='bps')
        self.technicolor_broadband_line_rate = GaugeMetricFamily('technicolor_broadband_line_rate', 'Nominal Bandwidth', labels=['direction'], unit='bps')
        self.technicolor_broadband_data = GaugeMetricFamily('technicolor_broadband_data', 'Total Transmitted Data', labels=['direction'], unit='bytes')
        self.technicolor_uptime = CounterMetricFamily('technicolor_uptime', 'Uptime', unit='seconds')

        self.technicolor_rx_packets = CounterMetricFamily('technicolor_rx_packets', 'Received Packets', labels=['interface', 'device', 'type'], unit='pkts')
        self.technicolor_tx_packets = CounterMetricFamily('technicolor_tx_packets', 'Transmitted Packets', labels=['interface', 'device', 'type'], unit='pkts')

        self.technicolor_rx_bytes = CounterMetricFamily('technicolor_rx_bytes', 'Received Bytes', labels=['interface', 'device', 'type'], unit='bytes')
        self.technicolor_tx_bytes = CounterMetricFamily('technicolor_tx_bytes', 'Transmitted Bytes', labels=['interface', 'device', 'type'], unit='bytes')

        self.technicolor_ports_speed = GaugeMetricFamily('technicolor_ports_speed', 'Port Speed', labels=['interface', 'device', 'type'], unit='mbps')

        self.technicolor_devices = InfoMetricFamily('technicolor_devices', 'Devices', labels=['mac_address'])
        
        self.tecnicolor_info = InfoMetricFamily('technicolor', 'Info', labels=['product_vendor', 'product_name', 'software_version', 'databump_version', 'firmware_oid', 'bootloader_version', 'bootloader_oid', 'hardware_version', 'serial_number', 'mac_address', 'current_timezone'])

    def collect(self):
        self.init_metrics()

        broadband_data = self.gateway.get_broadband_modal()
        network_data = self.gateway.get_diagnostics_network_modal()
        devices_data = self.gateway.get_device_modal()
        info_data = self.gateway.get_gateway_info_modal()

        self.technicolor_broadband_data.add_metric(['tx'], broadband_data['uploaded'] * 1024 * 1024)
        self.technicolor_broadband_data.add_metric(['rx'], broadband_data['downloaded'] * 1024 * 1024)

        self.technicolor_broadband_max_line_rate.add_metric(['tx'], broadband_data['max_line_rate_tx'] * 1024 * 1024)
        self.technicolor_broadband_max_line_rate.add_metric(['rx'], broadband_data['max_line_rate_rx'] * 1024 * 1024)

        self.technicolor_broadband_line_rate.add_metric(['tx'], broadband_data['line_rate_tx'] * 1024 * 1024)
        self.technicolor_broadband_line_rate.add_metric(['rx'], broadband_data['line_rate_rx'] * 1024 * 1024)

        # ["name", "rx_bytes", "tx_bytes", "rx_packets", "tx_packets", "rx_errors", "tx_errors", "interface", "interface_type", "speed", "status"]

        for interface_data in network_data:
            label_values = [interface_data['name'], interface_data['interface'], interface_data['interface_type']]
            self.technicolor_rx_packets.add_metric(label_values, interface_data['rx_packets'])
            self.technicolor_tx_packets.add_metric(label_values, interface_data['tx_packets'])
            self.technicolor_rx_bytes.add_metric(label_values, interface_data['rx_bytes'])
            self.technicolor_tx_bytes.add_metric(label_values, interface_data['tx_bytes'])

            if interface_data['interface_type'] == 'ethernet':
                self.technicolor_ports_speed.add_metric(label_values, interface_data['speed'])

        for device_data in devices_data:
            self.technicolor_devices.add_metric([device_data['mac']], {"name": device_data['name'], "ip": device_data['ip']})

        self.technicolor_uptime.add_metric([], broadband_data['uptime'])

        del info_data['uptime']
        del info_data['system_time']
        self.tecnicolor_info.add_metric([], info_data)

        yield self.technicolor_broadband_data
        yield self.technicolor_broadband_line_rate
        yield self.technicolor_broadband_max_line_rate
        yield self.technicolor_uptime

        yield self.technicolor_rx_packets
        yield self.technicolor_tx_packets

        yield self.technicolor_rx_bytes
        yield self.technicolor_tx_bytes

        yield self.technicolor_ports_speed
        yield self.technicolor_devices

        yield self.tecnicolor_info
