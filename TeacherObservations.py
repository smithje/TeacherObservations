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
from collections import defaultdict, Counter, OrderedDict
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
        
        Because the column headers aren't all the same in the second line, we need to special care in parsing the 
        categories.  We will create an OrderedDict with the broad categories (instructor doing, teacher doing) as keys.
        The values will be an array of subcategories.  
        
        We will receive the values already broken up by the csv module.
        
        Note that we toss out any categories which don't appear in the observation categories.  This is mostly to get rid of the comments.
        
        >>> header_broad_categories = ['','1. instructor','','','','','','','','','','','','2. Students','','','','','','','','','','','','','3. Engagement','','','Comments']
        >>> header_observation_categories = ['MIN','Lec','FUp','RtW','D / V','PQ','CQ','R / H ','1o1','CD ','AD','N','O','L','Ind','Prd','CG','WG ','OG ','SQ','WC','SP ','TQ ','W','AQ','O','L','M','H','']
        >>> categories = TeacherObservation.parse_categories(header_broad_categories, header_observation_categories)
        >>> categories.keys()
        ['', '1.  instructor', '2. Students']
        >>> categories['']
        ['MIN']
        """
        assert len(header_broad_categories) == len(header_observation_categories), "The header rows must have the same number of columns"
        broad_categories_unpacked = []
        categories = OrderedDict()
        # Force the first one to be Time
        last_category = 'Time'
        for category in header_broad_categories:
            if category != '':
                last_category = category
            broad_categories_unpacked.append(last_category)
        for index, broad_category in enumerate(broad_categories_unpacked):
                if not broad_category.startswith('Comment'):
                    
                    categories.setdefault(broad_category, [])
                    categories[broad_category].append(header_observation_categories[index])
        del categories['Time']
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
            
            # Set up the results object
            self.results = {}
            for category in self.categories.keys():
                if category != '':
                    self.results[category] = defaultdict(list)
            #reader = csv.DictReader(csvfile, fieldnames = self.categories)
            for line in reader:
                
                # Time must always be first
                time_block = line[0]
                # Skip any lines without something in the minute field, as these are presumed to be just headers
                if time_block != '':
                    # get rid of the ranges, so we could analyze or plot these data
                    time_block_first_digit = time_block.split('-')[0].strip()
                    # The times are stored in a list
                    self.times.append(time_block_first_digit)
                    
                    # Initialize our parsing
                    result_position = 1
                    
                    # Iterate over the categories
                    for category, obs in self.categories.iteritems():
                        # Iterate over the observations
                        for observation in obs:
                            
                            value=line[result_position]
                            if value.strip() == '':
                                value = 0
                            else:
                                value = 1
                            # Build up the results
                            self.results[category][observation].append(value)
                            # Move on to the next position
                            result_position += 1
                                    

def count_filled_time_intervals(observations):
    """
    We want to count how many time intervals were actually filled out - that means 
    that it is non-zero for any observation 
    """
    # Put all the observations together:
    obs = zip(*observations)
    
    # Count up the intervals that have anything filled out
    return sum([1 for x in obs if any(x) is True])
    
    
def compare_teacher_evals(eval1, eval2):
    """
    Returns a Counter with the following keys:
    both, neither, first, second
    """
    
    
    assert eval1.categories == eval2.categories, \
    "The categories do not match, I can't compare these\nEval1 Categories: %s\nEval2 Categories: %s" % (eval1.categories, eval2.categories)
    assert eval1.times == eval2.times, \
    "The times do not match, I can't compare these.\nEval1 times: %s\nEvan2 times: %s" % (eval1.times, eval2.times)
    
    # How many rows filled out in eval1
    eval1obs = []
    for obs in eval1.results.itervalues():
        eval1obs.extend(obs.values())
    eval1_count = count_filled_time_intervals(eval1obs)
    
    print "Teacher 1: %d time blocks" % eval1_count
    
    eval2obs = []
    for obs in eval2.results.itervalues():
        eval2obs.extend(obs.values())
    eval2_count = count_filled_time_intervals(eval2obs)
    
    print "Teacher 2: %d time blocks" % eval2_count
    
    if eval1_count>eval2_count:
        total_time_count = eval1_count
    else:
        total_time_count = eval2_count
    
    

    # How many rows filled out in eval2
    
    # Create a counter to get global statistics
    cnt = Counter()
    category_results = defaultdict(list)
    print "Category results (Observation code, both, neither, first only, second only, overlap %)"
    for category, observations in eval1.categories.iteritems():
        eval1_total_counts = sum([sum(observation) for observation in eval1.results[category].itervalues()])
        eval2_total_counts = sum([sum(observation) for observation in eval2.results[category].itervalues()])
        
        print category
        overlap_counter = 0
        for observation in observations:
            
            eval1results = eval1.results[category][observation]
            eval2results = eval2.results[category][observation]
            
            both_match = sum([1 for index, x in enumerate(eval1results) if x==1 and eval2results[index]==1])
            neither_match = sum([1 for index, x in enumerate(eval1results) if x==0 and eval2results[index]==0])
            first_only = sum([1 for index, x in enumerate(eval1results) if x==1 and eval2results[index]==0])
            second_only = sum([1 for index, x in enumerate(eval1results) if x==0 and eval2results[index]==1])
            
            # Increase our global counts
            cnt['both']+=both_match
            cnt['neither']+=neither_match
            cnt['first']+=first_only
            cnt['second']+=second_only
            
            eval1_counts = 100*float(sum(eval1results))/eval1_total_counts
            eval2_counts = 100*float(sum(eval2results))/eval2_total_counts
            
            # We calculate a general agreement for this observation by simply taking the lesser of eval1_counts and eval2_counts
            if eval1_counts<eval2_counts:
                overlap = eval1_counts
            else:
                overlap = eval2_counts
            

            overlap_counter+=overlap
            
            print " %s, %d, %d, %d, %d, %.1f%%" % (observation, both_match, neither_match, first_only, second_only, overlap)
            category_results[category].append(both_match)
        print " Total Overlap for %s: %.1f" % (category, overlap_counter)
            

    print """Totals:
