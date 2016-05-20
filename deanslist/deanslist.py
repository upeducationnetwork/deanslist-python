__author__ = 'rknight'
import os
import csv
import logging
import datetime
from requests_futures.sessions import FuturesSession


def dl(reports, dlkeys):
    # Primary call

    # Send requests
    allreports = dlrequest(reports=reports, dlkeys=dlkeys)

    # Write results
    for outreport in allreports.keys():
        # Points and incidents require unique parsing
        if outreport == 'points':
            writepoints('points.csv', report=allreports[outreport])

        elif outreport == 'coaching':
            writecoaching('coaching.csv', report=allreports[outreport])

        elif outreport == 'coaching_evidence':
            writeevidence('coaching_evidence.csv', report=allreports[outreport])

        elif outreport == 'incidents':
            writeincidents(report=allreports[outreport])

        else:
            # Merge the schools into a single list
            dat = []
            for school in allreports[outreport]['data']:
                dat.extend(school['data'])
            writefile('{0}.csv'.format(outreport), dataset=dat, rewrite=allreports[outreport]['write'])



def dlrequest(reports, dlkeys):
    '''
        Primary function to get data for a range of dates

        Returns a dict. Structure should be:
            {'outname': {'data': [all the data for this report with one list item per school],
                         'write': whether to write or append},
             'second outname': {'data': [all the data for this report with one list item per key],
                         'write': whether to write or append},
             etc
            }
    '''

    session = FuturesSession(max_workers=10)
    allreports = {}
    futures = []

    # This is run in background once the download is completed
    def bg_call(sess, resp, outname):
        dat = resp.json()
        allreports[outname]['data'].append(dat)

    # Throw the requests at Deanslist
    for ireport in reports:
        outname = ireport['outname']

        url = ireport['reporturl']

        allreports[outname] = {'data': [], 'write': ireport.get('rewrite', 'w')}

        for dlkey in dlkeys:
            futures.append(session.get(url,
                            params={'sdt': ireport.get('pulldate', ''),
                                    'edt': ireport.get('enddate', ''),
                                    'apikey': dlkey},
                            background_callback=lambda sess, resp, outname=outname: bg_call(sess, resp, outname)))

    # Parse errors in the results
    for f in futures:
        try:
            response = f.result()
        except:
            logging.exception('No data.')
            raise
        if response.status_code != 200:
            logging.warning('Response code {0} for {1}'.format(response.status_code, response.url))
            continue

    return allreports



