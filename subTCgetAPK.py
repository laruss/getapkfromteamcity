from teamcityGetAPK import *

helpUsage ='''
USAGE: teamcityGetAPK.py *arg1* *arg2*
*arg1* - assembly num
*arg2* - prod / debug / preview (version af app)
*additional args*:
 -d - APK won't be installed, just will be downloaded
'''

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
				print("Will only download APK files, not install it")
			else: dwnld = False
			if not version: print("Version argument is not delivered, set to default.")

	main(assNum = assemblyNum, vers=version, dwnld=dwnld)