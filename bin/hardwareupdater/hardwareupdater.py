# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'hardwareupdater.py'
# Bytecode version: 3.14rc3 (3627)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

import os
import sys
import serial
import struct
import time
import serial.tools.list_ports
import hid
if sys.platform == 'darwin':
    import ctypes
    hid.hidapi.hid_darwin_set_open_exclusive.argtypes = [ctypes.c_int]
    hid.hidapi.hid_darwin_set_open_exclusive.restype = None
    hid.hidapi.hid_darwin_set_open_exclusive(0)

import json
import functools

MIN_HW_ID = 68
print = functools.partial(print, flush=True)
VERSION_NUMBER = '1.5'
k_EDeviceType_Triton_BL = 0
k_EDeviceType_Proteus_BL = 1
k_EDeviceType_Triton_USB = 2
k_EDeviceType_Triton_BLE = 3
k_EDeviceType_Triton_ESB = 4
k_EDeviceType_Proteus_USB = 5
k_EDeviceType_Nereid_USB = 6
k_EDeviceClass_Triton = 0
k_EDeviceClass_Proteus = 1
Device_Type_Strings = ['Triton BL', 'Proteus BL', 'Triton USB', 'Triton BLE', 'Triton ESB', 'Proteus USB', 'Nereid USB']
ESCAPE_BYTE = b'\xac'
SOF_BYTE = b'\xad'
EOF_BYTE = b'\xae'
MESSAGE_INFO = 4659
MESSAGE_FW_BEGIN = 4660
MESSAGE_FW_DATA = 4661
MESSAGE_FW_END = 4662
MESSAGE_RESET = 4663
MESSAGE_PROVISION = 4664
RSP_ACK = 0
PROTEUS_FW_MAGIC = 779703857
PROTEUS_FIRMWARE_HEADER_MAGIC = 779703857
TRITON_FIRMWARE_HEADER_MAGIC = 3537396839
PROVISIONING_MAGIC = 2888999977
MSG_PROVISION_MAGIC = 3899499719
HID_LEN = 64
script_name = os.path.basename(__file__)
cfg_name = os.path.splitext(script_name)[0] + '.cfg'
class MyHidDevice(hid.Device):
    bcd_version = None
def usage():
    print(script_name + ' [--help | --check-for-updates | --update-all  | --update-by-serial SERNUM | --prep-by-serial SERNUM | --reboot-by-serial SERNUM | --show-all-devices]')
def sanity_check_metadata(meta):
    magic, _, _ = struct.unpack_from('<3I', meta)
    if magic!= TRITON_FIRMWARE_HEADER_MAGIC and magic!= PROTEUS_FIRMWARE_HEADER_MAGIC:
            print('ERROR: INVALID FIRMWARE FILE')
            sys.exit((-1))
def get_feature_report(device, fr_id):
    # irreducible cflow, using cdg fallback
    # ***<module>.get_feature_report: Failure: Compilation Error
    hid_len = 64
    t_start = time.time()
    if time.time() < t_start + 0.5:
        pass
    report = device.get_feature_report(fr_id, hid_len + 1)
    pass
    report_type = report[1]
    report_length = report[2]
    report_bytes = report[3:3 + report_length]
    return (report_type, report_length, report_bytes)
    except hid.HIDException:
        pass
    time.sleep(0.01)
def pad_hid_fr(blob):
    blob += b'\x00' * (HID_LEN - len(blob))
    return blob
def hex_to_ascii(input):
    return hex(input).upper().replace('X', 'x')
def get_str_attribute(device, fr_id, attribute_number, op):
    blob = struct.pack('=bBbb', fr_id, op, 1, attribute_number)
    blob = pad_hid_fr(blob)
    device.send_feature_report(blob)
    report_type, report_length, report_bytes = get_feature_report(device, fr_id)
    if not report_length or report_type!= op:
        return None
    else:
        report_bytes = report_bytes[1:]
        if report_bytes[0] == 255:
            return 'Not Provisioned'
        else:
            null_pos = report_bytes.find(0, 0)
            if null_pos == (-1):
                return 'Not Provisioned'
            else:
                str = report_bytes[:null_pos].strip(b'\x00').decode('utf-8')
                return str
