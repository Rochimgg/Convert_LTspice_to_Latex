#!/usr/local/bin/python3

import os, sys

import numpy as np

FULL_EXAMPLE_HEADER = '''\\documentclass[a4paper,12pt]{article}
\\pagestyle{empty}
\\usepackage{amsmath}
\\usepackage{tikz}
\\usepackage[siunitx,american]{circuitikz}
\\usetikzlibrary{bending}
\\usetikzlibrary{arrows}

\\begin{document}
'''

CIRCUIT_BEGINNING = '''\\ctikzset{tripoles/mos style/arrows}
\\begin{circuitikz}[transform shape,scale=1]
\\begin{center}
'''

CIRCUIT_END = '''
\\end{circuitikz}
\\end{center}\n'''

END_DOCUMENT = '''\n\\end{document}'''

def write_full_example_header(file):
    file.write(FULL_EXAMPLE_HEADER)

def convert_all_ltspice_form_dir_to_tex(path='.', ltspice_directory=r'C:\Program Files\LTC\LTspiceXVII\lib\sym',
                                        full_example=0):
    for filename in os.listdir(path):
        if os.path.isfile(os.path.join(path, filename)) and filename.endswith('.asc'):
            print('Convert: ' + filename)
            ltspice_to_latex(ltspice_directory=ltspice_directory, full_example=full_example)


components_count = 0
components_add_memory = []


