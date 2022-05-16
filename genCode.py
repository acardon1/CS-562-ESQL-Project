import sys
import subprocess
from tokenize import group
from importlib import util

phi = {"S" : [],
       "n" : "",
       "V" : [],
       "F" : [],
       "sig" : [],
       "G" : ""
}
python = sys.executable

# Checks if the user has all the packages we are using installed and returns the module
def checkModule(mod_name):
    if util.find_spec(mod_name):
        print(f"{mod_name} already installed!")
    else:
        print(f"Installing {mod_name}")
        subprocess.check_call([python, '-m', 'pip', 'install', mod_name], stdout=subprocess.DEVNULL)
        print(f"{mod_name} installed!")

# Reads the text file containing all the parameters and saves it to a dictionary    
def getPhiValues(txt_file):
    file = open(txt_file, mode = 'r', encoding = 'utf-8-sig')
    lines = file.readlines()
    file.close()
    keys = [*phi.keys()]
    count = -1
    for line in lines:
        if line[0] == "#":
            count += 1
        elif line.strip():
            for i in line.strip().split(","):
                    if keys[count] == "n":
                        if not i.strip().isdigit():
                            raise ValueError(f"Number of Grouping Variables has to be an integer!")
                        phi[keys[count]] = int(i.strip())
                    elif keys[count] == "G":
                        if phi[keys[count]]: 
                            raise ValueError(f"Only one string allowed for having clause!")
                        phi[keys[count]] = i.strip()
                    else:    
                        phi[keys[count]].append(i.strip())
                
# Print out Phi to see            
def printPhi():
    for i in phi.items():
        print(f"{i[0]} : {i[1]}")