def get_serial_triton(hiddev):
    return get_str_attribute(hiddev, 1, 1, 174)
def get_serial_dongle(hiddev):
    if hiddev.bcd_version == 2:
        sn = get_str_attribute(hiddev, 2, 1, 174)
        return sn
    else:
        sn = get_str_attribute(hiddev, 1, 1, 164)
        return sn
def get_build_ts_triton(hiddev):
    attrs = read_attribute_values(hiddev, 1, 131)
    return (attrs['hw_id'], attrs['build_timestamp'])
def get_build_ts_dongle(hiddev):
    if hiddev.bcd_version == 2:
        attrs = read_attribute_values(hiddev, 2, 131)
    else:
        attrs = read_attribute_values(hiddev, 1, 166)
    return (attrs['hw_id'], attrs['build_timestamp'])
def read_attribute_values(device, fr_id, opcode):
    blob = struct.pack('=bB', fr_id, opcode)
    blob = pad_hid_fr(blob)
    device.send_feature_report(blob)
    report_type, report_length, report_bytes = get_feature_report(device, fr_id)
    num_attrs = report_length // 5
    if not num_attrs:
        return {}
    else:
        format_str = '=' + 'BL' * num_attrs
        data = struct.unpack(format_str, report_bytes)
        attrs = {}
        for i in range(num_attrs):
            tag = data[i * 2]
            val = data[i * 2 + 1]
            if tag == 0:
                attrs['unique_id'] = val
            else:
                if tag == 1:
                    attrs['product_id'] = val
                else:
                    if tag == 2:
                        attrs['capabilities'] = val
                    else:
                        if tag == 4:
                            attrs['build_timestamp'] = val
                        else:
                            if tag == 5:
                                attrs['radio_build_timestamp'] = val
                            else:
                                if tag == 9:
                                    attrs['hw_id'] = val
                                else:
                                    if tag == 10:
                                        attrs['boot_build_timestamp'] = val
                                    else:
                                        if tag == 11:
                                            attrs['frame_rate'] = val
                                        else:
                                            if tag == 12:
                                                attrs['secondary_build_timestamp'] = val
                                            else:
                                                if tag == 13:
                                                    attrs['secondary_boot_build_timestamp'] = val
                                                else:
                                                    if tag == 14:
                                                        attrs['secondary_hw_id'] = val
                                                    else:
                                                        if tag == 15:
                                                            attrs['data_streaming'] = val
                                                        else:
                                                            if tag == 16:
                                                                attrs['trackpad_id'] = val
                                                            else:
                                                                if tag == 17:
                                                                    attrs['secondary_trackpad_id'] = val
        return attrs
def find_devices_by_PID(PID):
    devices = []
    for d in hid.enumerate(10462, PID):
        if d['usage_page'] >= 65280:
            hiddev = MyHidDevice(path=d['path'])
            if 'release_number' in d:
                hiddev.bcd_version = d['release_number']
            devices.append(hiddev)
    return devices
