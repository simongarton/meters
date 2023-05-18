
# a year of mercury data - 30 minutes - expands to about 400kb if done with month files,
# or a mb with days - which is too much for the pico. by month, it is working well.

def save_current_lines(month, lines):
    titles = 'date,time,usage'
    if month == None:
        return
    if len(lines) == 0:
        return
    with open('months/{}.csv'.format(month), 'w') as output:
        output.write('{}\n'.format(titles))
        for line in lines:
            parts = line.split(',')
            output.write('{},{},{}\n'.format(parts[1],parts[2],parts[4]))

with open('home-2022.csv') as input:
    lines = input.readlines()
    data_lines = lines[1:]
    current_month = None
    current_months_lines = []
    for line in data_lines:
        parts = line.split(',')
        if parts[1][:7] != current_month:
            save_current_lines(current_month, current_months_lines)
            current_month = parts[1][:7]
            current_months_lines = []
            current_months_lines.append(line)
        else:
            current_months_lines.append(line)
    save_current_lines(current_month, current_months_lines)