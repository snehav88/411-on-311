import numpy as np
import csv
import datetime
import pickle as pkl

month_number = {
    'Jan': 1,
    'Feb': 2,
    'Mar': 3,
    'Apr': 4,
    'May': 5,
    'Jun': 6,
    'Jul': 7,
    'Aug': 8,
    'Sep': 9,
    'Oct': 10,
    'Nov': 11,
    'Dec': 12
}

def create_data_structures():
    """ Create data structures to optimize the search """
    # Read in crime csv file
    crime_r = csv.reader(open('../data/Crimes_-_Feb_15__2012_to_August_6__2013_-_Outdoor.csv',
        'r'))
    # Create a dictionary to store a hash table of crimes indexed by date
    # (Each date will have a list of crimes)
    fields = crime_r.next()
    print fields
    crimes_by_date = {'fields': fields, 'data':{}}
    # For each row, extract the date, and store the record (as list) in the
    # 'data' part of the dictionary
    i = 0
    for row in crime_r:
        date_s = row[2].split(' ')[0]
        mdy = date_s.split('/')
        date = datetime.date(int(mdy[2]), int(mdy[0]), int(mdy[1]))
        if date in crimes_by_date['data'].keys():
            crimes_by_date['data'][date].append(row)
        else:
            crimes_by_date['data'][date] = [row]
        if i%10000 == 0:
            print i
        i += 1
    return crimes_by_date
    pkl.dump(crimes_by_date, open('../data/crimes_by_date.pkl', 'wb'))


