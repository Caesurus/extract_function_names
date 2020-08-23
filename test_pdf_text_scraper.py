import unittest


from pdf_text_scraper import PDFTextParser, TableType


class PDFTextParserTestCase(unittest.TestCase):
    def test_extract_function_name(self):
        pdf_p = PDFTextParser()
        function, desc = pdf_p._get_function_name("timer_getoverrun( ) Return the timer expiration overrun.")
        self.assertEqual('timer_getoverrun', function)
        self.assertEqual('Return the timer expiration overrun.', desc)

        function, desc = pdf_p._get_function_name("timer_getoverrun( )")
        self.assertEqual('timer_getoverrun', function)
        self.assertEqual('', desc)

    def test_process_table_at_index(self):
        pdf_p = PDFTextParser()
        pdf_p.parse(example_text_table_1)

        idx = pdf_p.find_next_table_idx()
        self.assertEqual(5, idx)
        pdf_p.idx = idx

        expected_first_table = {'descriptions': ['Get the clock resolution (CLOCK_REALTIME '
                                                 'andCLOCK_MONOTONIC).',
                                                 'Set the clock resolution.Obsolete VxWorks-specific POSIX '
                                                 'extension.',
                                                 'Get the current clock time (CLOCK_REALTIME '
                                                 'andCLOCK_MONOTONIC).',
                                                 'Set the clock to a specified time for CLOCK_REALTIME(fails '
                                                 'for CLOCK_MONOTONIC; not supported for athread CPU-time '
                                                 'clock in the kernel).'],
                                'functions': ['clock_getres',
                                              'clock_setres',
                                              'clock_gettime',
                                              'clock_settime'],
                                'lib_name': 'clockLib',
                                'tbl_name': 'Table 5-4',
                                'type': TableType.RoutinesFirst.value}
        table_info = pdf_p.process_table_at_index(idx)
        self.assertEqual(4, len(table_info['functions']))
        self.assertEqual(4, len(table_info['descriptions']))
        self.assertEqual(expected_first_table, table_info)
        self.assertEqual(33, pdf_p.idx)

        idx = pdf_p.find_next_table_idx()
        self.assertEqual(63, idx)
        pdf_p.idx = idx

        expected_second_table = {'descriptions': ['Allocate a timer using the specified clock for a timing '
                                                  'base (CLOCK_REALTIME or CLOCK_MONOTONIC).',
                                                  'Remove a previously created timer.',
                                                  'Open a named timer. VxWorks-specific POSIX extension.',
                                                  'Close a named timer. VxWorks-specific POSIX extension.',
                                                  'Get the remaining time before expiration and the reload '
                                                  'value.',
                                                  'Return the timer expiration overrun.',
                                                  'Set the time until the next expiration and arm timer.',
                                                  'Cancel a timer. VxWorks-specific POSIX extension.'],
                                 'functions': ['timer_create',
                                               'timer_delete',
                                               'timer_open',
                                               'timer_close',
                                               'timer_gettime',
                                               'timer_getoverrun',
                                               'timer_settime',
                                               'timer_cancel'],
                                 'lib_name': 'timerLib',
                                 'tbl_name': 'Table 5-5',
                                 'type': TableType.Intermingled.value}

        table_info = pdf_p.process_table_at_index(idx)
        self.assertEqual(8, len(table_info['functions']))
        self.assertEqual(8, len(table_info['descriptions']))
        self.assertEqual(expected_second_table, table_info)
        self.assertEqual(105, pdf_p.idx)

        idx = pdf_p.find_next_table_idx()
        self.assertEqual(111, idx)
        pdf_p.idx = idx

        expected_second_table_continued = {'descriptions': ['Connect a user routine to the timer signal. '
                                                            'VxWorks-specific POSIX extension.',
                                                            'Unlink a named timer. VxWorks-specific POSIX extension.',
                                                            'Suspend the current pthread (task) until the time interval '
                                                            'elapses.',
                                                            'Delay for a specified amount of time.',
                                                            'Set an alarm clock for delivery of a signal.',
                                                            'function. Nevertheless, the precision of both is the same, '
                                                            'and is'],
                                           'functions': ['timer_connect',
                                                         'timer_unlink',
                                                         'nanosleep',
                                                         'sleep',
                                                         'alarm',
                                                         'taskDelay'],
                                           'lib_name': None,
                                           'tbl_name': 'Table 5-5',
                                           'type': TableType.Intermingled.value}

        table_info = pdf_p.process_table_at_index(idx)
        self.assertEqual(6, len(table_info['functions']))
        self.assertEqual(6, len(table_info['descriptions']))
        self.assertEqual(expected_second_table_continued, table_info)
        self.assertEqual(141, pdf_p.idx)

    def test_determine_table_type(self):
        pdf_p = PDFTextParser()
        pdf_p.parse(example_text_table_1)

        idx = pdf_p.find_next_table_idx()
        self.assertEqual(5, idx)
        pdf_p.idx = idx

        table_type = pdf_p.table_type(idx)
        self.assertEqual(TableType.RoutinesFirst.value, table_type)

        pdf_p.idx += 1
        idx = pdf_p.find_next_table_idx()
        self.assertEqual(63, idx)
        pdf_p.idx = idx

        table_type = pdf_p.table_type(idx)
        self.assertEqual(TableType.Intermingled.value, table_type)

    def test_determine_table_type_not_found(self):
        pdf_p = PDFTextParser()
        pdf_p.parse(example_text_table_2)

        idx = pdf_p.find_next_table_idx()
        self.assertEqual(2, idx)
        pdf_p.idx = idx

        table_type = pdf_p.table_type(idx)
        self.assertEqual(None, table_type)

        table_info = pdf_p.process_table_at_index(idx)
        self.assertEqual(0, len(table_info['functions']))
        self.assertEqual(0, len(table_info['descriptions']))
        self.assertEqual(3, pdf_p.idx)

        idx = pdf_p.find_next_table_idx()
        self.assertEqual(None, idx)

    def test_find_next_table(self):
        pdf_p = PDFTextParser()
        pdf_p.parse(example_text_table_1)

        idx = pdf_p.find_next_table_idx()
        self.assertEqual(5, idx)
        pdf_p.idx = idx + 1

        idx = pdf_p.find_next_table_idx()
        self.assertEqual(63, idx)

    def test_parse_text(self):
        pdf_p = PDFTextParser()
        self.assertTrue(isinstance(pdf_p, PDFTextParser))

        sample_text = """A
        
        B
        
        C
        
        D"""

        pdf_p.parse(sample_text)

        self.assertTrue(['A', '', 'B', '', 'C', '', 'D'], pdf_p.text)

    def test_instance(self):
        pdf_p = PDFTextParser()
        self.assertTrue(isinstance(pdf_p, PDFTextParser))