def find_units_for_update(new_triton_ts, new_proteus_ts, updateable_only):
    output = {}
    output['version'] = VERSION_NUMBER
    updates = []
    no_min_hw_id = False
    if new_triton_ts == 0 and new_proteus_ts == 0:
            no_min_hw_id = True
    allports = serial.tools.list_ports.comports()
    for port, _, hwid in allports:
        if 'VID:PID=28DE:1007' in hwid:
            time.sleep(5)
    allports = serial.tools.list_ports.comports()
    for port, _, hwid in allports:
        if 'VID:PID=28DE:1005' in hwid:
            hwid, sn, _ = get_info_from_bootloader(port)
            if hwid >= MIN_HW_ID or no_min_hw_id:
                updates.append({'type': k_EDeviceType_Triton_BL, 'Name': Device_Type_Strings[k_EDeviceType_Triton_BL], 'hardware_id': hwid, 'serial_number': sn, 'current_ts': hex_to_ascii(0), 'update_ts': hex_to_ascii(new_triton_ts), 'must_update': True})
        else:
            if 'VID:PID=28DE:1007' in hwid:
                hwid, sn, _ = get_info_from_bootloader(port)
                if hwid >= MIN_HW_ID or no_min_hw_id:
                    updates.append({'type': k_EDeviceType_Proteus_BL, 'Name': Device_Type_Strings[k_EDeviceType_Proteus_BL], 'hardware_id': hwid, 'serial_number': sn, 'current_ts': hex_to_ascii(0), 'update_ts': hex_to_ascii(new_proteus_ts), 'must_update': True})
    devices = find_devices_by_PID(4866)
    for hiddev in devices:
        sn = get_serial_triton(hiddev)
        hwid, ts = get_build_ts_triton(hiddev)
        if ts!= new_triton_ts and (hwid >= MIN_HW_ID or no_min_hw_id):
                if ts < MUST_UPDATE_TRITON_FW_TIMESTAMP:
                    must_update = True
                else:
                    must_update = False
                updates.append({'type': k_EDeviceType_Triton_USB, 'Name': Device_Type_Strings[k_EDeviceType_Triton_USB], 'hardware_id': hwid, 'serial_number': sn, 'current_ts': hex_to_ascii(ts), 'update_ts': hex_to_ascii(new_triton_ts), 'must_update': must_update})
    if not updateable_only:
        devices = find_devices_by_PID(4867)
        for hiddev in devices:
            sn = get_serial_triton(hiddev)
            hwid, ts = get_build_ts_triton(hiddev)
            if ts!= new_triton_ts and (hwid >= MIN_HW_ID or no_min_hw_id):
                    if ts < MUST_UPDATE_TRITON_FW_TIMESTAMP:
                        must_update = True
                    else:
                        must_update = False
                    updates.append({'type': k_EDeviceType_Triton_BLE, 'Name': Device_Type_Strings[k_EDeviceType_Triton_BLE], 'hardware_id': hwid, 'serial_number': sn, 'current_ts': hex_to_ascii(ts), 'update_ts': hex_to_ascii(new_triton_ts), 'must_update': must_update})
    proteuses = find_devices_by_PID(4868)
    nereids = find_devices_by_PID(4869)
    devices = proteuses + nereids
    if not updateable_only:
        for hiddev in devices:
            try:
                sn = get_serial_triton(hiddev)
            except hid.HIDException:
                continue
            hwid, ts = get_build_ts_triton(hiddev)
            if ts < MUST_UPDATE_TRITON_FW_TIMESTAMP:
                must_update = True
            else:
                must_update = False
            if ts!= new_triton_ts and (hwid >= MIN_HW_ID or no_min_hw_id):
                    updates.append({'type': k_EDeviceType_Triton_ESB, 'Name': Device_Type_Strings[k_EDeviceType_Triton_ESB], 'hardware_id': hwid, 'serial_number': sn, 'current_ts': hex_to_ascii(ts), 'update_ts': hex_to_ascii(new_triton_ts), 'must_update': must_update})
    serial_numbers = {}
    for hiddev in proteuses:
        sn = get_serial_dongle(hiddev)
        if sn in serial_numbers:
            continue
        else:
            serial_numbers[sn] = True
            hwid, ts = get_build_ts_dongle(hiddev)
            if ts!= new_proteus_ts and (hwid >= MIN_HW_ID or no_min_hw_id):
                    if ts < MUST_UPDATE_PROTEUS_FW_TIMESTAMP:
                        must_update = True
                    else:
                        must_update = False
                    updates.append({'type': k_EDeviceType_Proteus_USB, 'Name': Device_Type_Strings[k_EDeviceType_Proteus_USB], 'hardware_id': hwid, 'serial_number': sn, 'current_ts': hex_to_ascii(ts), 'update_ts': hex_to_ascii(new_proteus_ts), 'must_update': must_update})
    serial_numbers = {}
    for hiddev in nereids:
        sn = get_serial_dongle(hiddev)
        if sn in serial_numbers:
            continue
        else:
            serial_numbers[sn] = True
            hwid, ts = get_build_ts_dongle(hiddev)
            if ts!= new_proteus_ts and (hwid >= MIN_HW_ID or no_min_hw_id):
                    if ts < MUST_UPDATE_PROTEUS_FW_TIMESTAMP:
                        must_update = True
                    else:
                        must_update = False
                    updates.append({'type': k_EDeviceType_Nereid_USB, 'Name': Device_Type_Strings[k_EDeviceType_Nereid_USB], 'hardware_id': hwid, 'serial_number': sn, 'current_ts': hex_to_ascii(ts), 'update_ts': hex_to_ascii(new_proteus_ts), 'must_update': must_update})
    output['updates_available'] = updates
    return output
