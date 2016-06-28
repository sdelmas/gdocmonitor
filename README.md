## Synopsis

    gdocmonitor.py [-h] [--config CONFIG] [--frommail address] [--tomail address] [--smtphost hostname] [--smtpport port] [--usessl] [--username mailuser] [--psasword password] [--interval minutes] [--update] [--queries query] [--verbose]

## Thanks

This code is based upon the gitdriver code that can be found
here https://github.com/larsks/gitdriver

## Requirements
- python2
- pip install pyyaml
- pip install requests
- pip install pyslack-real

## Options

- `--config CONFIG`, `-f CONFIG` -- Path to configuration file
- `--frommail address`, `-f` -- From mail address
- `--tomail address`, `-t` -- To mail address, repeat option for multiple addresses
- `--smtphost`, `-s` -- SMTP host name
- `--smtpport`, `-o` -- SMTP port number
- `--usessl`, `-l` -- Use SSL for SMTP
- `--username`, `-e` -- SMTP user name
- `--password`, `-p` -- SMTP user password
- `--interval`, `-i` -- Repeat scan in <interval> minutes
- `--update`, `-u` -- Update the list of monitored documents and modification dates
- `--queries`, `-q` -- Queries to run in google drive, repeat option for multiple queries
- '--slackroom', '-r' -- Slack room to use
- '--slacktoken', '-g' -- Slack token to use (https://api.slack.com/web)
- '--slackuser', '-j' -- Slack user name to use
- `--verbose`, `-v` -- Verbose output

Note that the gd.conf file is a Yaml file (example included) that allows you
to set all these options. The names are a direct match.

## Example usage:

    $ python gdocmonitor.py --interval 2

## Google setup

You will need to create an OAuth client id and secret for use with
this application, the Drive API [Python quickstart][] has links to the
necessary steps.

[python quickstart]: https://developers.google.com/drive/v3/web/quickstart/python

- Create a Project
- Set the app name on the Oauth consent screen (the one to the right)
- Add an OAuth client ID (I use gdocmonitor as name)
- copy the client ID and client secret in your gd.conf (see below)

## Configuration

In order to make this go you will need to create file named `gd.conf`
where the code can find it (typically the directory in which you're
running the code, but you can also use the `-f` command line option to
specify an alternate location).

The file is a simple YAML document that should look like this:

    googledrive:
      client id: YOUR_CLIENT_ID
      client secret: YOUR_CLIENT_SECRET

Where `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` are replaced with the
appropriate values from Google that you established in the previous
step.

Additional options in gd.conf match the commandline options. You will want
to uncomment the mail options to enable mail sending. Use the interval
option set to something besides 0 to run the program in daemon mode, which 
will scan for changes indefinitively (waiting for <interval> minutes
between scans.

Set --update to make the locally created modification tracking file
be updated. If you don't do this, the next scan will continue to
report the files from prior scans.

You can define any number of queries to be performed to identify
files to monitor. These are standard google docs queries, see the
gd.conf file for examples. Each query can only return 1000 files,
so if you want to monitor more, you will need to define multiple
smaller queries (this is a Google API limitation).

## Troubleshooting

If you get: smtplib.SMTPAuthenticationError: (534... when using gmail
you need to enable less secure access at https://www.google.com/settings/u/1/security/lesssecureapps

Remember, only 1000 docs per query, so if you get a warning about having
to many files returned it's time to break up the query.
