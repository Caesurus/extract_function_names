#!/usr/bin/env python3
import argparse
import json
import re
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
        self.SEARCH_BACKWARD_RANGE = 6

        self.regex_libname = r'.*\s(?P<lib_name>\w+Lib)'
        self.regex_function = r'^(?P<function_name>\w+)\(\s*\)\s*(?P<description>.*)'
        self.regex_page_number = r'^\d+$'

    def parse(self, text_chunk):
        self.text = text_chunk.split('\n')
        for i in range(len(self.text)):
            self.text[i] = self.text[i].strip()

    def find_next_table_idx(self):
        try:
            for i in range(self.idx, len(self.text)):
                line = self.text[i]
                if line.startswith('Table'):
                    return i
        except:
            print('boo')
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
            description = m.groupdict()['description']
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
        table_info = {'tbl_name': self.text[self.idx]}

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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='parse text pdf output for symbols')
    parser.add_argument('-f', '--files', required=True, nargs='+', help='pass file/files to analyze')
    parser.add_argument('-o', '--output', help='json file to output to')

    args = parser.parse_args()
    tbls=[]

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
                    if table_info['lib_name']:
                        tbls.append(table_info)
                else:
                    break

    if args.output:
        with open(args.output, 'w') as f:
            f.write(json.dumps(tbls, sort_keys=True, indent=2))
    else:
        print(json.dumps(tbls, sort_keys=True, indent=2))