def get_device_class(device_type):
    if device_type == k_EDeviceType_Triton_ESB or device_type == k_EDeviceType_Triton_BLE or device_type == k_EDeviceType_Triton_USB or (device_type == k_EDeviceType_Triton_BL):
        return k_EDeviceClass_Triton
    else:
        if device_type == k_EDeviceType_Proteus_BL or device_type == k_EDeviceType_Proteus_USB or device_type == k_EDeviceType_Nereid_USB:
            return k_EDeviceClass_Proteus
        else:
            print('ERROR: No class associasted w/ device type: {}'.format(type))
            sys.exit((-1))
def find_triton_device_by_serial_number(serial):
    # ***<module>.find_triton_device_by_serial_number: Failure: Different bytecode
    triton_usb_devices = find_devices_by_PID(4866)
    triton_ble_devices = find_devices_by_PID(4867)
    proteus_esb_devices = find_devices_by_PID(4868)
    nereid_esb_devices = find_devices_by_PID(4869)
    all_devices = triton_usb_devices + triton_ble_devices + proteus_esb_devices + nereid_esb_devices
    for hiddev in all_devices:
        try:
            sn = get_serial_triton(hiddev)
        except hid.HIDException:
            continue
        if sn == serial:
            return (k_EDeviceClass_Triton, hiddev)
    return (None, None)
def find_attached_device_by_serial_number(serial):
    triton_devices = find_devices_by_PID(4866)
    for hiddev in triton_devices:
        sn = get_serial_triton(hiddev)
        if sn == serial:
            return (k_EDeviceClass_Triton, hiddev)
    proteus_devices = find_devices_by_PID(4868)
    nereid_devices = find_devices_by_PID(4869)
    dongle_devices = proteus_devices + nereid_devices
    for hiddev in dongle_devices:
        sn = get_serial_dongle(hiddev)
        if sn == serial:
            return (k_EDeviceClass_Proteus, hiddev)
    return (None, None)
def reboot_to_BL(device_class, hiddev):
    if device_class == k_EDeviceClass_Proteus:
        if hiddev.bcd_version == 2:
            blob = pad_hid_fr(b'\x02\x90')
            hiddev.send_feature_report(blob)
            return True
        else:
            blob = pad_hid_fr(b'\x01\x90')
            hiddev.send_feature_report(blob)
            if __debug__:
                pass
            return True
    else:
        blob = pad_hid_fr(b'\x01\x90')
        hiddev.send_feature_report(blob)
        return True
def reboot(device_class, hiddev):
    if device_class!= k_EDeviceClass_Triton:
        return False
    else:
        blob = pad_hid_fr(b'\x01\x95')
        hiddev.send_feature_report(blob)
        return True
def encode_msg(msg):
    escaped_msg = bytes(SOF_BYTE)
    for i in [bytes([b]) for b in msg]:
        if i == ESCAPE_BYTE:
            escaped_msg += ESCAPE_BYTE + b'\x00'
        else:
            if i == SOF_BYTE:
                escaped_msg += ESCAPE_BYTE + b'\x01'
            else:
                if i == EOF_BYTE:
                    escaped_msg += ESCAPE_BYTE + b'\x02'
                else:
                    escaped_msg += bytes(i)
    escaped_msg += EOF_BYTE
    return escaped_msg
