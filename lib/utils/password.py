# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#

import lib.constants as c
from lib.tools import Tools

if __name__ == '__main__':

    def print_menu():
        print 30 * "-", "Password Util", 30 * "-"
        print "1. Create Master Key"
        print "2. Generate Device SSH Password"
        print "3. Generate Junos Space REST Api Password"
        print "4. Generate OSSH Shared Secret"
        print "5. Generate AMQP Password"
        print "6. Exit"
        print 75 * "-"

    loop = True

    while loop:
        print_menu()
        choice = input("Enter your choice [1-6]: ")

        if choice == 1:
            print "Creating Master key..."
            Tools.create_master_key()
        elif choice == 2:
            print 'Generating Device SSH password'
            Tools.create_password(c.YAPT_PASSWORD_TYPE_DEVICE)
        elif choice == 3:
            print "Generating Junos Space REST Api Password"
            Tools.create_password(c.YAPT_PASSWORD_TYPE_SPACE)
        elif choice == 4:
            print "Generating OSSH Shared Secret"
            Tools.create_password(c.YAPT_PASSWORD_TYPE_OSSH)
        elif choice == 5:
            print "Generating AMQP Client Password"
            Tools.create_password(c.YAPT_PASSWORD_TYPE_AMQP)
        elif choice == 6:
            print "Bye"
            loop = False
        else:
            raw_input("Wrong option selection. Enter any key to try again..")
