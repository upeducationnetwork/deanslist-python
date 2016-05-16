# deanslist-python
Simple python wrapper for the Deanslist API that flattens the json response and writes a csv file to the current directory.

Note that I don't think the API is very clear right now, so future versions may break the API.

There are two primary commands, `dl` and `dlall`

`dl` gets submits a single request for each report. It has two required arguments, reports and dlkeys, and an optional pulldate and
enddate. Finally, there is a rewrite option which can be 'a' or 'w'. If 'a', it will append the results to an existing file instead of re-writing the file.

Reports expects a list of dicts of the form:

{'outname': 'the name of the report you are getting',
 'reporturl': 'the url of the Deanslist request'}

'outname' can be:
* points
* coaching
* coaching_evidence
* incidents
* Or your own name for any of the other endpoints

dlkeys is a list of API keys. A separate request will be made for each key in the list, and the results are appended together.

Example:
```
reports = [
    {'outname': 'communications', 'reporturl': baseurl + 'beta/export/get-comm-data.php'},
    {'outname': 'users', 'reporturl': baseurl + 'beta/export/get-users.php'},
    {'outname': 'students', 'reporturl': baseurl + 'beta/export/get-students.php'},
    {'outname': 'rosters', 'reporturl':  baseurl + 'beta/export/get-roster-assignments.php'},
    {'outname': 'terms', 'reporturl':  baseurl + 'v1/terms'},
    {'outname': 'incidents', 'reporturl':  baseurl + 'v1/incidents'}
    {'outname': 'homework', 'reporturl': 'beta/export/get-homework-data.php', 'rewrite': 'a',
       'pulldate': datetime.date.today().strftime('%Y-%m-%d')}]

deanslist.dl(reports, dlkeys)

```

`dlall` gets all data between two dates, submitting a separate request for each date.
This is useful for transferring large amounts of data.