def dlall(outname, reporturl, startat, dlkeys, endat=''):
    # Get all data for large datasets by sending a separate request for each week of data

    one_week = datetime.timedelta(days=7)
    one_day = datetime.timedelta(days=1)

    try:
        sdt = datetime.datetime.strptime(startat, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError("Incorrect data format for startat, should be YYYY-MM-DD")

    if endat != '':
        try:
            endat = datetime.datetime.strptime(endat, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError("Incorrect data format for endat, should be YYYY-MM-DD")
    else:
        endat = datetime.date.today()

    edt = sdt + one_week

    alldat = []
    
    session = FuturesSession(max_workers=10)

    while edt < endat + one_week:

        # outname_date = outname + "/" + outname + "_Week_" + edt.strftime("%Y-%m-%d")

        dat = dlrequest_single(reporturl=reporturl, sdt=sdt, edt=edt, dlkeys=dlkeys, session=session)
        alldat.extend(dat)

        sdt = edt + one_day
        edt = edt + one_week

    # Write to hard drive
    if len(alldat) > 0:
        writefile('{0}.csv'.format(outname), dataset=alldat, rewrite='w')





def dlrequest_single(reporturl, sdt, edt, dlkeys, session = FuturesSession(max_workers=5)):
    """
        Request and write a single report for all schools for a date range
    """

    alldat = []
    futures = []
    url = reporturl

    # Throw the requests at Deanslist
    for dlkey in dlkeys:
        futures.append(session.get(url,
                        params={'sdt': sdt,
                                'edt': edt,
                                'apikey': dlkey}))

    # Parse errors in the results
    for f in futures:
        try:
            response = f.result()
        except MemoryError:
            logging.warning('Memory Error.')
        if response.status_code != 200:
            logging.warning('Response code {0} for {1}'.format(response.status_code, response.url))
            continue

        # Append results
        dat = response.json()
        alldat.extend(dat['data'])

    return alldat


def writefile(outname, dataset, headers=None, rewrite='a'):
    """
        Utility to write results to file
    """

    if len(dataset) == 0:
        logging.warning('No data for {0}'.format(outname))
        return

    # Make default headers
    if not headers:
        headers = sorted(list(dataset[0].keys()))

    # Flag to write headers if its the first time
    exists = os.path.isfile(outname)

    # Write output
    with open(outname, rewrite, encoding='utf-8') as file:
        outfile = csv.DictWriter(file, headers, lineterminator='\n')
        if not exists or rewrite == 'w':
            outfile.writeheader()
        for row in dataset:
            outfile.writerow(row)


def writepoints(outname, report):
    # Parse and write points

    points = []
    # Flatten
    for dat in report['data']:
        for row in dat['Students']:
            for item in row['Terms']:
                item['StudentID'] = row['StudentID']
                item['StudentSchoolID'] = row['StudentSchoolID']
                item['SchoolID'] = dat['SchoolID']
                try:
                    item['StartDate'] = item['StartDate']['date']
                    item['EndDate'] = item['EndDate']['date']
                except:
                    pass
                points.append(item)

    # Write
    writefile(outname, dataset=points, rewrite=report['write'])


# Parse & write the incidents module, which has a unique json structure
def writeincidents(report):

    incidents = []
    penalties = []
    actions = []
    custfields = []

    # All possible ids
    inc_id_list = ['IncidentID', 'SchoolID', 'StudentID', 'StudentFirst', 'StudentLast',
                   'StudentSchoolID', 'GradeLevelShort', 'HomeroomName', 'Infraction', 'Location', 'ReportedDetails']

    for school in report['data']:
      for idat in school['data']:

        # grab ids in this report
        inc_id = {this_id: idat[this_id] for this_id in inc_id_list}

        # Flatten
        for timefield in ['CreateTS', 'UpdateTS', 'IssueTS', 'ReviewTS', 'CloseTS', 'ReturnDate']:
            try:
                idat[timefield] = idat.pop(timefield)['date']
            except:
                idat[timefield] = ''

        # Actions
        act_list = idat.pop('Actions')
        idat['NumActions'] = len(actions)

        for iact in act_list:
            iact.update(inc_id)
            actions.append(iact)

        # Penalties
        pen_list = idat.pop('Penalties')
        idat['NumPenalties'] = len(penalties)

        for ipen in pen_list:
            ipen.update(inc_id)
            penalties.append(ipen)

        # Custom fields (not currently used)
        if 'Custom_Fields' in idat:
            cust_list = idat.pop('Custom_Fields')
            for field in cust_list:
                 if field['StringValue'] == 'Y':
                    custfields.append({'IncidentID': inc_id['IncidentID'], 'SpecialCase': field['FieldName']})

        # Incidents
        incidents.append(idat)

    # Export
    exportdict = {'incidents': incidents, 'incidents-penalties': penalties, 'incidents-actions': actions, 'incidents-custfields': custfields}
    for key in exportdict:
        writefile('{0}.csv'.format(key), dataset=exportdict[key], rewrite='w')

def writecoaching(outname, report):
    # Flatten
    coaching = []
    for school in report['data']:
        for observation in school['data']:
            for timefield in ['DebriefDate', 'ReviewDate', 'LessonDate']:
                try:
                    observation[timefield] = observation.pop(timefield)['date']
                except:
                    observation[timefield] = ''
            feedbackitems = observation.pop('FeedbackItems')
            for feedbackitem in feedbackitems:
                feedbackitem.update(observation)
                coaching.append(feedbackitem)
    writefile(outname, dataset=coaching, rewrite=report['write'])
    return coaching

def writeevidence(outname, report):
    # Flatten
    coaching = []
    for school in report['data']:
        for observation in school['data']:
            for timefield in ['EvidenceDate']:
                try:
                    observation[timefield] = observation.pop(timefield)['date']
                except:
                    observation[timefield] = ''
            coaching.append(observation)

    writefile(outname, dataset=coaching, rewrite=report['write'])
