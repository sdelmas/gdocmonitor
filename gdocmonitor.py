#!/usr/bin/python

import os
import sys
import argparse
import yaml
import smtplib
import time

from drive import GoogleDrive, DRIVE_RW_SCOPE
from email.mime.text import MIMEText
from pyslack import SlackClient

# Load the file list with last dates
from myfilelist import *

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--config', '-c', default='gd.conf', help="Path to configuration file")
    p.add_argument('--frommail', '-f', default='', help="From mail address")
    p.add_argument('--tomail', '-t', action='append', help="To mail address, repeat option for multiple addresses")
    p.add_argument('--smtphost', '-s', default='smtp.gmail.com', help="SMTP host name")
    p.add_argument('--smtpport', '-o', default=587, type=int, help="SMTP port number")
    p.add_argument('--usessl', '-l', action='store_true', help="Use SSL for SMTP")
    p.add_argument('--username', '-e', default='', help="SMTP user name")
    p.add_argument('--password', '-p', default='', help="SMTP user password")
    p.add_argument('--interval', '-i', default=0, type=int, help="Repeat scan in <interval> minutes")
    p.add_argument('--update', '-u', action='store_true', help="Update the list of monitored documents and modification dates")
    p.add_argument('--queries', '-q', help="Queries to run in google drive, repeat option for multiple queries")
    p.add_argument('--slackroom', '-r', default='', help="Slack room to use")
    p.add_argument('--slacktoken', '-g', default='', help="Slack token to use (https://api.slack.com/web)")
    p.add_argument('--slackuser', '-j', default='', help="Slack user name to use")
    p.add_argument('--verbose', '-v', action='store_true', help="Verbose output")

    return p.parse_args()