def decode_msg(msg):
    try:
        sofpos = msg.index(SOF_BYTE)
        eofpos = msg.index(EOF_BYTE)
        m = msg[sofpos + 1:eofpos]
        ret = []
        escape_state = False
        for c in m:
            if not escape_state:
                if c!= ESCAPE_BYTE[0]:
                    ret += [c]
                else:
                    escape_state = True
            else:
                ret += [c + ESCAPE_BYTE[0]]
                escape_state = False
        return bytes(ret)
    except Exception:
        print('ERROR: Invalid message', msg)
        sys.exit((-1))
def send_msg_and_expect_ack(s, msg):
    s.write(encode_msg(msg))
    rsp = decode_msg(s.read_until(expected=EOF_BYTE))
    if len(rsp) < 1 or rsp[0]!= RSP_ACK:
        print('ERROR: Invalid response', rsp)
        sys.exit((-1))
    return rsp[1:]
def open_comport(thecomport):
    # ***<module>.open_comport: Failure: Different control flow
    try_count = 10
    if try_count >= 0:
        try:
            s = serial.Serial(thecomport, timeout=60)
            return s
        except serial.SerialException:
            try_count = try_count - 1
            time.sleep(2)
        else:
            pass
    else:
        print('ERROR: Couldn\'t open BL comport')
        sys.exit((-1))
def get_info_from_bootloader(thecomport):
    # ***<module>.get_info_from_bootloader: Failure: Different bytecode
    s = open_comport(thecomport)
    s.reset_input_buffer()
    msg = struct.pack('<H', MESSAGE_INFO)
    rsp = send_msg_and_expect_ack(s, msg)
    if len(rsp)!= 164:
        print('ERROR: BAD INFO RESPONSE: {}'.format(rsp.hex('-')))
        sys.exit((-1))
    current_provisioning = rsp[36:]
    magic, hwid, unit, pcba = struct.unpack_from('<II16s16s', current_provisioning)
    if magic == PROVISIONING_MAGIC:
        try:
            pcba_serial = pcba.decode('utf-8').split('\x00')[0]
        except UnicodeDecodeError:
            pcba_serial = 'None'
        try:
            unit_serial = unit.decode('utf-8').split('\x00')[0]
        except UnicodeDecodeError:
            unit_serial = 'None'
        return (hwid, unit_serial, pcba_serial)
    else:
        print('ERROR: BAD PROVISIONING MAGIC: {}'.format(rsp))
def program_by_serial(device_type, serial_number, app_filename):
    # ***<module>.program_by_serial: Failure: Different control flow
    if device_type!= k_EDeviceType_Triton_BL and device_type!= k_EDeviceType_Proteus_BL:
            device_class, hiddev = find_attached_device_by_serial_number(serial_number)
            if hiddev is None:
                print('ERROR: Entering BL - No device with serial number: {}'.format(serial_number))
                sys.exit((-1))
            reboot_to_BL(device_class, hiddev)
            time.sleep(4)
    device_class = get_device_class(device_type)
    found = False
    thecomport = None
    allports = serial.tools.list_ports.comports()
    for port, _, hwid in allports:
        if device_class == k_EDeviceClass_Triton and 'VID:PID=28DE:1005' in hwid:
                _, sn, _ = get_info_from_bootloader(port)
                if sn == serial_number:
                    print('DEBUG: Found TRITON matching SN`')
                    thecomport = port
                    found = True
                    break
        if device_class == k_EDeviceClass_Proteus and 'VID:PID=28DE:1007' in hwid:
                _, sn, _ = get_info_from_bootloader(port)
                if sn == serial_number:
                    print('DEBUG: Found PROTEUS matching SN')
                    thecomport = port
                    found = True
                    break
    if not found:
        print('ERROR: No device with serial number: {} found in BL'.format(serial_number))
        sys.exit((-1))
    s = open_comport(thecomport)
    s.reset_input_buffer()
    with open(app_filename, 'rb') as f:
        fwdata = f.read()
        fwmetadata = fwdata[:32]
        fwdata = fwdata[32:]
        sanity_check_metadata(fwmetadata)
    print('ERASING')
    msg = struct.pack('<H', MESSAGE_FW_BEGIN)
    send_msg_and_expect_ack(s, msg)
    print('PROGRAMMING: {}'.format(app_filename))
    size = len(fwdata)
    current = 0
    if len(fwdata) > 0:
        chunk = fwdata[:32768]
        current += 32768
        percent = current / size * 100
        if percent > 100:
            percent = 100
        print('PROGRESS: {0:.0f}%'.format(percent))
        msg = struct.pack('<HH', MESSAGE_FW_DATA, len(chunk)) + chunk
        send_msg_and_expect_ack(s, msg)
        fwdata = fwdata[32768:]
    else:
        msg = struct.pack('<H', MESSAGE_FW_END) + fwmetadata
        send_msg_and_expect_ack(s, msg)
        print('RESETTING')
        msg = struct.pack('<H', MESSAGE_RESET)
        send_msg_and_expect_ack(s, msg)
        print('SUCCESS')
