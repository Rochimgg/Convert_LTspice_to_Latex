import os

import numpy as np


def ConvertForAllLTspiceFilesFormFolderToTEX(path='.', ltspice_directory=r'C:\Program Files\LTC\LTspiceXVII\lib\sym',
                                             full_example=0):
    for filename in os.listdir(path):
        if os.path.isfile(os.path.join(path, filename)):
            if filename.endswith('.asc'):
                print('Convert: ' + filename)
                LtSpiceToLatex(file_name_ltspice=filename, ltspice_directory=ltspice_directory,
                               full_example=full_example)


components_count = 0
components_add_memory = []


def LtSpiceToLatex(save_file='', file_name_ltspice='Draft.asc',
                   ltspice_directory=r'C:\Program Files\LTC\LTspiceXVII\lib\sym', full_example=0):
    global components_count
    global components_add_memory

    save_file = file_name_ltspice[0:-len(file_name_ltspice.split('.')[-1])] + r'tex'

    if not ltspice_directory[-1] == os.path.sep:
        ltspice_directory = ltspice_directory + os.path.sep

    def first_item(ls):
        if ls:
            return ls[0]

    def find_pins_in_lib(name):
        with open(ltspice_directory + name + ".asy", "r") as f:
            sym = f.readlines()
        pin = []
        words = []
        for line in sym:
            words = line.split()
            if words[0] == 'PIN':
                pin.append((int(words[1]), -int(words[2])))
        return pin

    def node_search(coordinate):
        node = [idx for idx, x1 in enumerate(node_list) if x1[0] == coordinate]
        if not node:
            node = [len(node_list)]
            node_list.append([coordinate, [], [], []])
        return node[0]

    def wire_addition(order):
        x1 = (int(order[1]), -int(order[2]))
        x2 = (int(order[3]), -int(order[4]))
        wire_quantity = len(wire_list)

        node1 = node_search(x1)
        node2 = node_search(x2)
        node_list[node1][1].append(wire_quantity)
        node_list[node2][1].append(wire_quantity)

        wire_list.append([node1, node2])

    def groundTextAddition(order):
        x1 = (int(order[1]), -int(order[2]))
        componentQuantity = len(component_list)
        node = node_search(x1)
        node_list[node][2].append(componentQuantity)
        if order[0] == 'FLAG':
            component_list.append([node, 'FLAG', '', []])
        else:
            text = ' '.join(order[5:]).replace(';', '')
            component_list.append([node, 'TEXT', text, []])

    def componentAddition(idx, order):
        x = np.array([int(order[2]), -int(order[3])])
        pin = find_pins_in_lib(order[1])
        componentQuantity = len(component_list)

        Rotation = {
            'R0': [[1, 0], [0, 1]],
            'R90': [[0, -1], [1, 0]],
            'R180': [[-1, 0], [0, -1]],
            'R270': [[0, 1], [-1, 0]],
            'M0': [[-1, 0], [0, 1]],
            'M90': [[0, -1], [-1, 0]],
            'M180': [[1, 0], [0, -1]],
            'M270': [[0, 1], [1, 0]], }

        pin = np.dot(pin, Rotation[order[4]])

        node_memory = []
        for pin_n in pin:
            node = node_search(tuple(pin_n + x))
            node_memory.append(node)
            node_list[node][2].append(componentQuantity)

        component_designation = ''
        for i in range(idx + 1, idx + 4):
            if words[i][0] == 'SYMATTR':
                component_designation = words[i][2]
                if component_designation.count('_') > 0 and component_designation.count('$') < 2:
                    component_designation = r'$' + component_designation + r'$'
                break

        global components_count
        global components_add_memory

        node_related = []
        if not order[1] in possible_component and not order[1] in specialComponentName:
            if not order[1] in components_add_memory:
                print('The following component is new: ' + order[1])
                components_add_memory.append(order[1])

            node_related = []
            for ind, t in enumerate(pin):
                node_related.append('B' + str(components_count) + ' X' + str(ind))

            components_count = components_count + 1;
            order[1] = order[1] + ' ' + (order[4] + '  ')[0:4]
            for t, name in enumerate(node_related):
                node_list[node_memory[t]][3] = name

        if not order[1] in possible_component and order[1] in specialComponentName:
            node_related = specialComponentName[order[1]]
            node_related = ['B' + str(components_count) + '.' + t for t in node_related]
            components_count = components_count + 1;
            if order[4].count('M'):
                if isSpecialComponent[order[1]].count('yscale=-1'):
                    order[1] = order[1] + r',yscale=-1' + ',xscale=-1' + ',rotate=' + '-' + order[4][1:] + r',yscale=-1'
                else:
                    order[1] = order[1] + ',xscale=-1' + ',rotate=' + '-' + order[4][1:]
            else:
                if isSpecialComponent[order[1]].count('yscale=-1'):
                    order[1] = order[1] + r',yscale=-1' + ',rotate=' + '-' + order[4][1:] + r',yscale=-1'
                else:
                    order[1] = order[1] + ',rotate=' + '-' + order[4][1:]
            for t, name in enumerate(node_related):
                node_list[node_memory[t]][3] = name

        component_list.append([node_memory, component[1], component_designation, node_related])

    def coordinateNodeScale(scale):
        for idx, x in enumerate(node_list):
            node_list[idx][0] = np.array(node_list[idx][0]) * scale

    def listsearch(x, y):
        return next((i for i, t in enumerate(x) if t == y), None)

    def get_node_name(node):
        if node_list[node][3]:
            return '(' + str(node_list[node][3]) + ')'
        else:
            return printXY(node_list[node][0])

    specialComponentName = {
        'mesfet': ['D', 'G', 'S'],
        'njf': ['D', 'G', 'S'],
        'nmos': ['D', 'G', 'S'],
        'nmos4': ['D', 'G', 'S', 'bulk'],
        'npn': ['C', 'B', 'E'],
        'npn2': ['C', 'B', 'E'],
        'npn3': ['C', 'B', 'E'],
        'pjf': ['C', 'B', 'E'],
        'pmos': ['D', 'G', 'S'],
        'pmos4': ['D', 'G', 'S', 'bulk'],
        'pnp': ['C', 'B', 'E'],
        'pnp2': ['C', 'B', 'E'],
    }

    isSpecialComponent = {
        'mesfet': 'njfet,anchor=D',
        'njf': 'njfet,anchor=D',
        'nmos': 'nigfete,anchor=D',
        'nmos4': 'nfet,anchor=D',
        'npn': 'npn,anchor=D',
        'npn2': 'npn,anchor=D',
        'npn3': 'npn,anchor=D',
        'njf': 'njfet,anchor=D',
        'pmos': 'pigfete,anchor=D,yscale=-1',
        'pmos4': 'pfet,anchor=D,yscale=-1',
        'pnp': 'pnp,anchor=D,yscale=-1',
        'pnp2': 'pnp,anchor=D,yscale=-1',
    }

    possible_component = {
        'bi': 'controlled current source,i=\ ',
        'bi2': 'controlled current source,i_=\ ',
        'bv': 'controlled voltage source,v_=\ ',
        'cap': 'C',
        'csw': 'switch',
        'current': 'current source,i=\ ',
        'diode': 'D',
        'f': 'controlled current source,i=\ ',
        'h': 'voltage source,v_=\ ',
        'ind': 'L',
        'LED': 'led',
        'load': 'vR',
        'load2': 'controlled current source,i=\ ',
        'polcap': 'eC',
        'res': 'R',
        'res2': 'R',
        'schottky': 'sDo',
        'TVSdiode': 'zDo',
        'varactor': 'VCo',
        'voltage': 'voltage source,v_=\ ',
        'zener': 'zDo', }

    def printXY(xy, offset=[0, 0]):
        return '(' + str(xy[0] - offset[0]) + ',' + str(xy[1] - offset[1]) + ')'

    def convert_new_name(name):
        ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
        result = ''.join(ones[int(i)] if i.isdigit() else str(i) for i in name)
        result = result.replace("-", "")
        return result.replace("/", "")

    def CreateDevFromLib(name, scale=1 / 64):
        with open(ltspice_directory + name + ".asy", "r") as f:
            sym = f.readlines()

        pin = []
        pinName = []
        line = []
        rect = []
        circ = []
        arc = []
        text = []
        window = []
        for l in sym:
            words = l.split()
            if words[0] == 'PIN':  # that is not drawn
                pin.append([int(words[1]) * scale, -int(words[2]) * scale])
            if words[0] == 'LINE':  # \draw (-1.5,0) -- (1.5,0);
                line.append(
                    [int(words[2]) * scale, -int(words[3]) * scale, int(words[4]) * scale, -int(words[5]) * scale])
            if words[0] == 'RECTANGLE':  # \draw (0,0) rectangle (1,1)
                rect.append(
                    [int(words[2]) * scale, -int(words[3]) * scale, int(words[4]) * scale, -int(words[5]) * scale])
            if words[0] == 'CIRCLE':  # \draw[x radius=2, y radius=1] (0,0) ellipse [];
                circ.append(
                    [int(words[2]) * scale, -int(words[3]) * scale, int(words[4]) * scale, -int(words[5]) * scale])
            if words[0] == 'ARC':  # \draw (3mm,0mm) arc (0:30:3mm);
                arc.append(
                    [int(words[2]) * scale, -int(words[3]) * scale, int(words[4]) * scale, -int(words[5]) * scale,
                     int(words[6]) * scale, -int(words[7]) * scale, int(words[8]) * scale, -int(words[9]) * scale])
            if words[0] == 'TEXT':  # \node[right] at (0,1) {bla} ;
                text.append([int(words[1]) * scale, -int(words[2]) * scale, words[3], ' '.join(words[5:])])
            if words[0] == 'WINDOW':  # that is not drawn
                window.append([int(words[2]) * scale, -int(words[3]) * scale])

        offset = pin[0] if pin else [0, 0]

        new_lib = '/def/' + convert_new_name(
            str(name)) + r'(#1)#2#3{%' + '\n' + r'  \begin{scope}[#1,transform canvas={scale=1}]' + '\n'

        for t in line:
            new_lib = new_lib + r'  \draw ' + printXY(t[0:], offset) + ' -- ' + printXY(t[2:], offset) + ';' + '\n'
        if window:  # \draw  (2,0.5) node[left] {$x$};
            t = window[0]
            new_lib = new_lib + r'  \draw ' + printXY(t[0:], offset) + ' coordinate (#2 text);' + '\n'
        for t in circ:
            new_lib = new_lib + r'  \draw[x radius=' + str((t[2] - t[0]) / 2) + ', y radius=' + str(
                (t[3] - t[1]) / 2) + ']'
            new_lib = new_lib + printXY([(t[0] + t[2]) / 2, (t[1] + t[3]) / 2], offset) + ' ellipse [];' + '\n'
        for t in arc:  # \draw (0,4)++(49: 1 and 2)  arc (49:360: 1 and 2);
            center = [(t[0] + t[2]) / 2, (t[1] + t[3]) / 2]
            Rx = (t[2] - t[0]) / 2
            Ry = (t[3] - t[1]) / 2
            start_angle = np.angle((t[4] - center[0]) + 1j * (t[5] - center[1])) * 180 / np.pi
            end_angle = np.angle((t[6] - center[0]) + 1j * (t[7] - center[1])) * 180 / np.pi
            strR = str(abs(Rx)) + ' and ' + str(abs(Ry))
            new_lib = new_lib + r'  \draw ' + printXY(center, offset) + '++( ' + str(start_angle) + ': ' + strR
            new_lib = new_lib + ')  arc (' + str(start_angle) + ':' + str(end_angle) + ': ' + strR + ');' + '\n'
        for t in rect:
            new_lib = new_lib + r'  \draw ' + printXY(t[0:], offset) + ' rectangle ' + printXY(t[2:],
                                                                                               offset) + ';' + '\n'
        for t in text:
            new_lib = new_lib + r'  \node[right] at ' + printXY(t[0:], offset) + r'{' + t[3] + r'};' + '\n'
        for ind, t in enumerate(pin):
            new_lib = new_lib + r'  \draw ' + printXY(t[0:], offset) + ' coordinate (#2 X' + str(ind) + ');' + '\n'
            pinName.append('  X' + str(ind))

        new_lib = new_lib + r'  \end{scope}' + '\n'

        if window:
            new_lib = new_lib + r'  \draw (#2 text) node[right] {#3};' + '\n'

        new_lib = new_lib + r'}' + '\n'

        return new_lib

    with open(file_name_ltspice, "r") as f:
        data = f.readlines()

    words = []
    for line in data:
        words.append(line.split())

    components_add_memory = []
    node_list = []
    component_list = []
    wire_list = []
    components_count = 0

    for idx in enumerate(words):
        if idx[1][0] == 'WIRE':
            wire_addition(idx[1])

        if idx[1][0] == 'FLAG' or idx[1][0] == 'TEXT':
            groundTextAddition(idx[1])

        if idx[1][0] == 'SYMBOL':
            componentAddition(idx[0], idx[1])

    coordinateNodeScale(1 / 64)

    for K1, K2 in wire_list:  # Wire that directly connects two components is divided into two parts
        if (len(node_list[K1][2]) == 1 and len(node_list[K2][2]) == 1
                and len(node_list[K1][1]) == 1 and len(node_list[K2][1]) == 1):
            oldWire = node_list[K1][1][0]
            newWire = len(wire_list)  # New wire index
            node_list[K2][1] = [newWire]  # Connect new wire to K2

            K3 = len(node_list)  # Add nodes between the two old nodes
            xyK3 = (node_list[K1][0] + node_list[K2][0]) / 2
            node_list.append([xyK3, [newWire, oldWire], [], []])

            wire_list.append([K3, K2])  # add new wire
            wire_list[oldWire][1] = K3  # Connect the old wire to the new knot

    current_node_index = 0
    node_coordinates = ''
    for ind, t in enumerate(node_list):
        if not node_list[ind][3] and (len(node_list[ind][1]) + len(node_list[ind][2])) > 2:
            node_list[ind][3] = 'X' + str(current_node_index)
            xy = printXY(node_list[ind][0])
            node_coordinates = node_coordinates + '\draw ' + xy + ' to[short,-*] ' + xy + ' coordinate (' + \
                               node_list[ind][3] + ');\n'
            current_node_index = current_node_index + 1

    f = open(save_file, "w")

    if full_example:
        f.write(
            '\\documentclass[a4paper,12pt]{article} \n'
            '\\pagestyle{empty} \n'
            '\\usepackage{amsmath} \n'
            '\\usepackage{tikz} \n'
            '\\usepackage[siunitx,american]{circuitikz} \n'
            '\\usetikzlibrary{bending} \n'
            '\\usetikzlibrary{arrows} \n')
        f.write('\n \n\\begin{document} \n\\centering \n')

    f.write('\\ctikzset{tripoles/mos style/arrows} \n\\begin{circuitikz}[transform shape,scale=1] \n \n')

    f.write(node_coordinates)

    for t in components_add_memory:
        f.write(CreateDevFromLib(t, scale=1 / 64))

    for node, component, name, node_name in component_list:
        if component in possible_component:
            xy = [[], []]
            for idx, c1 in enumerate(node):
                wire_number = first_item(node_list[c1][1])
                if not isinstance(wire_number, int) or node_list[c1][3]:  # No cable is connected to the component
                    xy[idx] = c1
                else:
                    if wire_list[wire_number][0] == c1:  # Component between IndexK1-IndexK2 or IndexK2-IndexK1
                        c2 = wire_list[wire_number][1]
                    else:
                        c2 = wire_list[wire_number][0]

                    xy[idx] = c2
                    wire_list[wire_number] = []
            f.write('\\draw %s to[%s,l=%s] %s ;\n' % (
                get_node_name(xy[0]), possible_component[component], name, get_node_name(xy[1])))

        if component == 'FLAG':
            f.write('\\draw %s node[ground] {} ;\n' % (get_node_name(node),))

        if component == 'TEXT':
            f.write('\\node[right] at %s {%s} ;\n' % (get_node_name(node), name))

        temp = component.split(',')[0]
        if temp in specialComponentName:
            rot = component[len(temp):]
            rotation = rot.split('rotate=')[1].split(',')[0]
            component = component.split(',')[0]
            t_node_name = node_name[0].partition(".")[0]
            if not rot.count('xscale=-1'):
                if isSpecialComponent[component].count('yscale=-1'):
                    f.write('\\draw %s node[%s](%s){\\rotatebox{%s}{\\reflectbox{%s}}} ;\n' % (
                        printXY(node_list[node[0]][0]), isSpecialComponent[component] + rot, t_node_name,
                        str(180 + int(rotation)), name))
                else:
                    f.write('\\draw %s node[%s](%s){\\rotatebox{%s}{%s}} ;\n' % (
                        printXY(node_list[node[0]][0]), isSpecialComponent[component] + rot, t_node_name,
                        str(-int(rotation)),
                        name))
            else:
                if isSpecialComponent[component].count('yscale=-1'):
                    f.write('\\draw %s node[%s](%s){\\rotatebox{%s}{%s}} ;\n' % (
                        printXY(node_list[node[0]][0]), isSpecialComponent[component] + rot, t_node_name,
                        str(180 + int(rotation)), name))
                else:
                    f.write('\\draw %s node[%s](%s){\\rotatebox{%s}{\\reflectbox{%s}}} ;\n' % (
                        printXY(node_list[node[0]][0]), isSpecialComponent[component] + rot, t_node_name,
                        str(-int(rotation)),
                        name))

        if component[:-5] in components_add_memory:
            rot = component[-4:]
            if rot[0] == 'M':
                rot = 'rotate=' + rot[1:] + ',xscale=-1'
            else:
                rot = 'rotate=' + rot[1:]

            component = component[:-5]
            t_node_name = node_name[0].partition(" ")[0]
            f.write('\\%s (shift={%s},%s) {%s} {%s};\n' % (
                convert_new_name(component), printXY(node_list[node[0]][0]), rot, t_node_name, name))
    for x in wire_list:
        if len(x) != 0:
            f.write('\\draw %s to[short,-] %s ;\n' % (get_node_name(x[0]), get_node_name(x[1])))

    f.write('\n\\end{circuitikz}')
    if full_example:
        f.write('\n\\end{document}')

    f.close()

    print('Congratulations. The run was successful.')
