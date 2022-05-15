import sys
import subprocess
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
    
if __name__ == "__main__":
    # Installs and imports the modules    
    required = {'psycopg2', 'pandas'}
    for i in required: checkModule(i)  
    
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