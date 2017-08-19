from flask import Flask
from flask import render_template
from flask import request
from flask import abort
from sqlalchemy import desc
from model import db
from model import Location_API
from model import CreateDB
from model import app as application
import simplejson as json
from sqlalchemy.exc import IntegrityError
import os
import requests
import google_coordinates
import json

import googlemaps
import commands



app = Flask(__name__)

@app.route('/')
def homepage():
	return render_template('index.html')

#find all locations
@app.route('/locations',methods =['GET'])
def findAll():
	try:
		locations = Location_API.query.order_by(desc(Location_API.id)).all();
		result = [];
		for location in locations:
			result.append({'id': location.id, 'name': location.name, 'address': location.address, 'city': location.city, 'state': location.state, 'zip': location.zip, 'coordinate': {'lat': location.lat, 'lng':location.lng}});
		return json.dumps(result), 201;
	except IntegrityError:
		return json.dumps({'status':False})


#adding a new location
@app.route('/locations', methods=['POST'])
def post():
	try:
		data = json.loads(request.data)
		if not data or not 'city' in data:
			abort(404)
		database = CreateDB(hostname = 'localhost')
		db.create_all()
		coordinate = google_coordinates.address_to_cordinate(data['address'] + data['city'] + data['state'] + data['zip'])
		lat = str(coordinate['lat'])
		lng = str(coordinate['lng'])
		new_location = Location_API(data['name'], data['address'], data['city'], data['state'], data['zip'], lat, lng)
		db.session.add(new_location)
		db.session.commit()
		added_location = {'id': new_location.id, 'name': new_location.name, 'address': new_location.address, 'city': new_location.city, 'state': new_location.state, 'zip': new_location.zip, 'coordinate': {'lat': new_location.lat, 'lng':new_location.lng}}
		return json.dumps(added_location), 201

	except IntegrityError:
		return json.dumps({'status':False})


@app.route('/locations/<location_id>',methods =['GET'])
def get_locationID(location_id):
	try:
		location = Location_API.query.filter_by(id=location_id).first_or_404()
		return json.dumps({'id': location.id, 'name': location.name, 'address': location.address, 'city': location.city, 'state': location.state, 'zip': location.zip, 'coordinate': {'lat': location.lat, 'lng':location.lng}})
	except IntegrityError:
		return json.dumps({'status':False})

@app.route('/locations/<location_id>',methods=['PUT'])
def update_locationID(location_id):
	try:
		location_data = json.loads(request.data)
		if location_data != None:
			new_name = location_data['name']
			location = Location_API.query.filter_by(id=location_id).first_or_404()
			location.name = new_name
			db.session.commit()
			return json.dumps("Accepted"),202
		else:
			return json.dumps("Error"),400

	except IntegrityError:
		return json.dumps({'status':False})

@app.route('/locations/<location_id>',methods=['DELETE'])
def delete_location(location_id):
    db.session.delete(Location_API.query.get(location_id))
    db.session.commit()
    return json.dumps({}),204

