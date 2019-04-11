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
helpUsage ='''
USAGE: teamcityGetAPK.py *arg1* *arg2*
*arg1* - номер сборки
*arg2* - версия приложения
 (слово в названии файла .APK, например 'debug' или 'preview')
*additional args*:
 -d - APK не будет устанавливаться, а только скачается в папку
'''

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

	path = '/app/rest/builds'
	params = dict(locator="branch:default:any,status:SUCCESS,count:500,lookupLimit:1000")
	jsonResponse = request(path, params)
	print("Parsing JSON Response")
	for build in jsonResponse["build"]:
		if assemblyNum in build["number"]:
			path = build['href']+'/artifacts/archived'+_pathToAPK_
			params = dict(locator="pattern:**/*.apk")
			streamResponse = request(path, params)
			SaveZipFromResponse(streamResponse)
			break
	else:
		raise Exception("No assembly number is found in Teamcity's assembly numbers")

def unziip_file(name=TEMPZIPNAME):
	global apks
	apkName = ''
	apksPath = SETTINGSJSON['apksPath']

	try: os.mkdir(apksPath)
	except FileExistsError: pass

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


if __name__ == '__main__':
	if len(sys.argv) == 1 or sys.argv[1].lower() in ('-h','-help', '-d'):
		print(helpUsage)
	else:
		assemblyNum = sys.argv[1]
		print("Assembly number is set to "+assemblyNum)
		if len(sys.argv) >= 3:
			if sys.argv[2] != '-d':
				version = sys.argv[2]
				print("APK version is set to "+version+'\n')
			if '-d' in sys.argv:
				dwnld = True
				print("Только скачиваем APK файлы, не устанавливая")
			else: dwnld = False
			if not version: print("Аргумент версии не получен, установлен на дефолт.")

		loadSettingsJSON()
		downloadZIP()
		unziip_file()
		if not dwnld: install_apk()