example_text_table_1 = """See Table 5-4 for a list of the POSIX clock routines. The obsolete VxWorks-specific 
POSIX extension clock_setres( ) is provided for backwards-compatibility 
purposes. For more information about clock routines, see the API reference for 
clockLib. 

Table 5-4

POSIX Clock Routines 

Call

clock_getres( )

clock_setres( )

clock_gettime( )

clock_settime( )

Description

Get the clock resolution (CLOCK_REALTIME and 
CLOCK_MONOTONIC). 

Set the clock resolution. 
Obsolete VxWorks-specific POSIX extension.

Get the current clock time (CLOCK_REALTIME and 
CLOCK_MONOTONIC). 

Set the clock to a specified time for CLOCK_REALTIME 
(fails for CLOCK_MONOTONIC; not supported for a 
thread CPU-time clock in the kernel). 

To include the clockLib library in the system, configure VxWorks with the 
INCLUDE_POSIX_CLOCKS component. For thread CPU-time clocks, the 
INCLUDE_POSIX_PTHREAD_SCHEDULER and 
INCLUDE_POSIX_THREAD_CPUTIME components must be used as well.

260

5  POSIX Facilities
5.6  POSIX Clocks and Timers

POSIX Timers

The POSIX timer facility provides routines for tasks to signal themselves at some 
time in the future. Routines are provided to create, set, and delete a timer. 
Timers are created based on clocks. In the kernel, the CLOCK_REALTIME and 
CLOCK_MONOTONIC clocks are supported for timers. In processes, the 
CLOCK_REALTIME clock, CLOCK_MONOTONIC clock, and thread CPU-time 
clocks (including CLOCK_THREAD_CPUTIME_ID clock) are supported. 
When a timer goes off, the default signal, SIGALRM, is sent to the task. To install a 
signal handler that executes when the timer expires, use the sigaction( ) routine 
(see 4.18 Signals, p.226). 
See Table 5-5 for a list of the POSIX timer routines. The VxWorks timerLib library 
includes a set of VxWorks-specific POSIX extensions: timer_open( ), 
timer_close( ), timer_cancel( ), timer_connect( ), and timer_unlink( ). These 
routines allow for an easier and more powerful use of POSIX timers on VxWorks. 
For more information, see the VxWorks API reference for timerLib.

5

Table 5-5

POSIX Timer Routines 

Routine

Description

timer_create( )

Allocate a timer using the specified clock for a timing base 
(CLOCK_REALTIME or CLOCK_MONOTONIC).

timer_delete( )

Remove a previously created timer.

timer_open( )

timer_close( )

Open a named timer. 
VxWorks-specific POSIX extension. 

Close a named timer. 
VxWorks-specific POSIX extension. 

timer_gettime( )

Get the remaining time before expiration and the reload 
value.

timer_getoverrun( ) Return the timer expiration overrun.

timer_settime( )

Set the time until the next expiration and arm timer.

timer_cancel( )

Cancel a timer.
VxWorks-specific POSIX extension.

261

VxWorks
Kernel Programmer's Guide, 6.6 

Table 5-5

POSIX Timer Routines  (cont’d)

Routine

Description

timer_connect( )

Connect a user routine to the timer signal. 
VxWorks-specific POSIX extension. 

timer_unlink( )

Unlink a named timer. 
VxWorks-specific POSIX extension.

nanosleep( )

Suspend the current pthread (task) until the time interval 
elapses. 

sleep( )

alarm( )

Delay for a specified amount of time.

Set an alarm clock for delivery of a signal.

Example 5-1

POSIX Timers 

/* This example creates a new timer and stores it in timerid. */

/* includes */
#include <vxWorks.h>
#include <time.h>

int createTimer (void)

{
timer_t timerid;

/* create timer */
if (timer_create (CLOCK_REALTIME, NULL, &timerid) == ERROR)

{
printf ("create FAILED\n");
return (ERROR);
}

return (OK);
}

The POSIX nanosleep( ) routine provides specification of sleep or delay time in 
units of seconds and nanoseconds, in contrast to the ticks used by the VxWorks 
taskDelay( ) function. Nevertheless, the precision of both is the same, and is 
determined by the system clock rate; only the units differ. 
To include the timerLib library in a system, configure VxWorks with the 
INCLUDE_POSIX_TIMERS component. 

262

"""

example_text_table_2 = """Kernel Programmer's Guide, 6.6 

Table 5-2

POSIX Libraries

Functionality

Asynchronous I/O 

Buffer manipulation

Clock facility

Directory handling

Library

aioPxLib

bLib

clockLib

dirLib

Environment handling

C Library

File duplication

File management

I/O functions

Options handling

iosLib 

fsPxLib and ioLib 

ioLib

getopt 

POSIX message queues 

mqPxLib

POSIX semaphores

POSIX timers

POSIX threads

semPxLib

timerLib

pthreadLib

Standard I/O and some ANSI 

 C Library

Math

C Library

Memory allocation

memLib and memPartLib 

Network/Socket APIs

network libraries 

String manipulation

Trace facility

C Library

pxTraceLib 

The following sections of this chapter describe the optional POSIX API 
components that are provided in addition to the native VxWorks APIs.

256
"""


if __name__ == '__main__':
    unittest.main()
