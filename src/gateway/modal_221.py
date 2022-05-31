import re

# from tkinter.tix import Tree
import html2text

from bs4 import BeautifulSoup

h = html2text.HTML2Text()
h.body_width = 0

regex_broadband_modal = re.compile(
    r" {2}Line Rate +(?P<us>[0-9.]+)"
    r" Mbps (?P<ds>[0-9.]+) Mbps *Data Transferred +(?P<uploaded>[0-9.]+)"
    r" .Bytes (?P<downloaded>[0-9.]+) .Bytes "
)

regex_device_modal = re.compile(
    r"(?P<name>[\w\-_]+) ?\|"
    r" ?(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})? ?\|"
    r" ?(?P<mac>[\d\w]{2}:[\d\w]{2}:[\d\w]{2}:[\d\w]{2}:[\d\w]{2}:[\d\w]{2})"
)

regex_port_speed = re.compile(r"\((\d+) Mbps\)")

regex_line_rate = re.compile(
    r"([+-]?[0-9]*[.]?[0-9]+) Mbps\s+([+-]?[0-9]*[.]?[0-9]+) Mbps"
)

regex_data_transferred = re.compile(
    r"([+-]?[0-9]*[.]?[0-9]+) MBytes\s+([+-]?[0-9]*[.]?[0-9]+) MBytes"
)

regex_uptime = re.compile(r"(\d+)")


def get_gateway_info_modal(content):
    soup = BeautifulSoup(content, features="lxml")

    product_vendor = soup.find_all("span", id="Product Vendor")[0].text
    product_name = soup.find_all("span", id="Product Name")[0].text
    software_version = soup.find_all("span", id="Software Version")[0].text
    databump_version = soup.find_all("span", id="Datapump Version")[0].text
    firmware_oid = soup.find_all("span", id="Firmware OID")[0].text
    bootloader_version = soup.find_all("span", id="Bootloader Version")[0].text
    bootloader_oid = soup.find_all("span", id="Bootloader OID")[0].text
    hardware_version = soup.find_all("span", id="Hardware Version")[0].text
    serial_number = soup.find_all("span", id="Serial Number")[0].text
    mac_address = soup.find_all("span", id="MAC Address")[0].text
    uptime = parse_uptime(soup.find_all("span", id="Uptime")[0].text)
    system_time = soup.find_all("span", id="System Time")[0].text
    current_timezone = soup.find_all("span", id="Current Timezone")[0].text

    return {
        "product_vendor": product_vendor,
        "product_name": product_name,
        "software_version": software_version,
        "databump_version": databump_version,
        "firmware_oid": firmware_oid,
        "bootloader_version": bootloader_version,
        "bootloader_oid": bootloader_oid,
        "hardware_version": hardware_version,
        "serial_number": serial_number,
        "mac_address": mac_address,
        "uptime": uptime,
        "system_time": system_time,
        "current_timezone": current_timezone,
    }


def get_broadband_modal_old(content):
    body = h.handle(content)
    body = body[body.find("DSL Status") : body.find("Close")]
    body = body.replace("_", "").replace("\n", " ")
    return {
        key: float(value)
        for key, value in regex_broadband_modal.search(body).groupdict().items()
    }


def get_broadband_modal(content):
    soup = BeautifulSoup(content, features="lxml")

    uptime_text = soup.find_all("span", id="dsl_uptime")[0].text
    uptime = parse_uptime(uptime_text)

    max_line_rate_text = soup.find_all("span", id="dsl_max_linerate")[0].text
    max_line_rate_rx, max_line_rate_tx = parse_line_rate(max_line_rate_text)

    line_rate_text = soup.find_all("span", id="dsl_linerate")[0].text
    line_rate_rx, line_rate_tx = parse_line_rate(line_rate_text)

    data_transferred_text = soup.find_all("span", id="dsl_transfered")[0].text
    data_transferred_rx, data_transferred_tx = parse_data_transferred(
        data_transferred_text
    )

    return {
        "max_line_rate_tx": max_line_rate_tx,
        "max_line_rate_rx": max_line_rate_rx,
        "line_rate_tx": line_rate_tx,
        "line_rate_rx": line_rate_rx,
        "uploaded": data_transferred_tx,
        "downloaded": data_transferred_rx,
        "uptime": uptime,
    }