def main():
    opts = parse_args()
    cfg = yaml.load(open(opts.config))

    # match Yaml options to commandline options
    try:
        if cfg['mail']['frommail'] != "":
            opts.frommail = cfg['mail']['frommail']
    except:
        pass
    try:
        if cfg['mail']['tomail'] != "":
            opts.tomail = cfg['mail']['tomail']
    except:
        pass
    try:
        if cfg['mail']['smtphost'] != "":
            opts.smtphost = cfg['mail']['smtphost']
    except:
        pass
    try:
        if cfg['mail']['smtpport'] != "":
            opts.smtpport = int(cfg['mail']['smtpport'])
    except:
        pass
    try:
        if cfg['mail']['usessl'] != "":
            opts.usessl = bool(cfg['mail']['usessl'])
    except:
        pass
    try:
        if cfg['mail']['username'] != "":
            opts.username = cfg['mail']['username']
    except:
        pass
    try:
        if cfg['mail']['password'] != "":
            opts.password = cfg['mail']['password']
    except:
        pass
    try:
        if cfg['interval'] != "":
            opts.interval = int(cfg['interval'])
    except:
        pass
    try:
        if cfg['update'] != "":
            opts.update = bool(cfg['update'])
    except:
        pass
    try:
        if cfg['queries'] != "":
            opts.queries = cfg['queries']
    except:
        pass
    try:
        if cfg['slackroom'] != "":
            opts.slackroom = cfg['slackroom']
    except:
        pass
    try:
        if cfg['slacktoken'] != "":
            opts.slacktoken = cfg['slacktoken']
    except:
        pass
    try:
        if cfg['slackuser'] != "":
            opts.slackuser = cfg['slackuser']
    except:
        pass
    try:
        if cfg['verbose'] != "":
            opts.verbose = bool(cfg['verbose'])
    except:
        pass

    # print debug info
    if opts.verbose:
        print("from mail: " + opts.frommail)
        print("to mail: " + str(opts.tomail))
        print("smtp host: " + opts.smtphost)
        print("smtp port: " + str(opts.smtpport))
        print("use ssl: " + str(opts.usessl))
        print("username: " + opts.username)
        print("interval: " + str(opts.interval))
        print("update: " + str(opts.update))
        print("queries: " + str(opts.queries))
        print("slack room: " + str(opts.slackroom))
        print("slack user: " + str(opts.slackuser))
    
    gd = GoogleDrive(
            client_id=cfg['googledrive']['client_id'],
            client_secret=cfg['googledrive']['client_secret'],
            scopes=[DRIVE_RW_SCOPE],
            )

    # Establish our credentials.
    gd.authenticate()

    while True:
        # Locate relevant docs
        counter = 0
        for query in opts.queries:
            for file in gd.files_query(query):
                try:
                    docs[file['id']]
                except KeyError:
                    counter += 1
                    md = gd.get_file_metadata(file['id'])
                    if md['mimeType'] == 'application/vnd.google-apps.document':
                        print("Adding document: " + md['title'] + " (" + file['id'] + ")")
                        docs[file['id']] = None

            # Check that we are not getting too many documents
            if counter > 999:
                print("WARNING: Query returns too many documents, not tracking all docs: " + query)

        # Track if there where changes
        foundChanges = False

        # A mail message to send via mail
        mailMessageBody = ""

        # A message to be sent via slack
        slackMessageBody = ""

        # Iterate over the documents we monitor
        for doc,modifiedDate in docs.items():
            # Get information about the specified file.  This will throw
            # an exception if the file does not exist.
            md = gd.get_file_metadata(doc)

            if md['mimeType'] == 'application/vnd.google-apps.document':
                # Get some metadata for the file we track
                if modifiedDate is None:
                    modifiedDate=md['modifiedDate']
                title = md['title']
                try:
                    md['embedLink'] 
                except KeyError:
                    editLink = ""
                else:
                    editLink = md['embedLink'].replace('preview', 'edit')

                # Iterate over the revisions (from oldest to newest).
                lastRevModifiedDate=None
                for rev in gd.revisions(doc):
                    lastRevModifiedDate = rev['modifiedDate']
                if modifiedDate != lastRevModifiedDate:
                    foundChanges = True
                    if lastRevModifiedDate is None:
                        print("Need Edit access to: " + title + " (" + editLink + ")")
                        mailMessageBody += '<li><a href="' + editLink + '">' + title + ' (need edit access)</a></li>' + os.linesep
                        slackMessageBody += '<' + editLink + '|*' + title + ' (need edit access)*>' + os.linesep
                    else:
                        print("Document Change: " + title + " (" + editLink + ")")
                        mailMessageBody += '<li><a href="' + editLink + '">' + title + '</a></li>' + os.linesep
                        slackMessageBody += '<' + editLink + '|*' + title + '*>' + os.linesep
                    if lastRevModifiedDate is None:
                        docs[md['id']] = modifiedDate
                    else:
                        docs[md['id']] = lastRevModifiedDate

        # Write out the new files list and dates
        if opts.update and foundChanges:
            print("Updating file list")

            # write new file list
            f = open('myfilelist.py.new', 'w')
            f.write("docs={}\n")

            # Iterate over the documents we monitor
            for doc,modifiedDate in docs.items():
                if modifiedDate is not None:
               	    f.write('docs["' + doc + '"] = "' + modifiedDate + '"\n')
            f.close()

            # put new file in place
            os.rename('myfilelist.py.new', 'myfilelist.py')

        if opts.slackuser != "" and opts.slackroom != "" and opts.slacktoken != "" and slackMessageBody != "":
            print("Sending slack with changes")
            
            client = SlackClient(opts.slacktoken)
            client.chat_post_message("#" + opts.slackroom, ">>> The following documents have been changed since the last scan" + os.linesep + slackMessageBody, username=opts.slackuser)
            
        # Send a mail with the changes
        #
        # If you get: smtplib.SMTPAuthenticationError: (534... when using gmail
        #   you need to enable less secure access at https://www.google.com/settings/u/1/security/lesssecureapps
        #
        if opts.frommail != "" and mailMessageBody != "":
            print("Sending email with changes")

            finalMessageBody = "<html><head></head><body><ul>" + mailMessageBody + "</ul></body>"

            msg = MIMEText(finalMessageBody, 'html')
            msg['Subject'] = "The following documents have been changed since the last scan"
            msg['From'] = opts.frommail
            msg['To'] = ', '.join(opts.tomail)

            # Send the message via our own SMTP server, but don't include the
            # envelope header.
            if opts.usessl:
                s = smtplib.SMTP_SSL(opts.smtphost, opts.smtpport)
            else:
                s = smtplib.SMTP(opts.smtphost, opts.smtpport)
            s.ehlo()
            s.starttls()
            if opts.username != "":
                s.login(opts.username, opts.password)
            s.sendmail(opts.frommail, opts.tomail, msg.as_string())
            s.quit()

        # Bail out if we don't want to loop
        if opts.interval == 0:
            break
        else:
            time.sleep(opts.interval * 60)

if __name__ == '__main__':
    main()