def count_lights_out_and_crimes(outage_type='alley', cbd=None):
    """ Count crimes happening before, furing, and after outages """
    # Open the light outage file
    if outage_type == 'alley':
        outage_fn = 'alley_lights_out.csv'
    elif outage_type == 'street-one':
        outage_fn = 'street-lights-one-out.csv'
    elif outage_type == 'street-all':
        outage_fn = 'street-lights-all-out.csv'
    outage_r = csv.reader(open('../data/' + outage_fn, 'r'))
    fields = outage_r.next()
    print fields
    if cbd == None:
        cbd = create_data_structures()
    
    # Open output CSV file
    out_csv = open('../data/lights_and_crimes_' + outage_type + '.csv', 'w')
    
    #crime_types = set()
    #for r in cbd['data'].items():
        #print set([v[5] for v in r[1]])
        #crime_types = crime_types.union(set([v[5] for v in r[1]]))
    crime_types = ['THEFT', 'NARCOTICS', 'BATTERY', 'CRIMINAL DAMAGE'] +\
        ['MOTOR VEHICLE THEFT', 'ROBBERY', 'ASSAULT', 'BURGLARY', 'HOMICIDE']
    
    # Cycle over outages, and build the required data structure
    header = ','.join(map(str, fields))
    header += ',DateCreated,DateCompleted,OutageDuration,After.Period.Duration,'
    header_offset = len(header)
    for t in crime_types:
        # Crime type in lowercase (but the initial)
        t_list = [v.capitalize() for v in t.split(' ')]
        t_str = str(t_list).strip('[]')\
            .replace(' ','').replace(',','').replace('\'','')
        header += t_str + '.During,'
        header += t_str + '.Before,'
        header += t_str + '.After,'
    header += 'Crimes.Alley.During,Crimes.Alley.Before,Crimes.Alley.After,'
    header += 'Crimes.All.During,Crimes.All.Before,Crimes.All.After,'
    header += 'DeceptivePractice.During,DeceptivePractice.Before,DeceptivePractice.After\n'
    out_csv.write(header)
    # Place in the data structure where the triple associated to a particular crime is
    # located (for filling in the data)
    # Starts from 0
    print header
    crime_type_idx = dict((t, crime_types.index(t)*3) for t in crime_types)
    alley_index = 3 * len(crime_types)
    all_index = alley_index + 3
    dec_index = all_index + 3
    print crime_type_idx

    j = 0
    for row in outage_r:
        # String (row in the csv file)
        s = str(row).strip('[]')
        # Extract the dates
        dmy = row[2].split('-')
        cr_date  = datetime.date(2000+int(dmy[2]), int(month_number[dmy[1]]),
            int(dmy[0]))
        dmy = row[3].split('-')
        co_date  = datetime.date(2000+int(dmy[2]), int(month_number[dmy[1]]),
            int(dmy[0]))
        if co_date > datetime.date(2013, 7, 15):
            continue

        s += ',' + str(cr_date) + ',' + str(co_date) + ','
        
        # List storing counts
        counts = [0] * (3*len(crime_types) + 9)
        during_window = (cr_date, co_date)
        before_window = (max(datetime.date(2012, 2, 15), cr_date-datetime.timedelta(37)),
            cr_date-datetime.timedelta(7))
        after_window = (co_date + datetime.timedelta(7),
            min(datetime.date(2013, 7, 30), co_date + datetime.timedelta(37)))
        
        s += str((during_window[1]-during_window[0]).days+1) + ','
        s += str((after_window[1]-after_window[0]).days) + ','
        outage_x = float(row[6])
        outage_y = float(row[7])
        # Now, look at crimes committed in the "during", "before", and "after"
        # window 
        
        # DURING
        d = during_window[0]
        while d <= during_window[1]:
            # Look at crimes happening that day
            for c in cbd['data'][d]:
            #for c in cbd['data'][d]:
                # Retrieve the crime type
                t = c[5]
                if (t in crime_types or t == 'DECEPTIVE PRACTICE')\
                    and c[15] != '' and c[16] != '':
                    # See if the crime happens within 500 foot radius from
                    # outage
                    crime_x = float(c[15])
                    crime_y = float(c[16])
                    if np.sqrt((crime_x-outage_x)**2 + (crime_y-outage_y)**2) < 500:
                        if t == 'DECEPTIVE PRACTICE':
                            counts[dec_index] += 1
                        else:
                            counts[all_index] += 1
                            counts[crime_type_idx[t]] += 1
                            # Check if the location is an alley
                            if c[7] == 'ALLEY':
                                counts[alley_index] += 1
            d += datetime.timedelta(1)
        
        # BEFORE
        d = before_window[0]
        while d < before_window[1]:
            # Look at crimes happening that day
            for c in cbd['data'][d]:
                # Retrieve the crime type
                t = c[5]
                if (t in crime_types or t == 'DECEPTIVE PRACTICE')\
                    and c[15] != '' and c[16] != '':
                    # See if the crime happens within 500 foot radius from
                    # outage
                    crime_x = float(c[15])
                    crime_y = float(c[16])
                    if np.sqrt((crime_x-outage_x)**2 + (crime_y-outage_y)**2) < 500:
                        if t == 'DECEPTIVE PRACTICE':
                            counts[dec_index+1] += 1
                        else:
                            counts[all_index+1] += 1
                            counts[crime_type_idx[t]+1] += 1
                            # Check if the location is an alley
                            if c[7] == 'ALLEY':
                                counts[alley_index+1] += 1
            d += datetime.timedelta(1)
        
        # AFTER
        d = after_window[0] + datetime.timedelta(1)
        while d <= after_window[1]:
            # Look at crimes happening that day
            for c in cbd['data'][d]:
                # Retrieve the crime type
                t = c[5]
                if (t in crime_types or t == 'DECEPTIVE PRACTICE')\
                    and c[15] != '' and c[16] != '':
                    # See if the crime happens within 500 foot radius from
                    # outage
                    crime_x = float(c[15])
                    crime_y = float(c[16])
                    if np.sqrt((crime_x-outage_x)**2 + (crime_y-outage_y)**2) < 500:
                        if t == 'DECEPTIVE PRACTICE':
                            counts[dec_index+2] += 1
                        else:
                            counts[all_index+2] += 1
                            counts[crime_type_idx[t]+2] += 1
                            # Check if the location is an alley
                            if c[7] == 'ALLEY':
                                counts[alley_index+2] += 1
            d += datetime.timedelta(1)
        s += str(counts).strip('[]') + '\n'
        out_csv.write(s)
        j += 1
        if j%10 == 0:
            print j
        #if j > 10:
        #    break
    out_csv.close()