def prep_by_serial(serial_number):
    print('PREPPING TRITON - SN:\t{}'.format(sn))
    device_class, hiddev = find_triton_device_by_serial_number(serial_number)
    if hiddev is None:
        print('ERROR: No device with serial number: {}'.format(serial_number))
        sys.exit((-1))
    reboot_to_BL(device_class, hiddev)
    print('SUCCESS')
def reboot_by_serial(serial_number):
    print('REBOOTING TRITON - SN:\t{}'.format(sn))
    device_class, hiddev = find_triton_device_by_serial_number(serial_number)
    if hiddev is None:
        print('ERROR: No device with serial number: {}'.format(serial_number))
        sys.exit((-1))
    reboot(device_class, hiddev)
    print('SUCCESS')
def program_by_type_sn(device_type, sn):
    if device_type == k_EDeviceType_Triton_USB:
        print('UPDATING TRITON USB - SN:\t{}'.format(sn))
        program_by_serial(device_type, sn, TRITON_FW_FILENAME)
    else:
        if device_type == k_EDeviceType_Triton_BL:
            print('UPDATING TRITON IN BL - SN:\t{}'.format(sn))
            program_by_serial(device_type, sn, TRITON_FW_FILENAME)
        else:
            if device_type == k_EDeviceType_Proteus_USB:
                print('UPDATING PROTEUS - SN:\t{}'.format(sn))
                program_by_serial(device_type, sn, PROTEUS_FW_FILENAME)
            else:
                if device_type == k_EDeviceType_Proteus_BL:
                    print('UPDATING PROTEUS IN BL - SN:\t{}'.format(sn))
                    program_by_serial(device_type, sn, PROTEUS_FW_FILENAME)
                else:
                    if device_type == k_EDeviceType_Nereid_USB:
                        print('UPDATING NEREID - SN:\t{}'.format(sn))
                        program_by_serial(device_type, sn, PROTEUS_FW_FILENAME)
                    else:
                        print('ERROR: UNKNOWN TYPE:\t{}'.format(sn))
                        sys.exit((-1))
if __debug__:
    pass
TRITON_FW_TIMESTAMP = 0
PROTEUS_FW_TIMESTAMP = 0
MUST_UPDATE_TRITON_FW_TIMESTAMP = 0
MUST_UPDATE_PROTEUS_FW_TIMESTAMP = 0
try:
    fname = cfg_name
    lines = open(fname, 'r').read().split('\n')
    for line in lines:
        sl = line.split(':')
        if sl[0] == 'TRITON_FW_TS':
            TRITON_FW_TIMESTAMP = int(sl[1], 16)
        else:
            if sl[0] == 'PROTEUS_FW_TS':
                PROTEUS_FW_TIMESTAMP = int(sl[1], 16)
            else:
                if sl[0] == 'MUST_UPDATE_TRITON_FW_TS':
                    MUST_UPDATE_TRITON_FW_TIMESTAMP = int(sl[1], 16)
                else:
                    if sl[0] == 'MUST_UPDATE_PROTEUS_FW_TS':
                        MUST_UPDATE_PROTEUS_FW_TIMESTAMP = int(sl[1], 16)
