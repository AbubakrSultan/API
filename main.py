import requests
import json
from collections import OrderedDict
from operator import getitem

# fetch data from api

offset = 0
page_size = 1000
data = []
limit = page_size + 1

while offset < limit:
    api_endpoint = f"https://open.canada.ca/data/api/action/package_search?start={offset}&rows={page_size}"
    request = requests.get(api_endpoint)

    json_result = json.loads(request.content)
    data += json_result["result"]["results"]
    offset += page_size
    limit = json_result["result"]["count"] + 10
    print(f"Fetching data .... {str(offset)}")

# generate a dict of structure
# result = {
#   "creator": {
#                "number_of_packages": n,
#                "jurisdiction",
#                "packages": [ list of package ids] 
#              }
#          }
result = {}
for package in data:
    if package["jurisdiction"] == "municipal":
      try:
          contact = json.loads(package["contact_information"])
          org_name = contact["en"]["organization_name"]
      except KeyError:
          org_name = package["creator"]

    else:
      org_name = package["organization"]["title"]

    if org_name not in result.keys():
        result[org_name] = {"packages": [package["id"]]}
    else:
        result[org_name]["packages"].append(package["id"])
    result[org_name]["jurisdiction"] = package["jurisdiction"]

for row in result:
    result[row]["number_of_packages"] = len(result[row]["packages"])

# sort results in decending order for number_of_packages
sorted_result = OrderedDict(sorted(result.items(), key = lambda x: getitem(x[1], "number_of_packages"), reverse=True))

# generate html tags for table rows with a list of urls of packages inside a details/summary tag
row = ""
url = "https://open.canada.ca/data/en/dataset/"

keys = sorted_result.keys()
for key in keys:
    list = "<ol>"
    for id in sorted_result[key]["packages"]:
        list += f"<li><a href='{url}{id}' target='_blank'>{url}{id}</a></li>"
    list += "</ol>"
    row += f"""<tr valign='top'>
                 <td><details><summary>{key}</summary><p>{list}</p></details></td>
                 <td>{sorted_result[key]['jurisdiction']}</td>
                 <td>{sorted_result[key]['number_of_packages']}</td>
               </tr>"""

# generate html for the report webpage
script = "<script class='init'>$(document).ready(function () {$('#example').DataTable({paging: false, ordering: false, info: false});});</script>"
html_code = f"""
<!DOCTYPE html>
<html>
<head>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-rbsA2VBKQhggwzxH7pPCaAqO46MgnOM80zW1RWuH61DGLwZJEdK2Kadq2F9CUG65" crossorigin="anonymous"">
  <link href="https://cdn.datatables.net/1.13.1/css/jquery.dataTables.min.css">
  <script src="https://code.jquery.com/jquery-3.5.1.js"></script>
  <script src="https://cdn.datatables.net/1.13.1/js/jquery.dataTables.min.js"></script>
  {script}
</head>
<body>
<h1>Report</h1>
<h2>A total of {json_result["result"]["count"]} results.</h2>
<title>Report</title>
<table id="example" class="table table-hover" style="width:100%">
  <thead>
  <tr>
    <th>Organization</th>
    <th>Jurisdiction</th>
    <th>Number of packages</th>
  </tr>
  </thead>
  <tbody>
    {row}
  </tbody>
</table>
</body>
</html>
"""

# write html code to file
file = open("index.html", "w")
file.write(html_code)