Both: %d
Neither: %d
First only: %d
Second only: %d
Total: %d
Total agreement: %d (%.2f%%)
""" % (cnt['both'], cnt['neither'], cnt['first'], cnt['second'], \
                           sum(cnt.values()), cnt['both']+cnt['neither'], \
                           100.0*(cnt['both']+cnt['neither'])/sum(cnt.values()))
    return cnt, category_results, total_time_count
    

def html_output(eval1, eval2, output_file, category_result, time_blocks):
    """
    A quick and dirty attempt at making some plots
    """
    import json
    
    def tree():
        return defaultdict(tree)
    
    def get_title(category, observation):
       return "%s: %s" % (category, observation)  
    
    def get_css_name(name):
        return name.translate(None, r"""!"#$%&'()*+,./:;<=>?@[\]^`{|}~ 0123456789""")
    

    head="""<!DOCTYPE html>
<html>
  <head>
    <title>
        %s
    </title>
    <style>
        .plot {width:700px;height:250px}
    </style>
    <!--Load the AJAX API-->
    <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.8.2/jquery.min.js"></script>
    <script src="http://code.highcharts.com/highcharts.js"></script>
    <script src="http://code.highcharts.com/modules/exporting.js"></script>
    <script>
      $(function () {
        var times = %s; 

        var columnChartOptions = {
               chart: {
                    type: 'column',
                    height: 200,
                    width: 700,
                    borderColor: '#CCC',
                    borderWidth: 2
                },
                xAxis: {
                    categories: times
                },
                yAxis: {
                    min: 0,
                    max: 2,
                    minTickInterval: 1,
                    stackLabels: {
                        enabled: false,
                        style: {
                            fontWeight: 'bold',
                            color: (Highcharts.theme && Highcharts.theme.textColor) || 'gray'
                        }
                    }
                },
                legend: {
                    align: 'right',
                    verticalAlign: 'middle',
                    floating: false,
                    layout: 'vertical',
                    backgroundColor: (Highcharts.theme && Highcharts.theme.legendBackgroundColorSolid) || 'white',
                    borderColor: '#CCC',
                    borderWidth: 1,
                    shadow: false
                },
                tooltip: {
                    formatter: function() {
                        return '<b>'+ this.x +'</b><br/>'+
                            this.series.name +': '+ this.y +'<br/>'+
                            'Total: '+ this.point.stackTotal;
                    }
                },
                plotOptions: {
                    column: {
                        stacking: 'normal'
                    }
                }
          };
          
    var bothColumnChartOptions = {
                   chart: {
                    type: 'column',
                    height: 200,
                    width: 700,
                    borderColor: '#CCC',
                    borderWidth: 2
                },

                yAxis: {
                    min: 0,
                    max: 100,
                    stackLabels: {
                        enabled: false,
                        style: {
                            fontWeight: 'bold',
                            color: (Highcharts.theme && Highcharts.theme.textColor) || 'gray'
                        }
                    },
                    title: {
                        text: '%% of total time blocks'
                    }
                },
                legend: {
                    enabled: false
                },
                tooltip: {
                    formatter: function() {
                        return '<b>'+ this.x +'</b><br/>'+
                            this.series.name +': '+ this.y;
                    }
                },
                plotOptions: {
                    column: {
                        stacking: 'normal'
                    }
                }
    };
          
    var pieChartOptions = {
            chart: {
                plotBackgroundColor: null,
                plotBorderWidth: null,
                plotShadow: false,
                width: '700',
                height: '500'
                
            },

            tooltip: {
                pointFormat: '{series.name}: <b>{point.percentage}%%</b> (<b>{point.y}</b>)',
                percentageDecimals: 1
            },
            plotOptions: {
                pie: {
                    allowPointSelect: true,
                    cursor: 'pointer',
                    dataLabels: {
                        enabled: false,
                    },
                    showInLegend: true
                }
            },
            legend: {
                    align: 'right',
                    verticalAlign: 'middle',
                    floating: false,
                    layout: 'vertical',
                    backgroundColor: (Highcharts.theme && Highcharts.theme.legendBackgroundColorSolid) || 'white',
                    borderColor: '#CCC',
                    borderWidth: 1,
                    shadow: false
                }
        };
""" % (os.path.basename(output_file), json.dumps(eval1.times))
    output = head

    column_chart_additional_options = tree()
    chart_functions = []
    column_chart_div_ids = []
    
    # Add the column chart data
    for category, observations in eval1.categories.iteritems():
        for observation in observations:
            title = get_title(category, observation)
            id = get_css_name(title)
            column_chart_additional_options[id]['title']['text'] = title
            column_chart_additional_options[id]['series'] = \
                [
                  {'name': 'Teacher 1',
                   'data': eval1.results[category][observation]
                   },
                   {'name': 'Teacher 2',
                    'data': eval2.results[category][observation]
                    }
                ]
            chart_functions.append("""$(%s).highcharts($.extend({}, column_chart_additional_options['%s'], columnChartOptions))""" % (id, id))
            column_chart_div_ids.append(id)
    
    
    # Do the new both agree column chart thing
    both_column_chart_additional_options = tree()
    
    for category, observations in eval1.categories.iteritems():
        title = category
        id = get_css_name(title)+'both'
        both_column_chart_additional_options[id]['title']['text'] = category
        both_column_chart_additional_options[id]['xAxis']['categories'] = observations
        both_column_chart_additional_options[id]['series'] = [{'name':'observation', 'data': []}]
        for index, observation in enumerate(observations):
            both_column_chart_additional_options[id]['series'][0]['data'].append(100*float(category_result[category][index])/time_blocks)
        
        chart_functions.append("""$(%s).highcharts($.extend({}, both_column_chart_additional_options['%s'], bothColumnChartOptions))""" % (id, id))
        column_chart_div_ids.append(id)
    
    
    pie_chart_additional_options = tree()
    pie_chart_div_ids = []
    
    # Add the pie chart data
    for category, observations in eval1.categories.iteritems():
        id = get_css_name(category) + 'pie'
        pie_chart_div_ids.append(id)
        pie_chart_additional_options[id]['title']['text'] = category
        pie_chart_additional_options[id]['series'] = \
            [
                {'type': 'pie',
                 'name': 'Observation',
                 'data': []
                }
            ]
        for index, observation in enumerate(observations):
            value = round(category_result[category][index],1)
            pie_chart_additional_options[id]['series'][0]['data'].append({'name': observation,
                             'y': value,
                             'dataLabels': {'enabled': True if value>0 else False}
                             
                             })
        chart_functions.append("""$(%s).highcharts($.extend({}, pie_chart_additional_options['%s'], pieChartOptions))""" % (id, id))
        
        
        
    
    
    output += """\nvar column_chart_additional_options = %s;\n""" % json.dumps(column_chart_additional_options)
    output += """\nvar both_column_chart_additional_options = %s;\n""" % json.dumps(both_column_chart_additional_options)
    output += """\nvar pie_chart_additional_options = %s;\n""" % json.dumps(pie_chart_additional_options)
    
    
    for chart_function in chart_functions:
        output += "        %s\n" % chart_function
    
    
    