mf_algo ="""
#add imports and somehow send values and phi into this code
#needs values and phi
Attributes = {
    'cust' : 0,
    'prod' : 1,
    'day' : 2,
    'mo' : 3,
    'year' : 4,
    'state' : 5,
    'quant' : 6
}
MF_Struct = {}
#will be used for setting up grouping variables
predParts = [] #list of each predicate's parts in 2d array
for i in phi['sig']:
    predParts.append(i.split(' '))
#loop through table for each grouping variable
for i in range(phi['n'] + 1):
    #grouping variable 0 (set up the group)
    if (i == 0):
        for row in values:
            key = ''
            value = {}
            for attribute in phi['V']:
                key += f'{str(row[Attributes[attribute]])}'
            key = key[:-1]
            if key not in MF_Struct.keys():
                for groupAttribute in phi['V']:
                    colVal = row[groupAttribute]
                    if colVal:
                        value[groupAttribute] = colVal
                for agg in phi["F"]:
                    if (agg.split('_')[1] == 'avg'):
                        value[agg] = {'sum': 0, 'count': 0, 'avg': 0} #use sum and count to help calculate avg
                    elif (agg.split('_')[1] == 'min'):
                        value[agg] = 9999 #set default to 9999, since > all possible quants, for min
                    else:
                        value[agg] = 0 #otherwise max, count, sum are 0 by default
                MF_Struct[key] = value
    else: #setting up each grouping variable in mf_struct
        for agg in phi['F']:
            groupingVariable = agg.split('_')[0]
            aggregateFunc = agg.split('_')[1]
            groupingAttribute = agg.split('_')[2]
            
            if (i == int(groupingVariable)):
                for row in values:
                    key = ''
                    for attribute in phi['V']:
                        key += f'{str(row[Attributes[attribute]])}'
                    key = key[:-1]
                    #using strings with eval() method, replace grouping variables with actual values
                    if aggregateFunc == 'sum':
                        evalString = phi['sig'][i-1]
                        for s in predParts[i-1]:
                            if ((len(s.split('.')) > 1) and (s.split('.')[0] == str(i))):
                                val = row[Attributes[s.split('.')[1]]]
                                try:
                                    int(val)
                                    evalString = evalString.replace(s, str(val))
                                except:
                                    evalString = evalString.replace(s, f"'{val}")
                        if eval(evalString.replace('=', '==')):#recalc sum
                            sum = int(row[Attributes[groupingAttribute]])
                            MF_Struct[key][agg] += sum
                    elif aggregateFunc == 'avg':
                        sum = MF_Struct[key][agg]['sum']
                        count = MF_Struct[key][agg]['count']
                        evalString = phi['sig'][i-1]
                        for s in predParts[i-1]:
                            if ((len(s.split('.')) > 1) and (s.split('.')[0] == str(i))):
                                val = row[Attributes[s.split('.')[1]]]
                                try:
                                    int(val)
                                    evalString = evalString.replace(s, str(val))
                                except:
                                    evalString = evalString.replace(s, f"'{val}")
                        if eval(evalString.replace('=', '==')):#recalc avg
                            sum += int(row[Attributes[groupingAttribute]])
                            count += 1
                            MF_Struct[key][agg] = {'sum': sum, 'count': count, 'avg': (sum / count)}
                    elif aggregateFunc == 'min':
                        evalString = phi['sig'][i-1]
                        for s in predParts[i-1]:
                            if ((len(s.split('.')) > 1) and (s.split('.')[0] == str(i))):
                                val = row[Attributes[s.split('.')[1]]]
                                try:
                                    int(val)
                                    evalString = evalString.replace(s, str(val))
                                except:
                                    evalString = evalString.replace(s, f"'{val}")
                        if eval(evalString.replace('=', '==')):#recalc min
                            min = int(MF_Struct[key][agg])
                            if (int(row[Attributes[groupingAttribute]]) < min):
                                MF_Struct[key][agg] = row[Attributes[groupingAttribute]]
                    elif aggregateFunc == 'max':
                        evalString = phi['sig'][i-1]
                        for s in predParts[i-1]:
                            if ((len(s.split('.')) > 1) and (s.split('.')[0] == str(i))):
                                val = row[Attributes[s.split('.')[1]]]
                                try:
                                    int(val)
                                    evalString = evalString.replace(s, str(val))
                                except:
                                    evalString = evalString.replace(s, f"'{val}")
                        if eval(evalString.replace('=', '==')):
                            max = int(MF_Struct[key][agg])
                            if (int(row[Attributes[groupingAttribute]]) > max):
                                MF_Struct[key][agg] = row[Attributes[groupingAttribute]]
                    elif aggregateFunc == 'count':
                        evalString = phi['sig'][i-1]
                        for s in predParts[i-1]:
                            if ((len(s.split('.')) > 1) and (s.split('.')[0] == str(i))):
                                val = row[Attributes[s.split('.')[1]]]
                                try:
                                    int(val)
                                    evalString = evalString.replace(s, str(val))
                                except:
                                    evalString = evalString.replace(s, f"'{val}")
                        if eval(evalString.replace('=', '==')):
                            MF_Struct[key][agg] += 1
#set up output
outputRow = ''
for elem in phi['S']:
    outputRow += elem + "\t"
print(outputRow)
outputRow = ''
#every row in the MF_Struct should rows for all grouping vars + 1 bc group 0
#each row has columns initialized for its aggregates
for row in MF_Struct: #checking having condition AND doing output
    evalString = ''
    if phi['G'] != '': #having condition exists
        for s in phi['G'].split(' '):
            if s not in ['>', '>=', '<', '<=', '==', 'and', 'or', 'not', '*', '/', '+', '-']:
                try: #is number?
                    int(s)
                    evalString += s
                except: #is an aggregate
                    if ((len(s.split('_')) > 1) and (s.split('_')[1] == 'avg')):
                        evalString += str(MF_Struct[row][s]['avg'])
                    else:
                        evalString += str(MF_Struct[row][s])
            else: #is operator for comparison
                evalString += f' {s}'
        if (eval(evalString.replace('=', '=='))):
            output_info = []
            for elem in phi['S']:
                if ((len(elem.split('_')) > 1) and (elem.split('_')[1] == 'avg')):
                    output_info += [str(MF_Struct[row][elem]['avg'])]
                else:
                    output_info += [str(MF_Struct[row][elem])]
            for elem in phi['S']:
                outputRow += elem + "\t"
            print(outputRow)
            outputRow = ''
        evalString = ''
    else:
        output_info = []
        for elem in phi['S']:
            if ((len(elem.split('_')) > 1) and (elem.split('_')[1] == 'avg')):
                output_info += [str(MF_Struct[row][elem]['avg'])]
            else:
                output_info += [str(MF_Struct[row][elem])]
        for elem in phi['S']:
            outputRow += elem + "\t"
        print(outputRow)
        outputRow = ''
"""

def mf_query():
    with open('query_output.py', 'a') as mfQueryFile:
        mfQueryFile.write(mf_algo)
        mfQueryFile.close()
    
if __name__ == "__main__":
    # Installs and imports the modules    
    required = {'psycopg2', 'pandas'}
    for i in required: checkModule(i)  
    
    txt_file = 'phiOperator.txt'
    getPhiValues(txt_file)
    printPhi()