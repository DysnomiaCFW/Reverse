import xml.etree.ElementTree as ET

import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


tree = ET.ElementTree()
tree.parse('nrf52833.svd')

peripherals = tree.find('peripherals')

regs_peripherals = []
for peripheral in peripherals.findall('peripheral'):
    peripheral_name = peripheral.findtext('name')
    data = {'name': peripheral_name, 'addrs': []}
    base_addr = int(peripheral.findtext('baseAddress'), 16)
    regs = peripheral.findall('registers/register')
    for reg in regs:
        reg_rel_addr = int(reg.findtext('addressOffset'), 16)
        reg_name = reg.findtext('name')
        reg_addr = base_addr + reg_rel_addr
        data['addrs'].append((reg_addr, reg_name))
    data['addrs'] = sorted(data['addrs'])
    regs_peripherals.append(data)

for peripheral in regs_peripherals:
    for reg in peripheral['addrs']:
        eprint(hex(reg[0]), peripheral['name'], reg[1])


def range_intersect(r1, r2):
    return range(max(r1.start,r2.start), min(r1.stop,r2.stop)) or None


vals = []
for idx, a in enumerate(regs_peripherals):
    if len(a['addrs']) == 0:
        continue
    for b in regs_peripherals[idx + 1:]:
        if len(b['addrs']) == 0:
            continue
        a_range = range(a['addrs'][0][0], a['addrs'][-1][0])
        b_range = range(b['addrs'][0][0], b['addrs'][-1][0])
        if range_intersect(a_range, b_range):
            vals.append((a['name'], b['name']))

to_rename = {}
derives_to_remove = []
for a, b in vals:
    pa = peripherals.find(f"peripheral[name='{a}']")
    pb = peripherals.find(f"peripheral[name='{b}']")

    if pa is None or pb is None:
        # Probably already got merged.
        continue

    eprint("Merging", a, b)
    if a not in to_rename:
        to_rename[a] = a
    to_rename[a] += '_' + b
    derives_to_remove.append(b)
    ra = pa.find('registers')
    rb = pb.find('registers')

    for b_elem in rb.iter():
        # Check if ra already has that element.
        regname = b_elem.findtext('name')
        a_elem = ra.find(f"register[name='{regname}']")
        if a_elem is not None:
            continue
        ra.append(b_elem)


    peripherals.remove(pb)


for old, new in to_rename.items():
    pa = peripherals.find(f"peripheral[name='{old}']")
    pa.find('name').text = new

    for derived_a in peripherals.findall(f"peripheral[@derivedFrom='{old}']"):
        derived_a.attrib['derivedFrom'] = new


for old in derives_to_remove:
    for pa in peripherals.findall(f"peripheral[@derivedFrom='{old}']"):
        eprint('Removing', pa.findtext('name'))
        peripherals.remove(pa)


# Manually expand derivedFrom, since ghidrasvd doesn't support it.
for new_peripheral in peripherals.findall("peripheral[@derivedFrom]"):
    peripherals.remove(new_peripheral)
    derived_from_text = new_peripheral.attrib['derivedFrom']
    derived_from_peripheral = peripherals.find(f"peripheral[name='{derived_from_text}']")
    derived_from_peripheral = ET.fromstring(ET.tostring(derived_from_peripheral, encoding='unicode'))
    for item in new_peripheral:
        item_from_peripheral = derived_from_peripheral.find(item.tag)
        if item_from_peripheral is not None:
            derived_from_peripheral.remove(item_from_peripheral)
        derived_from_peripheral.append(item)

    peripherals.append(derived_from_peripheral)

# Manual fixes.
peripherals.find("peripheral[name='P0']/addressBlock/size").text = '0x300'
peripherals.find("peripheral[name='P1']/addressBlock/size").text = '0x300'

peripherals.find("peripheral[name='NVMC']/addressBlock/size").text = '0x800'
peripherals.find("peripheral[name='ACL']/baseAddress").text = '0x4001E800'
peripherals.find("peripheral[name='ACL']/addressBlock/size").text = '0x800'
peripherals.find("peripheral[name='ACL']/registers/cluster/addressOffset").text = '0'



ET.dump(tree)

#for addr, peripheral_name, reg_name in regs_peripherals:
#    if (addr, reg_name) in viewed_set:
#        print("           " + peripheral_name)
#        continue
#    addrs.append(())
#    print(hex(addr), peripheral_name, reg_name)
#    viewed_set.add((addr, reg_name))
