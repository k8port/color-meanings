import csv

fields = []
rows = []

def read_csv(filepath):
    with open(filepath, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        fields = next(csvreader)
        for row in csvreader:
            rows.append(row)

        print("Total no. of row: %d" % (csvreader.line_num))
    
    # printing field names
    print('Field names are:' + ', '.join(field for field in fields))

    # print 3 rows
    print('\nFirst 3 rows are:\n')
    for row in rows[:3]:
        for col in row:
            print("%10s" % col, end=" ")
        print('\n')

    return fields, rows


