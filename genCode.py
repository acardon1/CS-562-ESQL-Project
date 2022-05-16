import sys
import subprocess
from tokenize import group
from importlib import util
import os

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
    with open('query_output.py', 'a') as mfQueryFile:
        mfQueryFile.write("phi =")
        mfQueryFile.write(str(phi))
        mfQueryFile.write("\n")
        mfQueryFile.close()

# Gets the user input instead of reading txt file                       
def getUserInput():
    val = input("Enter all the Select Attributes (S) separated with commas: ")
    phi["S"] = [i.strip() for i in val.split(",")]
    val = input("Enter the number of grouping variables: ")
    while not val.isdigit():
        val = input("Invalid Input! Enter the number of grouping variables: ")
    phi["n"] = val
    val = input("Enter all the Grouping Attributes (V) separated with commas: ")
    phi["V"] = [i.strip() for i in val.split(",")]  
    val = input("Enter all the aggregate functions ([F]) separated with commas: ")
    phi["F"] = [i.strip() for i in val.split(",")]
    for i in range(int(phi['n'])):
        val = input(f"Enter the condition vector for grouping variable #{i+1}: ")
        phi["sig"].append(val.strip())
    val = input("Enter the having condition (G): ")
    phi["G"] = val
                
# Print out Phi to see            
def printPhi():
    for i in phi.items():
        print(f"{i[0]} : {i[1]}")