#    # Add the pie chart data
#    # Iterate over the broad categories (teachers doing/students doing)
#    for category, observations in eval1.categories.iteritems():
#        data = [['observation', 'overlap']]
#        for index, observation in enumerate(observations):
#            data.append([observation, round(category_result[category][index],1)])
#        output += """data["%s"] = google.visualization.arrayToDataTable(%s);\n""" % (category, json.dumps(data))
#        
#    # Add the pie chart functions
#    for category in eval1.categories.keys():
#        output += """new google.visualization.PieChart(document.getElementById('%s')).
#                        draw(data["%s"], {title: "%s", sliceVisibilityThreshold:0, pieSliceText: 'percentage'});
#                  """ % (category, category, category)
    
    # Close the script tags and start the body
    output += """});
    </script>
</head>
<body>
"""
    for id in column_chart_div_ids:
        output += '<div id="%s" class="plot"></div>\n' % id
    for id in pie_chart_div_ids:
        output += '<div id="%s" class="pie"></div>\n' % id
#    # Add divs for the plots
#    for category, observations in eval1.categories.iteritems():
#        for observation in observations:
#            id = category + ': ' + observation
#            output += '<div id="%s" style="width:700; height:100"></div>\n' % id
#    
#    for category in eval1.categories.keys():
#        output += '<div id="%s" style="width:700; height:500"></div>\n' % category
#        
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
        
        cnt, category_result, total_time_blocks = compare_teacher_evals(TE1, TE2)
        if args.output:
            html_output(TE1, TE2, args.output[0], category_result, total_time_blocks)
    
