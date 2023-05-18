
# this is for an attempted performance gain on the pico - which was taking too long
# to read a full year of data. however, the resulting files - seem to take up a mb,
# whereas the original file is only 400kb. and that mb is too much for the pico.

def save_current_lines(day, lines):
    titles = 'date,time,usage'
    if day == None:
        return
    if len(lines) == 0:
        return
    with open('days/{}.csv'.format(day), 'w') as output:
        output.write('{}\n'.format(titles))
        for line in lines:
            parts = line.split(',')
            output.write('{},{},{}\n'.format(parts[1],parts[2],parts[4]))

with open('home-2022.csv') as input:
    lines = input.readlines()
    data_lines = lines[1:]
    current_day = None
    current_days_lines = []
    for line in data_lines:
        parts = line.split(',')
        if parts[1] != current_day:
            save_current_lines(current_day, current_days_lines)
            current_day = parts[1]
            current_days_lines = []
            current_days_lines.append(line)
        else:
            current_days_lines.append(line)
    save_current_lines(current_day, current_days_lines)