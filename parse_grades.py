from bs4 import BeautifulSoup
def parse_grades(html):
    soup = BeautifulSoup(html, 'html.parser')
    assignment_tables = soup.select('div.AssignmentClass table[id^="plnMain_rptAssigmnetsByCourse_dgCourseAssignments_"]')
    grades = []
    for table in assignment_tables:
        rows = table.select('tbody tr.sg-asp-table-data-row')
        for row in rows:
            columns = row.find_all('td')
            if columns:
                assignment_info = {
                    'date': columns[0].get_text(strip=True),
                    'assignment': columns[2].get_text(strip=True),
                    'category': columns[3].get_text(strip=True),
                    'score': columns[4].get_text(strip=True),
                    'total': columns[5].get_text(strip=True),
                    'percentage': columns[6].get_text(strip=True),
                }
                grades.append(assignment_info)
    print("[LOG] Grades parsed")
    return(grades)