def ltspice_to_latex(file_name_ltspice='Draft.asc', ltspice_directory=r'C:\Program Files\LTC\LTspiceXVII\lib\sym',
                     full_example=0):
    global components_count
    global components_add_memory

    save_file = file_name_ltspice[0:-len(file_name_ltspice.split('.')[-1])] + r'tex'

    if not ltspice_directory[-1] == os.path.sep:
        ltspice_directory = ltspice_directory + os.path.sep

    def first_item(ls):
        if ls: return ls[0]

    def find_pins_in_lib(some_name):
        with open(ltspice_directory + some_name + ".asy", "r") as a_file:
            sym = a_file.readlines()
        pin = []
        for a_line in sym:
            some_words = a_line.split()
            if some_words[0] == 'PIN':
                pin.append((int(some_words[1]), -int(some_words[2])))
        return pin

    def node_search(coordinate):
        a_node = [idx for idx, x1 in enumerate(node_list) if x1[0] == coordinate]
        if not a_node:
            a_node = [len(node_list)]
            node_list.append([coordinate, [], [], []])
        return a_node[0]

    def wire_addition(order):
        x1 = (int(order[1]), -int(order[2]))
        x2 = (int(order[3]), -int(order[4]))
        wire_quantity = len(wire_list)

        node1 = node_search(x1)
        node2 = node_search(x2)
        node_list[node1][1].append(wire_quantity)
        node_list[node2][1].append(wire_quantity)

        wire_list.append([node1, node2])

    def ground_text_addition(order):
        x1 = (int(order[1]), -int(order[2]))
        component_quantity = len(component_list)
        a_node = node_search(x1)
        node_list[a_node][2].append(component_quantity)
        if order[0] == 'FLAG':
            component_list.append([a_node, 'FLAG', '', []])
        else:
            text = ' '.join(order[5:]).replace(';', '')
            component_list.append([a_node, 'TEXT', text, []])

    def component_addition(an_idx, order):
        x = np.array([int(order[2]), -int(order[3])])
        pin = find_pins_in_lib(order[1])
        component_quantity = len(component_list)

        rotations = {
            'R0': [[1, 0], [0, 1]],
            'R90': [[0, -1], [1, 0]],
            'R180': [[-1, 0], [0, -1]],
            'R270': [[0, 1], [-1, 0]],
            'M0': [[-1, 0], [0, 1]],
            'M90': [[0, -1], [-1, 0]],
            'M180': [[1, 0], [0, -1]],
            'M270': [[0, 1], [1, 0]], }

        pin = np.dot(pin, rotations[order[4]])

        node_memory = []
        for pin_n in pin:
            a_node = node_search(tuple(pin_n + x))
            node_memory.append(a_node)
            node_list[a_node][2].append(component_quantity)

        for i in range(an_idx + 1, an_idx + 4):
            if words[i][0] == 'SYMATTR':
                component_designation = words[i][2]
                if component_designation.count('_') > 0 and component_designation.count('$') < 2:
                    component_designation = r'$' + component_designation + r'$'
                break

        global components_count
        global components_add_memory
        node_related = []

        if not order[1] in possible_components and not order[1] in special_components_names:
            if not order[1] in components_add_memory:
                print('The following component is new: ' + order[1])
                components_add_memory.append(order[1])

            node_related = []
            for ind, y0 in enumerate(pin):
                node_related.append('B' + str(components_count) + ' X' + str(ind))

            components_count = components_count + 1
            order[1] = order[1] + ' ' + (order[4] + '  ')[0:4]
            for x0, a_name in enumerate(node_related):
                node_list[node_memory[x0]][3] = a_name

        if not order[1] in possible_components and order[1] in special_components_names:
            node_related = special_components_names[order[1]]
            node_related = ['B' + str(components_count) + '.' + t for t in node_related]
            components_count = components_count + 1
            if order[4].count('M'):
                if special_components[order[1]].count('yscale=-1'):
                    order[1] = order[1] + r',yscale=-1' + ',xscale=-1' + ',rotate=' + '-' + order[4][1:] + r',yscale=-1'
                else:
                    order[1] = order[1] + ',xscale=-1' + ',rotate=' + '-' + order[4][1:]
            else:
                if special_components[order[1]].count('yscale=-1'):
                    order[1] = order[1] + r',yscale=-1' + ',rotate=' + '-' + order[4][1:] + r',yscale=-1'
                else:
                    order[1] = order[1] + ',rotate=' + '-' + order[4][1:]
            for x0, a_name in enumerate(node_related):
                node_list[node_memory[x0]][3] = a_name

        component_list.append([node_memory, order[1], component_designation, node_related])

    def coordinate_node_scale(scale):
        for idx_i, data_i in enumerate(node_list):
            node_list[idx_i][0] = np.array(node_list[idx_i][0]) * scale

    def get_node_name(a_node):
        if node_list[a_node][3]:
            return '(' + str(node_list[a_node][3]) + ')'
        else:
            return print_xy(node_list[a_node][0])

    special_components_names = {
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

    special_components = {
        'mesfet': 'njfet,anchor=D',
        'njf': 'njfet,anchor=D',
        'nmos': 'nigfete,anchor=D',
        'nmos4': 'nfet,anchor=D',
        'npn': 'npn,anchor=D',
        'npn2': 'npn,anchor=D',
        'npn3': 'npn,anchor=D',
        'pmos': 'pigfete,anchor=D,yscale=-1',
        'pmos4': 'pfet,anchor=D,yscale=-1',
        'pnp': 'pnp,anchor=D,yscale=-1',
        'pnp2': 'pnp,anchor=D,yscale=-1',
    }

    possible_components = {
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

    def print_xy(coordinates, offset=None):
        if offset is None:
            offset = [0, 0]
        return '(' + str(coordinates[0] - offset[0]) + ',' + str(coordinates[1] - offset[1]) + ')'

    def convert_new_name(a_name):
        ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
        result = ''.join(ones[int(i)] if i.isdigit() else str(i) for i in a_name)
        result = result.replace("-", "")
        return result.replace("/", "")

    def create_dev_from_lib(a_name, scale=1 / 64):
        with open(ltspice_directory + a_name + ".asy", "r") as fi:
            sym = fi.readlines()

        pin = []
        pin_name = []
        line = []
        rect = []
        circ = []
        arc = []
        text = []
        window = []
        for l in sym:
            line_words = l.split()
            if line_words[0] == 'PIN':  # that is not drawn
                pin.append([int(line_words[1]) * scale, -int(line_words[2]) * scale])
            if line_words[0] == 'LINE':  # \draw (-1.5,0) -- (1.5,0);
                line.append(
                    [int(line_words[2]) * scale, -int(line_words[3]) * scale, int(line_words[4]) * scale,
                     -int(line_words[5]) * scale])
            if line_words[0] == 'RECTANGLE':  # \draw (0,0) rectangle (1,1)
                rect.append(
                    [int(line_words[2]) * scale, -int(line_words[3]) * scale, int(line_words[4]) * scale,
                     -int(line_words[5]) * scale])
            if line_words[0] == 'CIRCLE':  # \draw[x radius=2, y radius=1] (0,0) ellipse [];
                circ.append(
                    [int(line_words[2]) * scale, -int(line_words[3]) * scale, int(line_words[4]) * scale,
                     -int(line_words[5]) * scale])
            if line_words[0] == 'ARC':  # \draw (3mm,0mm) arc (0:30:3mm);
                arc.append(
                    [int(line_words[2]) * scale, -int(line_words[3]) * scale, int(line_words[4]) * scale,
                     -int(line_words[5]) * scale,
                     int(line_words[6]) * scale, -int(line_words[7]) * scale, int(line_words[8]) * scale,
                     -int(line_words[9]) * scale])
            if line_words[0] == 'TEXT':  # \node[right] at (0,1) {bla} ;
                text.append(
                    [int(line_words[1]) * scale, -int(line_words[2]) * scale, line_words[3], ' '.join(line_words[5:])])
            if line_words[0] == 'WINDOW':  # that is not drawn
                window.append([int(line_words[2]) * scale, -int(line_words[3]) * scale])

        offset = pin[0] if pin else [0, 0]

        new_lib = '/def/' + convert_new_name(
            str(name)) + r'(#1)#2#3{%' + '\n' + r'  \begin{scope}[#1,transform canvas={scale=1}]' + '\n'

        for t in line:
            new_lib = new_lib + r'  \draw ' + print_xy(t[0:], offset) + ' -- ' + print_xy(t[2:], offset) + ';' + '\n'
        if window:  # \draw  (2,0.5) node[left] {$x$};
            t = window[0]
            new_lib = new_lib + r'  \draw ' + print_xy(t[0:], offset) + ' coordinate (#2 text);' + '\n'
        for t in circ:
            new_lib = new_lib + r'  \draw[x radius=' + str((t[2] - t[0]) / 2) + ', y radius=' + str(
                (t[3] - t[1]) / 2) + ']'
            new_lib = new_lib + print_xy([(t[0] + t[2]) / 2, (t[1] + t[3]) / 2], offset) + ' ellipse [];' + '\n'
        for t in arc:  # \draw (0,4)++(49: 1 and 2)  arc (49:360: 1 and 2);
            center = [(t[0] + t[2]) / 2, (t[1] + t[3]) / 2]
            rx = (t[2] - t[0]) / 2
            ry = (t[3] - t[1]) / 2
            start_angle = np.angle((t[4] - center[0]) + 1j * (t[5] - center[1])) * 180 / np.pi
            end_angle = np.angle((t[6] - center[0]) + 1j * (t[7] - center[1])) * 180 / np.pi
            str_r = str(abs(rx)) + ' and ' + str(abs(ry))
            new_lib = new_lib + r'  \draw ' + print_xy(center, offset) + '++( ' + str(start_angle) + ': ' + str_r
            new_lib = new_lib + ')  arc (' + str(start_angle) + ':' + str(end_angle) + ': ' + str_r + ');' + '\n'
        for t in rect:
            new_lib = new_lib + r'  \draw ' + print_xy(t[0:], offset) + ' rectangle ' + print_xy(t[2:],
                                                                                                 offset) + ';' + '\n'
        for t in text:
            new_lib = new_lib + r'  \node[right] at ' + print_xy(t[0:], offset) + r'{' + str(t[3]) + r'};' + '\n'
        for ind, t in enumerate(pin):
            new_lib = new_lib + r'  \draw ' + print_xy(t[0:], offset) + ' coordinate (#2 X' + str(ind) + ');' + '\n'
            pin_name.append('  X' + str(ind))

        new_lib = new_lib + r'  \end{scope}' + '\n'

        if window:
            new_lib = new_lib + r'  \draw (#2 text) node[right] {#3};' + '\n'

        new_lib = new_lib + r'}' + '\n'
        return new_lib


    with open(file_name_ltspice, "r") as fi:
        data = fi.readlines()

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
            ground_text_addition(idx[1])

        if idx[1][0] == 'SYMBOL':
            component_addition(idx[0], idx[1])

    coordinate_node_scale(1 / 64)

    for c1, c2 in wire_list:  # Wire that directly connects two components is divided into two parts
        if (len(node_list[c1][2]) == 1 and len(node_list[c2][2]) == 1
                and len(node_list[c1][1]) == 1 and len(node_list[c2][1]) == 1):
            old_wire = node_list[c1][1][0]
            new_wire = len(wire_list)  # New wire index
            node_list[c2][1] = [new_wire]  # Connect new wire to K2

            c3 = len(node_list)  # Add nodes between the two old nodes
            xy_c3 = (node_list[c1][0] + node_list[c2][0]) / 2
            node_list.append([xy_c3, [new_wire, old_wire], [], []])

            wire_list.append([c3, c2])  # add new wire
            wire_list[old_wire][1] = c3  # Connect the old wire to the new knot

    current_node_index = 0
    node_coordinates = ''
    for ind, t in enumerate(node_list):
        if not node_list[ind][3] and (len(node_list[ind][1]) + len(node_list[ind][2])) > 2:
            node_list[ind][3] = 'X' + str(current_node_index)
            xy = print_xy(node_list[ind][0])
            node_coordinates = node_coordinates + '\draw ' + xy + ' to[short,-*] '
            node_coordinates += xy + ' coordinate (' + str(node_list[ind][3]) + ');\n'
            current_node_index = current_node_index + 1

    f = open(save_file, "w")

    if full_example:
        write_full_example_header(f)

    f.write(CIRCUIT_BEGINNING)

    f.write(node_coordinates)

    for t in components_add_memory:
        f.write(create_dev_from_lib(t, scale=1 / 64))

    for node, component, name, node_name in component_list:
        if component in possible_components:
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
                get_node_name(xy[0]), possible_components[component], name, get_node_name(xy[1])))

        if component == 'FLAG':
            f.write('\\draw %s node[ground] {} ;\n' % (get_node_name(node),))

        if component == 'TEXT':
            f.write('\\node[right] at %s {%s} ;\n' % (get_node_name(node), name))

        temp = component.split(',')[0]
        if temp in special_components_names:
            rot = component[len(temp):]
            rotation = rot.split('rotate=')[1].split(',')[0]
            component = component.split(',')[0]
            t_node_name = node_name[0].partition(".")[0]
            if not rot.count('xscale=-1'):
                if special_components[component].count('yscale=-1'):
                    f.write('\\draw %s node[%s](%s){\\rotatebox{%s}{\\reflectbox{%s}}} ;\n' % (
                        print_xy(node_list[node[0]][0]), special_components[component] + rot, t_node_name,
                        str(180 + int(rotation)), name))
                else:
                    f.write('\\draw %s node[%s](%s){\\rotatebox{%s}{%s}} ;\n' % (
                        print_xy(node_list[node[0]][0]), special_components[component] + rot, t_node_name,
                        str(-int(rotation)),
                        name))
            else:
                if special_components[component].count('yscale=-1'):
                    f.write('\\draw %s node[%s](%s){\\rotatebox{%s}{%s}} ;\n' % (
                        print_xy(node_list[node[0]][0]), special_components[component] + rot, t_node_name,
                        str(180 + int(rotation)), name))
                else:
                    f.write('\\draw %s node[%s](%s){\\rotatebox{%s}{\\reflectbox{%s}}} ;\n' % (
                        print_xy(node_list[node[0]][0]), special_components[component] + rot, t_node_name,
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
                convert_new_name(component), print_xy(node_list[node[0]][0]), rot, t_node_name, name))

    for x in wire_list:
        if len(x) != 0:
            f.write('\\draw %s to[short,-] %s ;\n' % (get_node_name(x[0]), get_node_name(x[1])))

    f.write(CIRCUIT_END)
    if full_example:
        f.write(END_DOCUMENT)

    f.close()

    print('Congratulations. The run was successful.')

def main():
    print(sys.argv)

    '''full = False
    if "-full" in sys.argv[1:]:
        full = True'''
    full = "-full" in sys.argv[1:]

    ltspice_to_latex('/Users/rgallo/Desktop/adc-semana-1.asc', '/Users/rgallo/sym', full_example=full)

if __name__ == '__main__':
    main()
