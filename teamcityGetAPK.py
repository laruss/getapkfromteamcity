#!/usr/bin/env python
import json, os, requests, shutil, subprocess, sys
# from json.decoder import JSONDecodeError
from zipfile import ZipFile


JSONNAME = 'teamcityGetAPK.json'
defaultJSON = {
	"username":"",
	"password":"",
	"serverUrl":"https://teamcity.city-mobil.ru",
	"apksPath":"apks",
	"teamcityPathToAPKFolder":"/app/build/outputs/apk/preview"
}
SETTINGSJSON = defaultJSON
headers = {
	'Content-Type': 'application/json',
	'Accept': 'application/json'
}
working_directory = os.getcwd()
assemblyNum = "101148"
version = "" # prod or debug
TEMPZIPNAME = 'temp.zip' # name of temp zip file
apks = []
dwnld = False

def loadSettingsJSON():
	'''
	try to load json
	if there is no file, create it
	'''
	global SETTINGSJSON
	if not os.path.isfile('./'+JSONNAME):
		createSettingsJSON()
	else:
		with open(JSONNAME) as json_file:
			SETTINGSJSON = json.load(json_file)
		print("Settings are loaded")

def createSettingsJSON():
	with open(JSONNAME, 'w') as outfile:
		json.dump(defaultJSON, outfile)
	print("\nNew Settings are created. Please, fill the file "+JSONNAME+'\n')

def request(path, params={}):
	'''returns json or streaming data (zip-file bytes) if response code is 200'''
	'''otherwise throws Exception'''
	response = requests.get(SETTINGSJSON['serverUrl'] + path,
		auth=(SETTINGSJSON['username'], SETTINGSJSON['password']),
		headers=headers, params=params)
	print("Was sent request to API")
	if response.status_code == 200:
		print("  Response-code is 200")
		if response.headers['Content-Type'] == 'application/json':
			returnData = response.json()
		else:
			print("Downloading Zipfile with APK from API...")
			print(SETTINGSJSON['serverUrl'] + path)
			print(params)
			response = requests.get(SETTINGSJSON['serverUrl'] + path,
				auth=(SETTINGSJSON['username'], SETTINGSJSON['password']),
				headers=headers, params=params, stream=True)
			returnData = response
			print("Zipfile is successfully downloaded")
	else:
		raise Exception(response.text)

	return returnData

def SaveZipFromResponse(response): # needs response as stream
	with open(TEMPZIPNAME, 'wb') as f:
		shutil.copyfileobj(response.raw, f)
	print('Temp file is saved in '+TEMPZIPNAME)

def downloadZIP():
	'''downloads zip with some assemblyNum'''
	# change last word to preview or prod in href
	_pathToAPK_ = SETTINGSJSON['teamcityPathToAPKFolder']
	href = "/app/rest/builds/branch:default:any,number:"+assemblyNum
	try:
		path = href+'/artifacts/archived'+_pathToAPK_
		params = dict(locator="pattern:**/*.apk")
		streamResponse = request(path, params)
		SaveZipFromResponse(streamResponse)
	except:
		raise Exception("No assembly number is found in Teamcity's assembly numbers")

def clear_zips_folder(zf_path):
	folder = zf_path
	for the_file in os.listdir(folder):
		file_path = os.path.join(folder, the_file)
		try:
			if os.path.isfile(file_path):
				os.unlink(file_path)
		except Exception as e:
			print(e)
	print("Folder with zip files is clear.")

def unziip_file(name=TEMPZIPNAME):
	global apks
	apkName = ''
	apksPath = SETTINGSJSON['apksPath']

	try: os.mkdir(apksPath)
	except FileExistsError: pass

	clear_zips_folder(zf_path=apksPath)

	with ZipFile(name, 'r') as zf:
		for el in zf.namelist():
			apkName = el.split('/')[-1]
			apks.append(apkName)
			with zf.open(el) as inApk:
				file = inApk.read()
				with open(apksPath+'/'+apkName, 'wb') as outfile:
					outfile.write(file)
	print('APK is unziped to folder '+apksPath)

def install_apk():
	apksPath = SETTINGSJSON['apksPath']
	apkName = apks[0]
	print(apks)
	if version:
		for apkn in apks:
			if version in apkn:
				apkName = apkn
				break

	adbCommands = (
		'adb devices',
		'adb install -r -d '+working_directory+'/'+apksPath+'/'+apkName
	)
	success = False
	while not success:
		for command in adbCommands:
			try:
				subprocess.check_output(command, shell=True) # trying not to get an error
				success = True	
			except:
				subprocess.call(command, shell=True) # but if we do output error
				if input("Try again? (y/n): ").lower() != 'y':
					success = True
	print("APK is successfully installed to device.")

def main(assNum, vers, dwnld=False):
	global assemblyNum, version
	assemblyNum = assNum
	version = vers
	loadSettingsJSON()
	downloadZIP()
	unziip_file()
	if not dwnld:
		install_apk()