except Exception:
    print('ERROR: Could not read config file: {}'.format(fname))
    sys.exit((-1))
if TRITON_FW_TIMESTAMP == 0 or PROTEUS_FW_TIMESTAMP == 0:
    print('ERROR: Did not find complete data in config file')
    sys.exit((-1))
TRITON_FW_FILENAME = 'IBEX_FW_{}.fw'.format(hex(TRITON_FW_TIMESTAMP)[2:].upper())
PROTEUS_FW_FILENAME = 'PROTEUS_FW_{}.fw'.format(hex(PROTEUS_FW_TIMESTAMP)[2:].upper())
if len(sys.argv) == 2 and sys.argv[1] == '--show-all-devices':
    units_to_update = find_units_for_update(0, 0, False)
    print(json.dumps(units_to_update, indent=4))
else:
    if len(sys.argv) == 2 and sys.argv[1] == '--check-for-updates':
        units_to_update = find_units_for_update(TRITON_FW_TIMESTAMP, PROTEUS_FW_TIMESTAMP, False)
        print(json.dumps(units_to_update, indent=4))
    else:
        if len(sys.argv) == 2 and sys.argv[1] == '--update-all':
            updates = find_units_for_update(TRITON_FW_TIMESTAMP, PROTEUS_FW_TIMESTAMP, True)
            for unit in updates['updates_available']:
                sn = unit['serial_number']
                print('FoundType: {} SN: {}'.format(Device_Type_Strings[unit['type']], sn))
                program_by_type_sn(unit['type'], sn)
        else:
            if len(sys.argv) == 3 and sys.argv[1] == '--update-by-serial':
                sn = sys.argv[2]
                updates = find_units_for_update(TRITON_FW_TIMESTAMP, PROTEUS_FW_TIMESTAMP, True)
                found = False
                for unit in updates['updates_available']:
                    if sn == unit['serial_number']:
                        found = True
                        print('Found Type: {} SN: {}'.format(Device_Type_Strings[unit['type']], sn))
                        program_by_type_sn(unit['type'], sn)
                if not found:
                    print('ERROR: NO UNIT NEEDING UPDATE FOUND FOR SERIAL NUMBER \"{}\"'.format(sn))
                    sys.exit((-1))
            else:
                if len(sys.argv) == 3 and sys.argv[1] == '--prep-by-serial':
                    sn = sys.argv[2]
                    updates = find_units_for_update(0, 0, False)
                    found = False
                    for unit in updates['updates_available']:
                        device_type = unit['type']
                        if device_type!= k_EDeviceType_Triton_BLE and device_type!= k_EDeviceType_Triton_ESB and (device_type!= k_EDeviceType_Triton_USB):
                                    continue
                        if sn == unit['serial_number']:
                            found = True
                            print('Found Type: {} SN: {}'.format(Device_Type_Strings[unit['type']], sn))
                            prep_by_serial(sn)
                    if not found:
                        print('ERROR: NO UNIT NEEDING PREP FOUND FOR SERIAL NUMBER \"{}\"'.format(sn))
                else:
                    if len(sys.argv) == 3 and sys.argv[1] == '--reboot-by-serial':
                        sn = sys.argv[2]
                        updates = find_units_for_update(0, 0, False)
                        found = False
                        for unit in updates['updates_available']:
                            device_type = unit['type']
                            if device_type!= k_EDeviceType_Triton_BLE and device_type!= k_EDeviceType_Triton_ESB and (device_type!= k_EDeviceType_Triton_USB):
                                        continue
                            if sn == unit['serial_number']:
                                found = True
                                print('Found Type: {} SN: {}'.format(Device_Type_Strings[unit['type']], sn))
                                reboot_by_serial(sn)
                        if not found:
                            print('ERROR: NO REBOOTABLE UNIT FOUND FOR SERIAL NUMBER \"{}\"'.format(sn))
                    else:
                        usage()