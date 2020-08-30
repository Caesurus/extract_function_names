#!/usr/bin/env python3
import argparse
import json
import re
from collections import OrderedDict
from enum import Enum
from pprint import pprint


class TableType(Enum):
    RoutinesFirst = 1
    Intermingled = 2


class PDFTextParser(object):
    def __init__(self):
        self.text = []
        self.idx = 0

        self.PAGE_SIZE = 100
        self.TABLE_TYPE_RANGE = 10
        self.TABLE_HEADING_RANGE = 30
        self.SEARCH_BACKWARD_RANGE = 6

        self.regex_libname = r'.*\s(?P<lib_name>\w+Lib)'
        self.regex_function = r'^(?P<function_name>\w+)\(\s*\)\s*(?P<description>.*)'
        self.regex_page_number = r'^\d\d\d+$'

    def parse(self, text_chunk):
        self.text = text_chunk.split('\n')
        for i in range(len(self.text)):
            self.text[i] = self.text[i].strip()

    def find_next_table_idx(self):
        try:
            for i in range(self.idx, len(self.text)):
                line = self.text[i]
                if line.startswith('Table') and 1 == line.count('Table'):
                    if '.' in line:
                        continue
                    return i
        except:
            pass
        return None

    def search_libname_in_range(self, start, end):
        lib_name = None
        for i in range(end, start, -1):
            m = re.match(self.regex_libname, ' ' + self.text[i])
            if m:
                lib_name = m.groupdict()['lib_name']
                break
        return lib_name

    def _get_function_name(self, line):
        function_name = None
        description = None
        m = re.match(self.regex_function, line)
        if m:
            function_name = m.groupdict()['function_name']
            description = self.sanitize_string(m.groupdict()['description'])
        return function_name, description

    def table_type(self, idx):
        for i in range(idx, idx + self.TABLE_TYPE_RANGE):
            if self.text[i].startswith('Routine') or self.text[i].startswith('Call'):
                if self.text[i + 2] == 'Description':
                    self.idx = i + 2
                    return TableType.Intermingled.value
                break
        if i + 1 == idx + self.TABLE_TYPE_RANGE:
            return None
        return TableType.RoutinesFirst.value

    def process_table_at_index(self, idx):
        self.idx = idx
        self.idx = self.find_next_table_idx()
        tbl_name, tbl_desc = self.get_table_name_and_description(self.idx)
        table_info = {'tbl_name': tbl_name, 'tbl_description': tbl_desc}

        start = self.idx - self.SEARCH_BACKWARD_RANGE
        if start < 0:
            start = 0

        table_info['lib_name'] = self.search_libname_in_range(start, self.idx)
        table_info['type'] = self.table_type(self.idx)
        table_info['functions'] = []
        table_info['descriptions'] = []

        if TableType.RoutinesFirst.value == table_info['type']:
            for i in range(self.idx, self.idx + self.PAGE_SIZE):
                line = self.text[i]
                if 'Description' == line:
                    # End of the routine descriptions
                    break
                function_name, maybe_desc = self._get_function_name(line)
                if function_name:
                    table_info['functions'].append(function_name)
                if maybe_desc:
                    table_info['descriptions'].append(maybe_desc.strip())
            self.idx = i + 1
            description = ""
            for i in range(self.idx, self.idx + self.PAGE_SIZE):
                line = self.text[i]
                description += line
                if len(self.text[i + 1]) == 0:
                    table_info['descriptions'].append(description.strip())
                    description = ""
                    if len(table_info['descriptions']) == len(table_info['functions']):
                        break
            self.idx = i + 1
        elif TableType.Intermingled.value == table_info['type']:
            flag_found_function = False
            for i in range(self.idx, self.idx + self.PAGE_SIZE):
                if i < self.idx:
                    # if we've processed a block of description text
                    # we move self.idx forward, but i will trail. So just cont
                    continue
                line = self.text[i]
                if '' == line:
                    continue

                if re.match(self.regex_page_number, line):
                    # reached the end of the page... done for now.
                    break

                function_name, maybe_desc = self._get_function_name(line)
                if maybe_desc:
                    table_info['descriptions'].append(maybe_desc.strip())

                if function_name:
                    table_info['functions'].append(function_name)
                    if '' == maybe_desc:
                        flag_found_function = True
                elif flag_found_function:
                    if len(table_info['descriptions']) < len(table_info['functions']):
                        idx, description = self.extract_description_block_at_block(i)
                        self.idx = idx
                        table_info['descriptions'].append(description.strip())
        else:
            # this is not a table we want to parse
            # advance idx so next reach for a table finds the next one
            self.idx += 1
            pass

        return table_info

    def extract_description_block_at_block(self, idx):
        description = ""
        for i in range(idx, idx + self.PAGE_SIZE):
            line = self.text[i]
            if '' != line:
                description = description + ' ' + line
            else:
                break
        return i, description

    @staticmethod
    def sanitize_string(input):
        return input.encode('ascii', 'ignore').decode('iso-8859-1')

    def get_table_name_and_description(self, idx):
        regex = r'^(?P<tbl_name>Table\s+[\w+\d+]+.\d+)\s*?(?P<tbl_description>.*)'
        line = self.text[idx]

        m = re.match(regex, self.text[idx])
        if m:
            desc = m['tbl_description']
            if desc == '' or desc is None:
                desc = self.text[idx + 2]

            desc = self.sanitize_string(desc)
            desc = desc.replace('(contd)', '').strip()
            return m['tbl_name'], desc

        return None, None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='parse text pdf output for symbols')
    parser.add_argument('-f', '--files', required=True, nargs='+', help='pass file/files to analyze')
    parser.add_argument('-o', '--output', help='json file to output to')

    args = parser.parse_args()
    library_dict = OrderedDict()

    for filename in args.files:
        with open(filename, 'r', encoding="ISO-8859-1") as f:
            data = f.read()
            pdf_p = PDFTextParser()
            pdf_p.parse(data)
            idx = 0
            while idx < len(data):
                idx = pdf_p.find_next_table_idx()
                if idx:
                    pdf_p.idx = idx
                    table_info = pdf_p.process_table_at_index(idx)
                    if table_info['type']:
                        tblName = table_info['tbl_name']
                        if tblName is None:
                            tblName = 'UnKnown'

                        if tblName not in library_dict:
                            library_dict[tblName] = {'table_name': table_info['tbl_name'],
                                                     'lib_name': None,
                                                     'description': table_info['tbl_description'],
                                                     'functions': []}

                        # update if we don't have a description already
                        if '' == library_dict[tblName]['description']:
                            library_dict[tblName]['description'] = table_info['tbl_description']

                        libName = table_info['lib_name']

                        if libName is None and library_dict[tblName]['lib_name'] is None:
                            libName = f'lib_at_{str(idx)}'

                        library_dict[tblName]['lib_name'] = libName

                        for i in range(len(table_info['functions'])):
                            item = {'name': table_info['functions'][i], 'description': table_info['descriptions'][i]}
                            library_dict[tblName]['functions'].append(item)

                else:
                    break

    if args.output:
        with open(args.output, 'w') as f:
            #for i in library_dict:
            #    pprint(library_dict[i])
            #    print('-'*80)
            #    print(json.dumps(library_dict[i], sort_keys=True, indent=2))
            f.write(json.dumps(library_dict, sort_keys=True, indent=2))
    else:
        print(json.dumps(library_dict, sort_keys=True, indent=2))
