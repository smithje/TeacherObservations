#!/usr/bin/env python
"""
This is used to parse and compare teaching observations.


Copyright (C) 2013 Jeremy Smith

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import csv
import argparse
import os.path
from collections import defaultdict, Counter
from pprint import pprint

class TeacherObservation(object):
    """
    An object which is designed to parse and interpret a teacher eval
    """
    def __init__(self, filename):
        if not os.path.exists(filename):
            raise IOError("File does not exist")
        else:
            self.filename = filename
            self.initialize_results()
    
    def initialize_results(self):
        self.categories = []
        self.times = []
        self.results = []
            
    @staticmethod    
    def parse_categories(header_broad_categories, header_observation_categories):
        """
        Parse out the categories
        The spreadsheet looks something like this:
        
        ,1. instructor doing,,,,,,,,,,,,2. Students doing,,,,,,,,,,,,,3. Engagement,,,"Comments"
        MIN,Lec,FUp,RtW,D / V,PQ,CQ,R / H ,1o1,CD ,AD,N,O,L,Ind,Prd,CG,WG ,OG ,SQ,WC,SP ,TQ ,W,AQ,O,L,M,H,
        
        Because the column headers aren't all the same in the second line, we need to make new category
        names which are actually unique.  Assume that each broad category contains only unique values.
        
        We will receive the values already broken up by the csv module.
        
        Note that we toss out any categories which don't appear in the observation categories.  This is mostly to get rid of the comments.
        
        >>> header_broad_categories = ['','1. instructor','','','','','','','','','','','','2. Students','','','','','','','','','','','','','3. Engagement','','','Comments']
        >>> header_observation_categories = ['MIN','Lec','FUp','RtW','D / V','PQ','CQ','R / H ','1o1','CD ','AD','N','O','L','Ind','Prd','CG','WG ','OG ','SQ','WC','SP ','TQ ','W','AQ','O','L','M','H','']
        >>> categories = TeacherObservation.parse_categories(header_broad_categories, header_observation_categories)
        >>> categories[0]
        ': MIN'
        >>> categories[1]
        '1. instructor: Lec'
        >>> categories[-1]
        '3. Engagement: H'
        """
        assert len(header_broad_categories) == len(header_observation_categories), "The header rows must have the same number of columns"
        broad_categories_unpacked = []
        last_category = ''
        for category in header_broad_categories:
            if category != '':
                last_category = category
            broad_categories_unpacked.append(last_category)
        categories = ['%s: %s' % (broad_categories_unpacked[ind], obs_cat) for ind, obs_cat in enumerate(header_observation_categories) if obs_cat != '']
        return categories
        
                
        
    
    def parse(self):
        """
        Parse the file
        """
        self.initialize_results()
        with open(self.filename, 'rb') as csvfile:
            # The first line is not used, discard it
            csvfile.readline()
            # Set up the csv reader
            reader = csv.reader(csvfile)
            # Retrieve the broad categories from the next line
            header_broad_categories = reader.next()
            # Get the specific categories
            header_observation_categories = reader.next()
            # Parse these categories
            self.categories = self.parse_categories(header_broad_categories, header_observation_categories)
            # Get rid of the basic reader, we can now use the DictReader
            del reader
            # The time category must always be the first column
            time_category = self.categories[0]
            # Set up the results object
            self.results = defaultdict(list)
            reader = csv.DictReader(csvfile, fieldnames = self.categories)
            for line in reader:
                # Skip any lines without something in the minute field, as these are presumed to be just headers
                time_block = line[time_category]
                if time_block != '':
                    # get rid of the ranges, so we could analyze or plot these data
                    time_block_first_digit = time_block.split('-')[0].strip()
                    # The times are stored in a list
                    self.times.append(time_block_first_digit)
                    for key, value in line.iteritems():
                        if key != time_category and key is not None:
                            if value.strip() == '':
                                value = 0
                            else:
                                value = 1
                            self.results[key].append(value)



def compare_teacher_evals(eval1, eval2):
    """
    Returns a Counter with the following keys:
    both, neither, first, second
    """
    assert eval1.categories == eval2.categories, \
    "The categories do not match, I can't compare these\nEval1 Categories: %s\nEval2 Categories: %s" % (eval1.categories, eval2.categories)
    assert eval1.times == eval2.times, \
    "The times do not match, I can't compare these.\nEval1 times: %s\nEvan2 times: %s" % (eval1.times, eval2.times)
    cnt = Counter()
    print "Both reviewers agree on the following:"
    for category in eval1.categories:
        both_counter=0
        # The : MIN category will be in categories.  We shouldn't try to process this, though
        # We also want to leave off the Engagement category because it is optional and not all reviewers do it.
        if category in eval1.results and category.lower().find('engagement')==-1:
            for time_ind, time in enumerate(eval1.times):
                eval1result = eval1.results[category][time_ind]
                eval2result = eval2.results[category][time_ind]
                if eval1result==1 and eval2result==1:
                    cnt['both']+=1
                    both_counter += 1
                elif eval1result==0 and eval2result==0:
                    cnt['neither']+=1
                elif eval1result==1 and eval2result==0:
                    cnt['first']+=1
                elif eval1result==0 and eval2result==1:
                    cnt['second']+=1
                else:
                    raise IOError("Something bad happened with our parsing.  This is likely a data problem...")
        if both_counter>0:
            print "  %d  - time blocks on category %s" % (both_counter, category)
    print """Totals:
