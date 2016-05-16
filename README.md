# deanslist-python
Simple python wrapper for the Deanslist API that flattens the json response and write a csv file.

There are two primary commands, `dl` and `dl_all`

`dl` gets submits a single request data. It takes two arguments, reports and dlkeys, with an optional start and
end date.

Reports expects a list of dicts of the form:
`{'outname': <the name of the report you are getting>, 'reporturl': <the url of the Deanslist request>}`

`outname` can be:
* points
* coaching
* coaching_evidence
* incidents
* Or your own name for any of the other endpoints

`dl_all` gets all data between two dates, submitting a separate request for each date.
This is useful for transfering large amounts of data.