mf_algo ="""
import psycopg2
import argparse
import pandas as pd

DATABASE_USERNAME = ""
DATABASE_PASSWORD = ""
DATABASE_SERVER = "localhost"
DATABASE_NAME = "postgres"

# Establishes a connection to the database using psycopg2 and returns the values of the query
def commit_query(query,result):
    values = None
    connection = ""
    try:
        connection = psycopg2.connect(user= DATABASE_USERNAME,
                                    password= DATABASE_PASSWORD ,
                                    host= DATABASE_SERVER,
                                    database= DATABASE_NAME)
        cursor = connection.cursor()
        cursor.execute(query)
        if cursor.description != None: values = cursor.fetchall()
        connection.commit()
        print(result) 
        connection.close() 
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL: ", error)
        if(connection):
            connection.close() 
        exit()
    return values

# Run the file: python "e:/main.py" username password [optional] server_address database_name
# Example: python "e:/main.py" postgres pwd [localhost postgres]
parser = argparse.ArgumentParser(description="Database Credentials")
parser.add_argument("database_username", help="Database Authentication Username")
parser.add_argument("database_password", help="Database Authentication Password")
parser.add_argument("-s", "--server_address", help="Database Server Address")
parser.add_argument("-d", "--database_name", help="Database Name")
args = parser.parse_args()

DATABASE_USERNAME = args.database_username
DATABASE_PASSWORD = args.database_password

if args.server_address:
    DATABASE_SERVER = args.server_address

if args.database_name:
    DATABASE_NAME = args.database_name

# Gets all the rows from the sales database by running the query below
values = commit_query("SELECT * from sales", "Getting all entries in sales table")

Attributes = {
    'cust' : 0,
    'prod' : 1,
    'day' : 2,
    'month' : 3,
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
            if key not in MF_Struct.keys():
                for groupAttribute in phi['V']:
                    colVal = row[Attributes[groupAttribute]]
                    if colVal:
                        value[groupAttribute] = colVal
                for agg in phi["F"]:
                    if (agg.split('_')[1] == 'avg' or agg.split('_')[0] == 'avg'):
                        value[agg] = {'sum': 0, 'count': 0, 'avg': 0} #use sum and count to help calculate avg
                    elif (agg.split('_')[1] == 'min' or agg.split('_')[0] == 'min'):
                        value[agg] = 9999 #set default to 9999, since > all possible quants, for min
                    else:
                        value[agg] = 0 #otherwise max, count, sum are 0 by default
                MF_Struct[key] = value
            else:
                for agg in phi["F"]:
                    groupingAttribute = agg.split('_')[1]
                    if (len(agg.split('_')) == 2):
                        if (agg.split('_')[0] == 'sum'): #recalc sum
                            MF_Struct[key][agg] += int(row[Attributes[groupingAttribute]])
                        elif (agg.split('_')[0] == 'count'): #increment count
                            MF_Struct[key][agg] += 1
                        elif (agg.split('_')[0] == 'min'): #recalc min
                            if (row[Attributes[groupingAttribute]] < MF_Struct[key][agg]):
                                MF_Struct[key][agg] = int(row[Attributes[groupingAttribute]])
                        elif (agg.split('_')[0] == 'avg'): #recalc avg
                            newSum = MF_Struct[key][agg]['sum'] + int(row[Attributes[groupingAttribute]])
                            newCount = MF_Struct[key][agg]['count'] + 1
                            MF_Struct[key][agg] = {'sum': newSum, 'count': newCount, 'avg': newSum/newCount}
                        else: #recalc max
                            if (row[Attributes[groupingAttribute]] > MF_Struct[key][agg]):
                                MF_Struct[key][agg] = row[Attributes[groupingAttribute]]
    else: #setting up each grouping variable in mf_struct
        for agg in phi['F']:
            if (len(agg.split('_')) == 2):
                continue
            groupingVariable = agg.split('_')[0]
            aggregateFunc = agg.split('_')[1]
            groupingAttribute = agg.split('_')[2]
            if (i == int(groupingVariable)):
                for row in values:
                    key = ''
                    for attribute in phi['V']:
                        key += f'{str(row[Attributes[attribute]])}'
                    #using strings with eval() method, replace grouping variables with actual values
                    if aggregateFunc == 'sum':
                        evalString = phi['sig'][i-1]
                        for s in predParts[i-1]:
                            if ((len(s.split('.')) > 1) and (s.split('.')[0] == str(i))): #changing 1.var
                                val = row[Attributes[s.split('.')[1]]]
                                try:
                                    int(val)
                                    evalString = evalString.replace(s, str(val))
                                except:
                                    evalString = evalString.replace(s, f"'{val}'")
                        for groupAttr in Attributes:
                            if (groupAttr in evalString):
                                evalString = evalString.replace(groupAttr, f"'{str(row[Attributes[groupAttr]])}'")
                        if eval(evalString.replace('=', '==')): #recalc sum
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
                                    evalString = evalString.replace(s, f"'{val}'")
                        for groupAttr in Attributes:
                            if (groupAttr in evalString):
                                evalString = evalString.replace(groupAttr, f"'{str(row[Attributes[groupAttr]])}'")
                        if eval(evalString.replace('=', '==')): #recalc avg
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
                                    evalString = evalString.replace(s, f"'{val}'")
                        for groupAttr in phi['V']:
                            if (groupAttr in evalString):
                                evalString = evalString.replace(groupAttr, f"'{str(row[Attributes[groupAttr]])}'")
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
                                    evalString = evalString.replace(s, f"'{val}'")
                        for groupAttr in phi['V']:
                            if (groupAttr in evalString):
                                evalString = evalString.replace(groupAttr, f"'{str(row[Attributes[groupAttr]])}'")
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
                                    evalString = evalString.replace(s, f"'{val}'")
                        for groupAttr in phi['V']:
                            if (groupAttr in evalString):
                                evalString = evalString.replace(groupAttr, f"'{str(row[Attributes[groupAttr]])}'")
                        if eval(evalString.replace('=', '==')):
                            MF_Struct[key][agg] += 1
#set up output
df = pd.DataFrame(None, None, phi['S'])
outputRow = ''
#every row in the MF_Struct should rows for all grouping vars + 1 bc group 0
#each row has columns initialized for its aggregates
for row in MF_Struct: #checking having condition AND doing output
    evalString = ''
    if phi['G'] != '': #having condition exists
        for s in phi['G'].split(' '):
            if s not in ['>', '>=', '<', '<=', '==', 'and', 'or', 'not', '*', '/', '+', '-']:
                try: #is number?
                    float(s)
                    evalString += s
                except: #is an aggregate
                    if ((len(s.split('_')) > 1) and (s.split('_')[1] == 'avg') or s.split('_')[0] == 'avg'):
                        evalString += str(MF_Struct[row][s]['avg'])
                    else:
                        evalString += str(MF_Struct[row][s])
            else: #is operator for comparison
                evalString += f' {s} '
        if (eval(evalString.replace('=', '=='))):
            output_info = []
            for elem in phi['S']:
                if ((len(elem.split('_')) > 1) and (elem.split('_')[1] == 'avg' or elem.split('_')[0] == 'avg')):
                    output_info += [MF_Struct[row][elem]['avg']]
                else:
                    output_info += [MF_Struct[row][elem]]
            df.loc[len(df)] = output_info
            output_info = ''
        evalString = ''
    else: #no having condition -> only output
        output_info = []
        for elem in phi['S']:
            if ((len(elem.split('_')) > 1) and (elem.split('_')[1] == 'avg' or elem.split('_')[0] == 'avg')):
                output_info += [MF_Struct[row][elem]['avg']]
            else:
                output_info += [MF_Struct[row][elem]]
        df.loc[len(df)] = output_info
        output_info = ''
print(df.to_string(index=False))
"""

def mf_query():
    with open('query_output.py', 'a') as mfQueryFile:
        mfQueryFile.write(mf_algo)
        mfQueryFile.close()
    
if __name__ == "__main__":
    # Installs and imports the modules    
    #required = {'psycopg2', 'pandas'}
    #for i in required: checkModule(i)  
    
    if os.path.exists("query_output.py"):
        os.remove("query_output.py")
  
    txt_file = 'phiOperator.txt'
    option = input(f"Do you want to read from {txt_file}? [Y/N] ")
    while True:
        if option in {"y","Y","yes","Yes"}:
            getPhiValues(txt_file)
            break
        elif option in {"n","N","no","No"}:
            getUserInput()
            break
        else:
            option = input(f"Invalid Input! Do you want to read from {txt_file}? [Y/N] ")
    printPhi()
    mf_query()