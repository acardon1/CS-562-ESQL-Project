# CS-562-ESQL-Project
Query processing engine to process ESQL queries: specifically the implementation of MF-Queries.
Program will produce embedded SQL code that will properly query against sales table and produce desired output.

## Setup & Running
1. Run genCode.py, this will generate the code in a 'query_output.py' file and download the proper modules needed.

2. Run the generated file, 
   ```
   python .\query_output [db_username] [db_pwd]  -s [server_address] -d [db_name]
   ```