def get_device_modal(content):
    data = []
    soup = BeautifulSoup(content, features="lxml")
    devices = soup.find_all("div", {"class": "popUp smallcard span4"})
    rows = soup.fieldset.find_all("tr")
    if len(devices) > 0:
        for device in devices:
            device_contents = device.contents
            name = device_contents[1].contents[1].contents[1].text
            ip = device_contents[3].contents[3].contents[1].text
            mac = device_contents[3].contents[5].contents[1].text
            data.append({"name": name, "ip": ip, "mac": mac})

    if len(rows) > 0:
        for row in rows:
            cols = row.find_all("td")
            cols = [ele.text.strip() for ele in cols]
            if len(cols) == 0:
                continue
            if len(cols) == 6:
                data.append({"name": cols[1], "ip": cols[2], "mac": cols[3]})
            if len(cols) == 12:
                data.append({"name": cols[1], "ip": cols[2], "mac": cols[4]})
            if len(cols) == 8:
                data.append({"name": cols[2], "ip": cols[3], "mac": cols[4]})
    return data


def get_diagnostics_network_modal(content):
    soup = BeautifulSoup(content, features="lxml")
    interfaces_group = soup.find_all(id="networkstats")

    if len(interfaces_group) != 1:
        print(
            f"Error: Wrong number of networkstats div ({len(interfaces_group)} instead of 1)"
        )
        return []

    sockets = parse_sockets(soup.find_all("div", {"class": "span2 simple-desc"}))
    data = parse_network_stats(interfaces_group[0].find_all("tr"), sockets)
    return data


def parse_network_stats(interface_rows, sockets):
    data = []
    column_names = [
        "name",
        "rx_bytes",
        "tx_bytes",
        "rx_packets",
        "tx_packets",
        "rx_errors",
        "tx_errors",
        "interface",
        "interface_type",
        "speed",
        "status",
    ]

    for interface_row in interface_rows:
        cols = interface_row.find_all("td")
        cols = [item.text.strip() for item in cols]
        if len(cols) == 0:
            continue

        if len(cols) != 8:
            print(f"Error: Wrong number of columns ({len(cols)} instead of 8)")
            continue

        cols = [
            int(c) if i in range(1, 7) else c for i, c in enumerate(cols)
        ]  # convert colomns to int
        interface_name = interface_row.find_all(id="Reset Stats")[0]["data-value"]

        if interface_name in sockets:
            socket = sockets[interface_name]
            values = cols[0:7] + [
                interface_name,
                "ethernet",
                socket["speed"],
                socket["status"],
            ]
        else:
            values = cols[0:7] + [interface_name, "wifi", -1, ""]

        data.append(dict(zip(column_names, values)))
    return data


def parse_sockets(socket_divs):
    sockets = {}
    for socket in socket_divs:
        paragraphs = socket.find_all("p", {"class": "socket-legend"})

        if len(paragraphs) == 0:
            continue

        id = paragraphs[0]["id"]
        status = paragraphs[0].text.strip()

        if len(paragraphs) == 1:  # disconnected
            sockets[id] = {"name": id, "speed": 0, "status": status}
            continue

        speed = parse_speed(paragraphs[1].text)

        sockets[id] = {"name": id, "speed": speed, "status": status}
    return sockets


def parse_speed(speed):
    # format: (100 Mbps) <something>
    if speed == "":
        return 0
    return int(regex_port_speed.search(speed).groups()[0])


def parse_line_rate(line_rate):
    # format: '  21.75 Mbps    90.36 Mbps'
    tx, rx = regex_line_rate.search(line_rate).groups()
    return float(rx), float(tx)


def parse_data_transferred(data_transferred_text):
    # format: '  898.57 MBytes     3973.16 MBytes'
    tx, rx = regex_data_transferred.search(data_transferred_text).groups()
    return float(rx), float(tx)


def parse_uptime(uptime_text):
    # format: '3 days 13 hours 4 minutes 31 seconds'
    coefs = [86400, 3600, 60, 1]

    time_spans = regex_uptime.findall(uptime_text)
    time_spans = pad_list(time_spans, len(coefs), front=True, padding_value=0)

    time = sum([int(span) * coef for span, coef in zip(time_spans, coefs)])
    return time


def pad_list(A, length, front=True, padding_value=None):
    if not front:
        return A + [padding_value] * (length - len(A))
    return [padding_value] * (length - len(A)) + A