Both: %d
Neither: %d
First only: %d
Second only: %d
Total: %d
Total agreement: %d (%.2f%%)""" % (cnt['both'], cnt['neither'], cnt['first'], cnt['second'], \
                           sum(cnt.values()), cnt['both']+cnt['neither'], (cnt['both']+cnt['neither'])/sum(cnt.values()))
    return cnt
    

def html_output(eval1, eval2, output_file):
    """
    A quick and dirty attempt at making some plots
    """
    import json
    head="""
<html>
  <head>
    <!--Load the AJAX API-->
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
    
      // Load the Visualization API and the piechart package.
      google.load('visualization', '1.0', {'packages':['corechart']});
      
      // Set a callback to run when the Google Visualization API is loaded.
      google.setOnLoadCallback(drawCharts);
      
      function drawCharts() {
          var data = {};
      
"""
    output = head

    
    # Add the data
    for category in eval1.categories[1:]:
        data = [['Time', 'Eval1', 'Eval2']]
        for time_ind, time in enumerate(eval1.times):
            data.append([int(time), eval1.results[category][time_ind], eval2.results[category][time_ind]])
        output += """data["%s"] = google.visualization.arrayToDataTable(%s, false);\n""" % (category, json.dumps(data))
    
    
    # Add the chart functions
    for category in eval1.categories[1:]:
        output += """new google.visualization.ColumnChart(document.getElementById("%s")).
                        draw(data["%s"], {title:"%s", width:600, height:100, hAxis: {title: "Minute"},
                        isStacked: true});
                    """ % (category, category, category)
    
    # Close the script tags and start the body
    output += """};
    </script>
</head>
<body>
"""
    
    # Add divs for the plots
    for category in eval1.categories[1:]:
        output += '<div id="%s" style="width:700; height:100"></div>\n' % category
    
    # End the page
    output += """</body>
</html>"""
    with open(output_file, 'w') as f:
        f.write(output)
        
        


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Parse, compare, and analyze \
    teaching observations")
    parser.add_argument("csvfile", nargs=2, help="A space separated \
    list of the filenames.  Only the first two will be read.")
    parser.add_argument('-t', '--test', action='store_true', help="Run the tests instead of running the program")
    parser.add_argument('-o', '--output', nargs=1, help="Produce a quick and dirty html page with bar graphs.")
    args = parser.parse_args()
    if args.test:
        import doctest
        doctest.testmod()
    else:
        for csvfile in args.csvfile:
            if not (os.path.exists(csvfile)):
                raise IOError("File %s does not exist" % csvfile)
        csv1 = args.csvfile[0]
        TE1 = TeacherObservation(csv1)
        TE1.parse()
        
        csv2 = args.csvfile[1]
        TE2 = TeacherObservation(csv2)
        TE2.parse()
        
        cnt = compare_teacher_evals(TE1, TE2)
        if args.output:
            html_output(TE1, TE2, args.output[0])
    
