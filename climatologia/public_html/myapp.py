#--- https://www.youtube.com/watch?v=51F_frStZCQ&t=525s
from flask import Flask, render_template, request
from flask_mysqldb import MySQL
from flask import jsonify
from datetime import datetime
import json

app = Flask(__name__)

#--- Database configuration
app.config['MYSQL_USER'] = 'USER'
app.config['MYSQL_PASSWORD'] = 'PASSWORD'
app.config['MYSQL_HOST'] = 'HOST'
app.config['MYSQL_DB'] = 'DB'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)
#--- Home route
@app.route('/')
def welcome():
    return render_template('homePage.html')

@app.route('/api/lastDate')
def getLastDate():
    cur = mysql.connection.cursor()
    lastDate = request.args.get('lastDate', 'null')
    if lastDate == 'lastDate':
        cur.execute("SELECT `Date` FROM `climate`.`data_usgs` ORDER BY `Date` DESC LIMIT 1;")
        date = str(cur.fetchone() )
        date =  str(datetime.strptime(date[date.find('(',1)+1:date.find(')')].replace(' ','').replace(',', '-'),'%Y-%m-%d').date())
        date = '{"lastDate":'+'"'+date +'"}'
        return json.loads(date)
    else:
        return "Error: lastDate parameter must be specified; if specified check parameter spelling"

#--- Api route
@app.route('/api')
def get():
    cur = mysql.connection.cursor()
    #--- Variables with default values set to null cannot remain null during execution
    q = request.args.get('q', 'null')
    station = request.args.get('station', 'all')
    attr = request.args.get('elem', 'null')
    calc = request.args.get('calc', 'none')
    start = request.args.get('startdate')
    end = request.args.get('enddate', start)

    stationType = request.args.get('type', 'all')

    if q == 'station':
        #--- Will return all stations and their data
        if stationType == 'all':
            cur.execute('''SELECT * FROM station;''')
        #--- Will return stations that start with the string "stationType"
        else:
            stationType = stationType + '%' # Will add wildcard operator, "%", to end of string for use in query dynamic operator
            cur.execute('''SELECT * FROM station WHERE stationid like %s;''', (stationType,))
    
    elif q == 'data':
        #--- Will return error message when attribute is null
        if attr == 'null':
            return 'Error: element parameter \"elem\" must be specified'
        #--- will return normal values by day
        elif attr == 'nord':
            if station == 'all':
                cur.callproc('get_all_normals_dly', [start, end])
            else:
                cur.callproc('get_station_normals_dly', [station, start, end])
        elif attr == 'norm':
            if station == 'all':
                cur.callproc('get_all_normals_mly', [start, end])
            else:
                cur.callproc('get_station_normals_mly', [station, start, end])         
        else:
            #--- Will return base value according to attr
            if calc == 'none':
                if station == 'all':
                    cur.callproc('get_all_attr', [attr, start, end])
                else:
                    cur.callproc('get_station_attr', [station, attr, start, end])
            #--- Will return all calculations in a single file according to attr
            elif calc == 'all':
                if station == 'all':
                    cur.callproc('get_all_allCalc', [attr, start, end])
                else:
                    cur.callproc('get_station_allCalc', [station, attr, start, end])
            #--- Will return averaged value according to attr
            elif calc == 'avg':
                if station == 'all':
                    cur.callproc('get_all_avg', [attr, start, end])
                else:
                    cur.callproc('get_station_avg', [station, attr, start, end])
            #--- Will return maximum value according to attr
            elif calc == 'max':
                if station == 'all':
                    cur.callproc('get_all_max', [attr, start, end])
                else:
                    cur.callproc('get_station_max', [station, attr, start, end])
            #--- Will return minimum value according to attr
            elif calc == 'min':
                if station == 'all':
                    cur.callproc('get_all_min', [attr, start, end])
                else:
                    cur.callproc('get_station_min', [station, attr, start, end])
            #--- Will return the standard deviation according to attr
            elif calc == 'stddev':
                if station == 'all':
                    cur.callproc('get_all_stddev', [attr, start, end])
                else:
                    cur.callproc('get_station_stddev', [station, attr, start, end])
            #--- Will return the standard error according to attr
            elif calc == 'stderr':
                if station == 'all':
                    cur.callproc('get_all_stderr', [attr, start, end])
                else:
                    cur.callproc('get_station_stderr', [station, attr, start, end])
            #--- Will return error message when calc is not valid
            else:
                return 'Error: \"' + calc + '\" not a valid value for parameter \"calc\"'
    #--- Will return error message if q is null          
    else:
        return 'Error: query parameter \'q\' must be specified; if specified check parameter spelling'

    results = cur.fetchall()
    resp = jsonify(results)
    resp.status_code = 200
    return resp

if __name__ == '__main__':
    app.run()
