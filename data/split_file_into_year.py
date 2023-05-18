
# take the original mercury file - which has had the first 5 lines of metadata removed -
# and write out a smaller file, skipping unneeded columns.

def save_current_lines(year, lines):
    titles = 'date,time,usage'
    if year == None:
        return
    if len(lines) == 0:
        return
    with open('years/{}.csv'.format(year), 'w') as output:
        output.write('{}\n'.format(titles))
        for line in lines:
            parts = line.split(',')
            output.write('{},{},{}\n'.format(parts[1],parts[2],parts[4]))

with open('home-2022.csv') as input:
    lines = input.readlines()
    data_lines = lines[1:]
    current_year = None
    current_years_lines = []
    for line in data_lines:
        parts = line.split(',')
        if parts[1][:4] != current_year:
            save_current_lines(current_year, current_years_lines)
            current_year = parts[1][:4]
            current_years_lines = []
            current_years_lines.append(line)
        else:
            current_years_lines.append(line)
    save_current_lines(current_year, current_years_lines)