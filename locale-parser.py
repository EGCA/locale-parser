"""
==============================================================================
A simple parsing script

Author: Cameron Asaoka

create a excel document with [File | Function name | Locale | line number]
==============================================================================
"""

# imports
import datetime
import os
import re
import xlsxwriter
import copy
from enum import Enum

DEBUG = False


class function_Status_enum(Enum):
    NOT_WITHIN_FUNCTION = 0
    WITHIN_TOP_LEVEL_FUNCTION = 1
    DEEPER_WITHIN_CASE_LOOP = 2


class MyLocaleParser:
    """
    A class for parsing specific text from text files

    Attributes (class variables)
    ----------
    locations_ : str
    my_work_list_ : list
    """

    def __init__(self):
        # initialize locations to none
        self.locations_ = None
        # creating list
        self.my_work_list_ = []
        # creating file list
        self.my_file_list_ = []
        # initialize current function name
        self.current_function_name_ = ['NAME NOT FOUND']
        # initialize current text
        current_text_line_ = ''
        # initialize line var to one
        current_text_num_ = 1
        # initialize locale
        self.current_locale_ = ''
        # initialize function counters
        self.openCounter_ = 0
        self.closeCounter_ = 0
        # initialize outside function
        self.status_of_function_ = 0
        # Create a workbook and add a worksheet.
        # TODO ADD TRY / CATCH TO THIS
        cur_dtl = datetime.datetime.today()
        self.workbook = xlsxwriter.Workbook('{:%Y%m%d_%H%M%S}_Locale_Report.xlsx'.format(cur_dtl))
        self.worksheet = self.workbook.add_worksheet()
        # Write some data headers.
        bold = self.workbook.add_format({'bold': True})
        self.worksheet.write('A1', 'Name of File', bold)
        self.worksheet.write('B1', 'Function Name', bold)
        self.worksheet.write('C1', 'Locale', bold)
        self.worksheet.write('D1', 'Line Number', bold)
        self.worksheet.write('E1', 'Path', bold)
        self.worksheet.set_column(0, 0, 35)
        self.worksheet.set_column(1, 1, 20)
        self.worksheet.set_column(2, 3, 15)
        self.worksheet.set_column(4, 4, 55)

        self.rows = 1
        self.cols = 4
        # initialize line var back to one every iteration
        self.current_text_num_ = 1
        self.my_path_list_ = []

    # Request the location of the base folder (gui)
    def request_for_location(self):
        self.locations_ = input("Type a container folder to search for locales: ")

    # Take location, search for .txt files
    def search_for_txt_files(self):
        """
        :parameter (local variable)
        -----------
        i : int
        os.walk -> returns a 3-tuple (variable container holding 3 items)
        root : str
        dirs : str
        files : str
        """
        # initialize index to start of array
        i = 0
        # setting interested extension as .txt
        regex = re.compile('(.*cpp$)')

        # search through directory using os.walk
        for root, dirs, files in os.walk(self.locations_):
            for file in files:
                # file matched a text file
                if regex.match(file):
                    # must not assign file to list, need to 'append'
                    self.my_work_list_.append(f'{root}\{file}')  # python3 syntax
                    # python2 equivalent: self.my_work_list_.append('{}\{}'.format(root, file))

                    # append file names to list
                    self.my_file_list_.append(f'{file}')
                    if DEBUG:
                        print(self.my_work_list_[i], '| i =', i)
                    # increment the array
                    i += 1  # equivalent to i = i + 1

    # Take my_work_list_ and iterate across each file. See if specific text exists
    def process_text_in_list(self):
        print('MY PROGRESS: [', end='')
        self.my_path_list_ = copy.deepcopy(self.my_work_list_)
        if DEBUG:
            print('NUM OF FILES = ', len(self.my_work_list_))
        for i in range(0, len(self.my_work_list_)):
            if DEBUG:
                print(self.my_work_list_[i])

            # open file as read-only since we only care about that
            current_file = open(self.my_work_list_[i], "r")

            # initialize line var back to one every iteration
            self.current_text_num_ = 1

            # read the current line
            current_text_line_ = current_file.readline()
            while current_text_line_:
                # ============= WORK STARTS HERE ======================
                current_text_length = len(current_text_line_)

                # check for function opening {curly} bracket
                function_status = MyLocaleParser.check_curly_bracket(self, current_text_line_)

                # check the previous runs function status
                if function_status == function_Status_enum.NOT_WITHIN_FUNCTION:
                    MyLocaleParser.reset_variables(self)

                # if self.status_of_function_ == 0:
                #     # call reset variables
                #     MyLocaleParser.resetCurrentVariables(self, current_text_line_)

                # check for function name - return true/false

                status_of_name = MyLocaleParser.check_for_function_name(self, current_text_line_)

                # only call check_for_function_name if were not in a function
                if function_status != function_Status_enum.NOT_WITHIN_FUNCTION:
                    # check for locale
                    status_of_locale = MyLocaleParser.check_for_locale(self, current_text_line_)

                    if status_of_locale:
                        # store file | function name | locale | line number
                        MyLocaleParser.store_excel_data(self, status_of_locale)

                    if not status_of_locale:
                        status_of_locale_instrumentation = MyLocaleParser.check_for_instrumentation_call(self, current_text_line_)
                        if status_of_locale_instrumentation:
                            MyLocaleParser.store_excel_data(self, status_of_locale)

                if DEBUG:
                    print('Current line = ', self.current_text_num_)
                    print(current_text_line_)

                # ============= WORK ENDS HERE ========================

                # Re-read and increase line number
                current_text_line_ = current_file.readline()
                self.current_text_num_ += 1

            # close file
            current_file.close()
            self.my_file_list_.pop(0)
            self.my_path_list_.pop(0)
            # TODO IMPLEMENT PROGRESS BAR
            # MyLocaleParser.progress_bar(self)
            print('X', end='')
        # close excel sheet
        self.workbook.close()
        print(']', end='')

        # set done
        done_ = True

    # check for function name
    def check_for_function_name(self, current_text_line_):
        if current_text_line_ == '\n':
            current_text_line_ = "LINE EMPTY\n"
        substring = '::'
        count = current_text_line_.count(substring)
        current_text_line_ = current_text_line_.split("::")
        check = False
        # check for function name
        if count == 1:
            # class and method found
            current_text_line_.pop(0)
            str_without_newline = []
            for sub in current_text_line_:
                str_without_newline.append(re.sub('\n', '', sub))
                if DEBUG:
                    print(str(str_without_newline))
                self.current_function_name_ = str_without_newline
            check = True
            return check
        elif count == 2:
            # class, class, method
            current_text_line_.pop(0)  # Loop through count vs. copy and paste
            current_text_line_.pop(0)
            str_without_newline = []
            for sub in current_text_line_:
                str_without_newline.append(re.sub('\n', '', sub))
                if DEBUG:
                    print(str(str_without_newline))
                self.current_function_name_ = str_without_newline
            check = True
            return check
        return check

    def check_for_locale(self, current_text_line_):  # case still valid but not for the actual function call
        substring = 'locale'
        count = current_text_line_.count(substring)
        check = False
        if count == 1:
            # locale found
            current_text_line_ = current_text_line_.split("= ")

            # parse for just locale
            current_text_line_.pop(0)
            str_without_newline = []
            str_without_semiColn = []
            for sub in current_text_line_:
                str_without_newline.append(re.sub('\n', '', sub))
            for sub in str_without_newline:
                str_without_semiColn.append(re.sub(';', '', sub))
            if DEBUG:
                print(str(str_without_semiColn))
            self.current_locale_ = str_without_semiColn
            check = True
            return check  # use for next function
        return check

    def check_curly_bracket(self, current_text_line_):
        substring = '{'
        self.openCounter_ = current_text_line_.count(substring)
        substring = '}'
        self.closeCounter_ = current_text_line_.count(substring)

        # self.status_of_function_=0 not within a function
        # self.status_of_function_=1 within function top level
        # self.status_of_function_>1 within conditional statement or loop
        if self.openCounter_ == 1:
            self.status_of_function_ += 1  # increase status
        if self.closeCounter_ == 1:
            self.status_of_function_ -= 1  # decrease status
        if self.status_of_function_ == 0:
            return function_Status_enum.NOT_WITHIN_FUNCTION
        elif self.status_of_function_ == 1:
            return function_Status_enum.WITHIN_TOP_LEVEL_FUNCTION
        elif self.status_of_function_ > 1:
            return function_Status_enum.DEEPER_WITHIN_CASE_LOOP

    def store_excel_data(self, status_of_locale):
        # store file | function name | locale | line number
        self.worksheet.write(self.rows, 0, self.my_file_list_[0])
        self.worksheet.write(self.rows, 1, self.current_function_name_[0])
        if status_of_locale:
            self.worksheet.write(self.rows, 2, self.current_locale_[0])
        else:
            self.worksheet.write(self.rows, 2, self.current_locale_)
        self.worksheet.write(self.rows, 3, self.current_text_num_)
        self.worksheet.write(self.rows, 4, self.my_path_list_[0])
        self.rows += 1

    def check_for_instrumentation_call(self, current_text_line_):
        substring = '0xB'
        count = current_text_line_.count(substring)
        check = False
        if count == 1:
            # locale found
            current_text_line_ = current_text_line_.split(",")

            # parse for just locale
            i = 0
            length = len(current_text_line_)
            while i < length:
                count = current_text_line_[0].count(substring)
                if count < 1:
                    current_text_line_.pop(0)
                else:
                    currentlength = len(current_text_line_)
                    if currentlength > 1:
                        current_text_line_.pop(1)
                i += 1
            str_without_newline = []
            str_without_semiColn = []
            for sub in current_text_line_:
                str_without_newline.append(re.sub('\n', '', sub))
            for sub in str_without_newline:
                str_without_semiColn.append(re.sub(';', '', sub))
            str_without_semiColn_space = str_without_semiColn[0].replace(" ", "")
            if DEBUG:
                print(str(str_without_semiColn_space))
            self.current_locale_ = str_without_semiColn_space
            check = True
            return check  # use for next function
        return check
    def reset_variables(self):
        self.current_function_name_[0] = 'NAME NOT FOUND'

    # TODO IMPLEMENT PROGRESS BAR
    # def progress_bar


def main():
    # step 1. instantiate LocaleParser class
    main_parser = MyLocaleParser()

    # step 2. Request Location from User
    main_parser.request_for_location()

    # step 3. Take location, search for source files
    main_parser.search_for_txt_files()

    # step 4. Open file in my_work_list_ and parse with saving what lines its on and if
    #         finds a locale then store in array
    main_parser.process_text_in_list()


if __name__ == '__main__':
    main()

# C++
# class Person:
#     int name;
#     int age;
#
#     void print_name() {
#         int x;
#         std::cout << "Name is " << this->name << std::endl;
#     }

# x = 3

# python3
# class Person:
#     def __init__(self, name: str):
#         self.title = name
#
#     def print_name(self):
#         print(f"Name is {self.title}")


# cameron = Person("Cameron")

# for i, walk in enumerate(os.walk(self.locations_)):
#     root, dirs, files = walk
#     pass