@app.route('/trips', methods=['POST'])
def trip_estimator():

    data1 = json.loads(request.data)
    startID = data1['start']
    locationsID = data1['others']


    alllocations=[]
    alllocations.append(int(startID))
    for i in range(len(locationsID)):
            alllocations.append(int(locationsID[i]))

    location = []
    location_coop = []
    for i in range(len(alllocations)):
            location.append(Location_API.query.filter_by(id=alllocations[i]).first_or_404())
            location_coop.append((location[i].lat , location[i].lng ))

    matrixlength = len(alllocations)

    gmaps = googlemaps.Client(key='AIzaSyCETh6MmyaZGznIQ-GBNKq9dGAA3N3IZPI')
    distanceMatrix = [[0 for row in range(0,matrixlength)] for col in range(0,matrixlength)]
    durationMatrix = [[0 for row in range(0,matrixlength)] for col in range(0,matrixlength)]
    
    startIndex = 0
    while(startIndex < matrixlength):
            matrix = gmaps.distance_matrix(location_coop[startIndex : min((startIndex + 5), matrixlength)], location_coop)
            
            for i in range(len(matrix['rows'])):
                    for j in range(len(matrix['rows'][i]['elements'])):
                            durationMatrix[startIndex + i][j] = matrix['rows'][i]['elements'][j]['duration']['value']/60.0
                            distanceMatrix[startIndex + i][j] = matrix['rows'][i]['elements'][j]['distance']['value']/1000.0
            startIndex += 5
              
    durMatrixFile = "durMatrix.txt"
    disMatrixFile = "disMatrix.txt"
    
    fmatrixDur = open(durMatrixFile, "wb")
    fmatrixDis = open(disMatrixFile, "wb")
    fmatrixDur.write(str(matrixlength) + "\n")
    fmatrixDis.write(str(matrixlength) + "\n")  
    for i in range(len(distanceMatrix)):
        for j in range(len(distanceMatrix)):
            fmatrixDur.write(str(durationMatrix[i][j])+ " ")
            fmatrixDis.write(str(distanceMatrix[i][j])+ " ")
        fmatrixDur.write("\n")
        fmatrixDis.write("\n")
    fmatrixDur.close()    
    fmatrixDis.close()

    a,outputDis = commands.getstatusoutput('./tsp/tsp ' + disMatrixFile)
    a,outputDur = commands.getstatusoutput('./tsp/tsp ' + durMatrixFile)
    print ("shortest distance\n"+outputDis)
    print ("shortest time\n" + outputDur)

    resultDis = outputDis.split("\n")
    bestroute_distance = (resultDis[1].split(":"))[1].strip().split(" ")

    resultDur = outputDur.split("\n")
    bestroute_duration = (resultDur[1].split(":"))[1].strip().split(" ")

    distance_best_route_locations = []
    distance_bestroute_distance = resultDis[2].split(":")[1]
    distance_bestroute_duration = 0.0
    duration_best_route_locations = []
    duration_bestroute_distance = 0.0
    duration_bestroute_duration = resultDur[2].split(":")[1]
          
    for i in range(0,len(bestroute_distance)-1):
		distance_best_route_locations.append(str(location[int(bestroute_distance[i])].name))
	#	distance_bestroute_distance += distanceMatrix[int(bestroute_distance[i])][int(bestroute_distance[i+1])]
		distance_bestroute_duration += durationMatrix[int(bestroute_distance[i])][int(bestroute_distance[i+1])]

		duration_best_route_locations.append(str(location[int(bestroute_duration[i])].name))
		duration_bestroute_distance += distanceMatrix[int(bestroute_duration[i])][int(bestroute_duration[i+1])]
	#	duration_bestroute_duration += durationMatrix[int(bestroute_duration[i])][int(bestroute_duration[i+1])]

	
    providers = []
    start_location = distance_best_route_locations.pop(0)
    duration_best_route_locations.pop(0)
##
##	uber_response = {"name" : "Uber","total_costs_by_cheapest_car_type" : uber_price_total, "currency_code": "USD", "total_duration" : uber_duration_total, "duration_unit": "minute",  "total_distance" : uber_distance_total, "distance_unit": "mile"}
##	lyft_response = {"name" : "Lyft","total_costs_by_cheapest_car_type" : lyft_price_total, "currency_code": "USD", "total_duration" : lyft_duration_total, "duration_unit": "minute",  "total_distance" : lyft_distance_total, "distance_unit": "mile"}
##	 
##	providers.append(uber_response)
##	providers.append(lyft_response)
##
##	trip_planner_response = {"start" : start_location, "best_route_by_costs" : best_route_by_costs, "providers" : providers, "end" : start_location}

    distance_response = {"name" : "Distance", "best_route" : distance_best_route_locations, "total_duration" : distance_bestroute_duration, "duration_unit": "minute",  "total_distance" : distance_bestroute_distance, "distance_unit": "km"}
    duration_response = {"name" : "Duration", "best_route" : duration_best_route_locations, "total_duration" : duration_bestroute_duration, "duration_unit": "minute",  "total_distance" : duration_bestroute_distance, "distance_unit": "km"}
	 
    providers.append(distance_response)
    providers.append(duration_response)

    trip_planner_response = {"start" : start_location, "providers" : providers, "end" : start_location}
    return json.dumps(trip_planner_response)


@app.route('/createdb')
def createDatabase():
	HOSTNAME = 'localhost'
	try:
		HOSTNAME = request.args['hostname']
	except:
		pass
	database = CreateDB(hostname = HOSTNAME)
	return json.dumps({'status':True})

@app.route('/info')
def app_status():
	return json.dumps({'server_info':application.config['SQLALCHEMY_DATABASE_URI']})

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5015, debug=True)

