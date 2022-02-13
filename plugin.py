#		   ZiBlue RfPlayer Plugin
#
#		   Author:	 zaraki673, 2017 - Modified crazymike, 2019
#
#
"""
<plugin key="rfplayer" name="rfplayer" author="zaraki673 (modified: crazymike)" version="2.0.0" wikilink="http://www.domoticz.com/wiki/plugins/Ziblue-RFPlayer.html" externallink="http://rfplayer.com/">
	<params>
		<param field="SerialPort" label="Serial Port" width="150px" required="true" default=""/>
		<param field="Mode1" label="Mac Address" width="200px"/>
		<param field="Mode4" label="Enable Learning Mode" width="75px">
			<options>
				<option label="Enable" value="True"/>
				<option label="Disable" value="False"  default="true" />
			</options>
		</param>
		<param field="Mode5" label="Manual Create devices" width="75px">
			<options>
				<option label="False" value="False"  default="true" />
				<option label="VISONIC - 433" value="1"/>
				<option label="VISONIC - 868" value="2"/>
				<option label="CHACON" value="3"/>
				<option label="DOMIA" value="4"/>
				<option label="X10" value="5"/>
				<option label="X2D - 433 - OPERATING_MODE" value="6"/>
				<option label="X2D - 433 - HEATING_SPEED" value="61"/>
				<option label="X2D - 433 - REGULATION" value="62"/>
				<option label="X2D - 433 - THERMIC_AREA_STATE" value="63"/>
				<option label="X2D - 868 - OPERATING_MODE" value="7"/>
				<option label="X2D - 868 - HEATING_SPEED" value="71"/>
				<option label="X2D - 868 - REGULATION" value="72"/>
				<option label="X2D - 868 - THERMIC_AREA_STATE" value="73"/>
				<option label="X2D - SHUTTER" value="8"/>
				<option label="RTS - SHUTTER" value="11"/>
				<option label="RTS - PORTAL" value="14"/>
				<option label="BLYSS" value="12"/>
				<option label="PARROT" value="13"/>
				<option label="KD101" value="16"/>
			</options>
		</param>
		<param field="Mode2" label="devices ID" width="200px"/>
		<param field="Mode3" label="Area (For X2D)" width="200px"/>
		<param field="Mode6" label="Debug" width="75px">
			<options>
				<option label="None" value="0"  default="true" />
				<option label="Python Only" value="2"/>
				<option label="Basic Debugging" value="62"/>
				<option label="Basic+Messages" value="126"/>
				<option label="Connections Only" value="16"/>
				<option label="Connections+Python" value="18"/>
				<option label="Connections+Queue" value="144"/>
				<option label="All" value="-1"/>
			</options>
		</param>
	</params>
</plugin>
"""
import Domoticz
import datetime
import json
import os
import time

global ReqRcv
global InfoType4SubTypes

InfoType4SubTypes = {}
#                             T/H T  H
InfoType4SubTypes['0x1A2D'] = (1, 1, 1) # THGR122/228/238/268, THGN122/123/132 Thermo+hygro V2
InfoType4SubTypes['0xCA2C'] = (4, 1, 1) # THGR328 Thermo+hygro V2
InfoType4SubTypes['0x0ACC'] = (3, 1, 1) # RTGR328 Thermo+hygro V2
InfoType4SubTypes['0xEA4C'] = (1, 2, 1) # THC238/268, THWR288,THRN122,THN122/132,AW129/131 thermometer V2
InfoType4SubTypes['0x1A3D'] = (6, 1, 1) # THGR918/928, THGRN228, THGN50 Thermo+hygro V2
InfoType4SubTypes['0x5A6D'] = (1, 1, 1) # THGR918N Temp+Pressure V2
InfoType4SubTypes['0xCA48'] = (1, 3, 1) # THWR800 S. pool thermo V3
InfoType4SubTypes['0xFA28'] = (2, 1, 1) # THGR810, THGN800 Thermo+hygro V3 


class BasePlugin:
	enabled = False
	SerialConn = None
	lastHeartbeat = datetime.datetime.now()

	def __init__(self):
		return

	def onStart(self):
		global ReqRcv
		global SerialConn
		if Parameters["Mode6"] != "0":
			Domoticz.Debugging(int(Parameters["Mode6"]))
			DumpConfigToLog()
			with open(Parameters["HomeFolder"]+"Debug.txt", "wt") as text_file:
				print("Started recording message for debug.", file=text_file)
			#Domoticz.Log("Debugger started, use 'telnet 0.0.0.0 4444' to connect")
			#import rpdb
			#rpdb.set_trace()
		if Parameters["Mode5"] != "False": # manual device creation
			if Parameters["Mode5"] =="1": protocol="2" #visonic433
			if Parameters["Mode5"] =="2": protocol="2" #visonic868
			if Parameters["Mode5"] =="3": protocol="4" #chacon
			if Parameters["Mode5"] =="4": protocol="6" #domia
			if Parameters["Mode5"] =="5": protocol="1" #X10
			if Parameters["Mode5"] =="6" or Parameters["Mode5"] =="61" or Parameters["Mode5"] =="62" or Parameters["Mode5"] =="63": protocol="8" #X2D433
			if Parameters["Mode5"] =="7" or Parameters["Mode5"] =="71" or Parameters["Mode5"] =="72" or Parameters["Mode5"] =="73": protocol="8" #X2D868
			if Parameters["Mode5"] =="8": protocol="8" #X2DSHUTTER
			if Parameters["Mode5"] =="11" or Parameters["Mode5"] =="14": protocol="9" #RTS
			if Parameters["Mode5"] =="12": protocol="3" #BLYSS
			if Parameters["Mode5"] =="13": protocol="11" #PARROT
			if Parameters["Mode5"] =="16": protocol="10" #KD101
			id = Parameters["Mode2"]
			Area = Parameters["Mode3"]
			if Parameters["Mode5"] == "4" or Parameters["Mode5"] == "5" or Parameters["Mode5"] == "13" :
				infoType="0"
			if Parameters["Mode5"] == "3" or Parameters["Mode5"] == "12" or Parameters["Mode5"] == "16" :
				infoType="1"
			if Parameters["Mode5"] == "1" or Parameters["Mode5"] == "2" :
				infoType="2"
			if Parameters["Mode5"] == "11" or Parameters["Mode5"] == "14" :
				infoType="3"
			if Parameters["Mode5"] == "6" or Parameters["Mode5"] == "61" or Parameters["Mode5"] == "62" or Parameters["Mode5"] == "63" or Parameters["Mode5"] == "7" or Parameters["Mode5"] == "71" or Parameters["Mode5"] == "72" or Parameters["Mode5"] == "73" :
				infoType="10"
			if Parameters["Mode5"] == "8":
				infoType="11"
			if infoType == "0" or infoType == "1" :
				Options = {"infoType":infoType, "id": str(id), "protocol": str(protocol)}
				stype=0
			if infoType == "2" and Parameters["Mode5"] =="1":
				Options = {"infoType":infoType, "id": str(id), "protocol": str(protocol), "frequency":"433920"}
				stype=0
			if infoType == "2" and Parameters["Mode5"] =="2":
				Options = {"infoType":infoType, "id": str(id), "protocol": str(protocol), "frequency":"868950"}
				stype=0
			if infoType == "3" and Parameters["Mode5"] =="11":                                
				Options = {"infoType": str(infoType), "id": str(id), "protocol": str(protocol), "LevelOffHidden": str("False")}
				stype=18
			if infoType == "3" and Parameters["Mode5"] =="14":
				Options = {"infoType": infoType, "id": str(id), "protocol": str(protocol), "subType": "1", "LevelActions": "||||", "LevelNames": "Off|Left button|Right button", "LevelOffHidden": "False", "SelectorStyle": "0"}
				stype=18
			if infoType == "10" and Parameters["Mode5"] =="6":
				Options = {"infoType":infoType, "id": str(id), "area": str(Area), "function": "2", "protocol": str(protocol), "frequency":"433920", "LevelActions": "|||||||||", "LevelNames": "Off|HG|Eco|Moderat|Medio|Comfort|Assoc", "LevelOffHidden": "False", "SelectorStyle": "0"}
				stype=18
			if infoType == "10" and Parameters["Mode5"] =="61":
				Options = {"infoType":infoType, "id": str(id), "area": str(Area), "function": "1", "protocol": str(protocol), "frequency":"433920"}
				stype=0
			if infoType == "10" and Parameters["Mode5"] =="62":
				Options = {"infoType":infoType, "id": str(id), "area": str(Area), "function": "12", "protocol": str(protocol), "frequency":"433920"}
				stype=0
			if infoType == "10" and Parameters["Mode5"] =="63":
				Options = {"infoType":infoType, "id": str(id), "area": str(Area), "function": "26", "protocol": str(protocol), "frequency":"433920"}
				stype=0
			if infoType == "10" and Parameters["Mode5"] =="7":
				Options = {"infoType":infoType, "id": str(id), "area": str(Area), "function": "2", "protocol": str(protocol), "frequency":"868950", "LevelActions": "|||||||||", "LevelNames": "Off|HG|Eco|Moderat|Medio|Comfort|Assoc", "LevelOffHidden": "False", "SelectorStyle": "0"}
				stype=18
			if infoType == "10" and Parameters["Mode5"] =="71":
				Options = {"infoType":infoType, "id": str(id), "area": str(Area), "function": "1", "protocol": str(protocol), "frequency":"868950"}
				stype=0
			if infoType == "10" and Parameters["Mode5"] =="72":
				Options = {"infoType":infoType, "id": str(id), "area": str(Area), "function": "12", "protocol": str(protocol), "frequency":"868950"}
				stype=0
			if infoType == "10" and Parameters["Mode5"] =="73":
				Options = {"infoType":infoType, "id": str(id), "area": str(Area), "function": "26", "protocol": str(protocol), "frequency":"868950"}
				stype=0
			if infoType == "11" :
				Options = {"infoType":infoType, "id": str(id), "protocol": str(protocol), "subType": "1", "LevelActions": "|||", "LevelNames": "Off|On|Stop", "LevelOffHidden": "False", "SelectorStyle": "0"}
				stype=18		
			IsCreated=False
			x=0
			nbrdevices=1
			Domoticz.Debug("Options to find or set : " + str(Options))
			#########check if devices exist ####################
			for x in Devices:
				DOptions = Devices[x].Options
				if {k: DOptions.get(k, None) for k in ('id', 'protocol', 'infoType', 'area', 'function')} == {k: Options.get(k, None) for k in ('id', 'protocol', 'infoType', 'area', 'function')}:
					IsCreated = True
					nbrdevices=x
					#Domoticz.Log("Devices already exist. Unit=" + str(x))
					Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
			########### create device if not found ###############
			if IsCreated == False :
				nbrdevices=FreeUnit()
				if infoType =="3" :
					Domoticz.Device(Name="RTS - " + Parameters["Mode2"],  Unit=nbrdevices, TypeName="Selector Switch", Switchtype=15, Description="Options:id=" + Parameters["Mode2"] + ";infoType=3;protocol=RTS;OtherId=", Used=1, Options=Options).Create()
				elif infoType=="10" and Options['function']=="2" :
					Domoticz.Device(Name="X2DELEC Switch - Area " + Options['area'],  Unit=nbrdevices, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
				else :
					Domoticz.Device(Name="Manual Switch - " + Parameters["Mode2"], Unit=nbrdevices, Type=16, Switchtype=stype).Create()
				Devices[nbrdevices].Update(nValue =0,sValue = "0",Options = Options)
			Domoticz.Log("Plugin has " + str(len(Devices)) + " devices associated with it.")
		#Domoticz.Transport("Serial", Parameters["SerialPort"], Baud=115200)
		#Domoticz.Protocol("None")  # None,XML,JSON,HTTP
		#Domoticz.Connect()
		CheckRFPControl();
		SerialConn = Domoticz.Connection(Name="RfP1000", Transport="Serial", Protocol="None", Address=Parameters["SerialPort"], Baud=115200)
		SerialConn.Connect()
		ReqRcv=''
		return
	
	# present de base 
	def onStop(self):
		#Domoticz.disconnect()
		Domoticz.Log("Plugin is stopping.")

	# present de base 
	def onConnect(self, Connection, Status, Description):
		global isConnected
		if (Status == 0):
			isConnected = True
			Domoticz.Status("Connected successfully to: "+Parameters["SerialPort"])
			# Run RFPlayer configuration
			RFpConf()
		else:
			Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Parameters["SerialPort"])
			Domoticz.Debug("Failed to connect ("+str(Status)+") to: "+Parameters["SerialPort"]+" with error: "+Description)
		return True

	# present de base 
	def onMessage(self, Connection, Data):
		global Tmprcv
		global ReqRcv
		#global ModeLastReceive
		###########################################
		Tmprcv=Data.decode(errors='ignore')
		################## check if more than 1 sec between two message, if yes clear ReqRcv
		lastHeartbeatDelta = (datetime.datetime.now()-self.lastHeartbeat).total_seconds()
		if (lastHeartbeatDelta > 1):
			ReqRcv=''
			Domoticz.Debug("Last Message was "+str(lastHeartbeatDelta)+" seconds ago, Message clear")
		#Wait not end of data '\r'
		if Tmprcv.endswith('\r',0,len(Tmprcv))==False :
			ReqRcv+=Tmprcv
		else : # while end of data is receive
			ReqRcv+=Tmprcv
			########## TODO : verifier si une trame ZIA n est pas en milieu de message (2 messages collés ou perturbation + message accollés)
			if ReqRcv.startswith("ZIA--"):
				#ModeLastReceive ="CONF"
				#Domoticz.Debug(ReqRcv)
				ReadConf(ReqRcv)
				ReqRcv=''
			if ReqRcv.startswith("ZIA33"):
				#ModeLastReceive ="DATA"
				#Domoticz.Debug(ReqRcv)
				ReadData(ReqRcv)
				ReqRcv=''
			if ReqRcv.startswith("ZIA55"):
				#ModeLastReceive ="TRACE"
				#Domoticz.Log("----Mode Trace----")
				#Domoticz.Log(ReqRcv)
				ReadTrace(ReqRcv)
				ReqRcv=''
				
			if ReqRcv.startswith("ZIA00"):
				#ModeLastReceive ="TRACE"
				Domoticz.Log("----Mode 00----")
				Domoticz.Log(ReqRcv)
				ReadZIA00(ReqRcv)
				ReqRcv=''
			if ReqRcv.startswith("ZIA11"):
				#ModeLastReceive ="TRACE"
				Domoticz.Log("----Mode 11----")
				Domoticz.Log(ReqRcv)
				ReadZIA11(ReqRcv)
				ReqRcv=''
			if ReqRcv.startswith("ZIA22"):
				#ModeLastReceive ="TRACE"
				Domoticz.Log("----Mode 22----")
				Domoticz.Log(ReqRcv)
				ReadZIA22(ReqRcv)
				ReqRcv=''
			if ReqRcv.startswith("ZIA44"):
				#ModeLastReceive ="TRACE"
				Domoticz.Log("----Mode 44----")
				Domoticz.Log(ReqRcv)
				ReadZIA44(ReqRcv)
				ReqRcv=''
			if ReqRcv.startswith("ZIA66"):
				#ModeLastReceive ="TRACE"
				Domoticz.Log("----Mode 66----")
				Domoticz.Log(ReqRcv)
				ReadZIA66(ReqRcv)
				ReqRcv=''
				
			#if ReqRcv.startswith("ZIA"):
				#ModeLastReceive ="TRACE"
			#Domoticz.Log("----Mode Trace----")
			#Domoticz.Log(str(ReqRcv))
			#ReqRcv=''
			
		self.lastHeartbeat = datetime.datetime.now()
		return

	# present de base action executer qd une commande est passé a Domoticz
	def onCommand(self, Unit, Command, Level, Hue):
		if Parameters["Mode6"] != "0":
			Domoticz.Log("SendtoRfplayer - Call: Unit=" + str(Unit) + " , Command=" + str(Command) + " , Level=" + str(Level) + " , Hue=" + str(Hue))
		SendtoRfplayer(Unit, Command, Level, Hue)
		return True

	def onHeartbeat(self):
	###########
		#infotype0  ==> ok
		#ReqRcv = 'ZIA33{ "frame" :{"header": {"frameType": "0", "cluster": "0", "dataFlag": "0", "rfLevel": "-44", "floorNoise": "-99", "rfQuality": "10", "protocol": "6", "protocolMeaning": "DOMIA", "infoType": "0", "frequency": "433920"},"infos": {"subType": "0", "id": "235", "subTypeMeaning": "OFF", "idMeaning": "O12"}}}'
	###########
		#infotype1 ==> ok
		#ReqRcv='ZIA33{ "frame" :{"header": {"frameType": "0", "cluster": "0", "dataFlag": "0", "rfLevel": "-72", "floorNoise": "-106", "rfQuality": "8", "protocol": "4", "protocolMeaning": "CHACON", "infoType": "1", "frequency": "433920"},"infos": {"subType": "1", "id": "424539265", "subTypeMeaning": "ON"}}}'
	###########
		#infotype2
		#==> ok
		#ReqRcv='ZIA33{ "frame" :{"header": {"frameType": "0", "cluster": "0", "dataFlag": "0", "rfLevel": "-51", "floorNoise": "-103", "rfQuality": "10", "protocol": "2", "protocolMeaning": "VISONIC", "infoType": "2", "frequency": "433920"},"infos": {"subType": "0", "subTypeMeaning": "Detector/Sensor", "id": "335547184", "qualifier": "3", "qualifierMeaning": { "flags": ["Tamper","Alarm"]}}}}'
		#ReqRcv='ZIA33{ "frame" :{"header": {"frameType": "0", "cluster": "0", "dataFlag": "0", "rfLevel": "-55", "floorNoise": "-102", "rfQuality": "10", "protocol": "2", "protocolMeaning": "VISONIC", "infoType": "2", "frequency": "433920"},"infos": {"subType": "0", "subTypeMeaning": "Detector/Sensor", "id": "2034024048", "qualifier": "1", "qualifierMeaning": { "flags": ["Tamper"]}}}}'
		#OK ==>  protocol = 3
		#ReqRcv='ZIA33{ "frame" :{"header": {"frameType": "0", "cluster": "0", "dataFlag": "0", "rfLevel": "-66", "floorNoise": "-106", "rfQuality": "10", "protocol": "3", "protocolMeaning": "BLYSS", "infoType": "2", "frequency": "433920"},"infos": {"subType": "0", "subTypeMeaning": "Detector/Sensor", "id": "256292321", "qualifier": "0"}}}'
		#ReqRcv='ZIA33{ "frame" :{"header": {"frameType": "0", "cluster": "0", "dataFlag": "1", "rfLevel": "-84", "floorNoise": "-106", "rfQuality": "5", "protocol": "2", "protocolMeaning": "VISONIC", "infoType": "2", "frequency": "868950"},"infos": {"subType": "0", "subTypeMeaning": "Detector/Sensor", "id": "2039708784", "qualifier": "0", "qualifierMeaning": { "flags": []}}}}'
		###########
		#infotype3 RTS Subtype0 ==> ok  // 
		#ReqRcv='ZIA33{ "frame" :{"header": {"frameType": "0", "cluster": "0", "dataFlag": "0", "rfLevel": "-64", "floorNoise": "-103", "rfQuality": "9", "protocol": "9", "protocolMeaning": "RTS", "infoType": "3", "frequency": "433920"},"infos": {"subType": "0", "subTypeMeaning": "Shutter", "id": "14813191", "qualifier": "4", "qualifierMeaning": { "flags": ["My"]}}}}'
	###########
		#infotype4
		#ReqRcv='ZIA33{ "frame" :{"header": {"frameType": "0", "cluster": "0", "dataFlag": "0", "rfLevel": "-86", "floorNoise": "-100", "rfQuality": "3", "protocol": "5", "protocolMeaning": "OREGON", "infoType": "4", "frequency": "433920"},"infos": {"subType": "0", "id_PHY": "0xEA4C", "id_PHYMeaning": "THC238/268,THWR288,THRN122,THN122/132,AW129/131", "adr_channel": "21762", "adr": "85", "channel": "2", "qualifier": "33", "lowBatt": "1", "measures" : [{"type" : "temperature", "value" : "-17.8", "unit" : "Celsius"}, {"type" : "hygrometry", "value" : "0", "unit" : "%"}]}}}'
		#ReqRcv='ZIA33{ "frame" :{"header": {"frameType": "0", "cluster": "0", "dataFlag": "0", "rfLevel": "-46", "floorNoise": "-105", "rfQuality": "10", "protocol": "5", "protocolMeaning": "OREGON", "infoType": "4", "frequency": "433920"},"infos": {"subType": "0", "id_PHY": "0x1A2D", "id_PHYMeaning": "THGR122/228/238/268,THGN122/123/132", "adr_channel": "63492", "adr": "248", "channel": "4", "qualifier": "32", "lowBatt": "0", "measures" : [{"type" : "temperature", "value" : "+20.3", "unit" : "Celsius"}, {"type" : "hygrometry", "value" : "41", "unit" : "%"}]}}}'
		#ReqRcv='ZIA33{ "frame" :{"header": {"frameType": "0", "cluster": "0", "dataFlag": "0", "rfLevel": "-77", "floorNoise": "-100", "rfQuality": "5", "protocol": "5", "protocolMeaning": "OREGON", "infoType": "4", "frequency": "433920"},"infos": {"subType": "0", "id_PHY": "0xFA28", "id_PHYMeaning": "THGR810", "adr_channel": "64513", "adr": "252", "channel": "1", "qualifier": "48", "lowBatt": "0", "measures" : [{"type" : "temperature", "value" : "+21.0", "unit" : "Celsius"}, {"type" : "hygrometry", "value" : "35", "unit" : "%"}]}}}'
	###########
		#infotype5
	###########
		#infotype6
	###########
		#infotype7
	###########
		#infotype8 OWL ==> ok
		#ReqRcv='ZIA33{ "frame" :{"header": {"frameType": "0", "cluster": "0", "dataFlag": "0", "rfLevel": "-85", "floorNoise": "-97", "rfQuality": "3", "protocol": "7", "protocolMeaning": "OWL", "infoType": "8", "frequency": "433920"},"infos": {"subType": "0", "id_PHY": "0x0002", "id_PHYMeaning": "CM180", "adr_channel": "35216",  "adr": "2201",  "channel": "0",  "qualifier": "1",  "lowBatt": "1", "measures" : [{"type" : "energy", "value" : "871295", "unit" : "Wh"}, {"type" : "power", "value" : "499", "unit" : "W"}]}}}'
	###########
		#infotype9
	###########
		#infotype10
	###########
		#infotype11 ==> ok
		#ReqRcv='ZIA33{ "frame" :{"header": {"frameType": "0", "cluster": "0", "dataFlag": "1", "rfLevel": "-75", "floorNoise": "-99", "rfQuality": "6", "protocol": "8", "protocolMeaning": "X2D", "infoType": "11", "frequency": "868350"},"infos": {"subType": "0", "subTypeMeaning": "Detector/Sensor", "id": "2888689920", "qualifier": "10", "qualifierMeaning": { "flags": ["Alarm","Supervisor/Alive"]}}}}'
		#ReqRcv='ZIA33{ "frame" :{"header": {"frameType": "0", "cluster": "0", "dataFlag": "1", "rfLevel": "-57", "floorNoise": "-106", "rfQuality": "10", "protocol": "8", "protocolMeaning": "X2D", "infoType": "11", "frequency": "868350"},"infos": {"subType": "0", "subTypeMeaning": "Detector/Sensor", "id": "1112729857", "qualifier": "2", "qualifierMeaning": { "flags": ["Alarm"]}}}}'
		#ReqRcv='ZIA33{ "frame" :{"header": {"frameType": "0", "cluster": "0", "dataFlag": "1", "rfLevel": "-57", "floorNoise": "-106", "rfQuality": "10", "protocol": "8", "protocolMeaning": "X2D", "infoType": "11", "frequency": "868350"},"infos": {"subType": "0", "subTypeMeaning": "Detector/Sensor", "id": "1112729857", "qualifier": "0", "qualifierMeaning": { "flags": []}}}}'
		###########
		
		
		#ReadData(ReqRcv)
		global SerialConn
		if (SerialConn.Connected() != True):
			SerialConn.Connect()
		return True


global _plugin
_plugin = BasePlugin()

def onStart():
	global _plugin
	_plugin.onStart()

def onStop():
	global _plugin
	_plugin.onStop()

def onConnect(Connection, Status, Description):
	global _plugin
	_plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
	global _plugin
	_plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
	global _plugin
	_plugin.onCommand(Unit, Command, Level, Hue)

def onHeartbeat():
	global _plugin
	_plugin.onHeartbeat()

	# Generic helper functions
def DumpConfigToLog():
	for x in Parameters:
		if Parameters[x] != "":
			Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
	Domoticz.Debug("Device count: " + str(len(Devices)))
	for x in Devices:
		Domoticz.Debug("Device:		   " + str(x) + " - " + str(Devices[x]))
		Domoticz.Debug("Device ID:	   '" + str(Devices[x].ID) + "'")
		Domoticz.Debug("Device Name:	 '" + Devices[x].Name + "'")
		Domoticz.Debug("Device nValue:	" + str(Devices[x].nValue))
		Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
		Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
		Domoticz.Debug("Options:         '" + str(Devices[x].Options) + "'")
	return

def UpdateDevice(Unit, nValue, sValue, Image, SignalLevel, BatteryLevel):
	# Make sure that the Domoticz device still exists (they can be deleted) before updating it 
	if (Unit in Devices):
		if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue) or (Devices[Unit].Image != Image) or (Devices[Unit].SignalLevel != SignalLevel) or (Devices[Unit].BatteryLevel != BatteryLevel) :
			Devices[Unit].Update(nValue, str(sValue),Image, SignalLevel, BatteryLevel)
			Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' SignalLevel:"+str(SignalLevel)+" batteryLevel:'"+str(BatteryLevel)+"%' ("+Devices[Unit].Name+")")
	return

def RFpConf():
	###################Configure Rfplayer ~##################
	'''
	lineinput='ZIA++REPEATER - *'
	SerialConn.Send(bytes(lineinput + '\n\r','utf-8'))
	lineinput='ZIA++RECEIVER - * + CHACON OREGONV2 OREGONV3/OWL X2D'
	SerialConn.Send(bytes(lineinput + '\n\r','utf-8'))
	'''
	lineinput='ZIA++RECEIVER + *'
	SerialConn.Send(bytes(lineinput + '\n\r','utf-8'))
	
	lineinput='ZIA++FREQ H 868350'
	SerialConn.Send(bytes(lineinput + '\n\r','utf-8'))
	lineinput='ZIA++SELECTIVITY H 1'
	SerialConn.Send(bytes(lineinput + '\n\r','utf-8'))
	lineinput='ZIA++SENSIBILITY H 1'
	SerialConn.Send(bytes(lineinput + '\n\r','utf-8'))
	lineinput='ZIA++RFLINKTRIGGER H 4'
	SerialConn.Send(bytes(lineinput + '\n\r','utf-8'))
	lineinput='ZIA++DSPTRIGGER H 4'
	SerialConn.Send(bytes(lineinput + '\n\r','utf-8'))
	
	#'''
	lineinput='ZIA++FORMAT JSON'
	SerialConn.Send(bytes(lineinput + '\n\r','utf-8'))
	if Parameters["Mode1"] != "" :
		lineinput='ZIA++SETMAC ' + Parameters["Mode1"]
		SerialConn.Send(bytes(lineinput + '\n\r','utf-8'))
	lineinput='ZIA++TRACE -* +RFLINK +RECEIVER'
	#Domoticz.Log(lineinput);
	SerialConn.Send(bytes(lineinput + '\n\r','utf-8'))
	#lineinput='ZIA++FORMAT RFLINK BINARY'
	#Domoticz.Log(lineinput);
	#SerialConn.Send(bytes(lineinput + '\n\r','utf-8'))
	lineinput='ZIA++STATUS JSON'
	SerialConn.Send(bytes(lineinput + '\n\r','utf-8'))
	#return
	
	

def ReadConf(ReqRcv):
	global RfPmac
	Domoticz.Debug(ReqRcv)
	ReqRcv=ReqRcv.replace("ZIA--", "")
	DecData = json.loads(ReqRcv)
	if 'systemStatus' in DecData :
		RfPmac = DecData['systemStatus']['info'][2]['v']
		Domoticz.Log('rfp1000 mac :' + str(RfPmac))
	#return RfPmac

def ReadData(ReqRcv):
	##############################################################################################################
	# decoding data from RfPlayer 
	##############################################################################################################
	if Parameters["Mode6"] != "0":
		Domoticz.Debug("ReadData - " + ReqRcv)
	ReqRcv=ReqRcv.replace("ZIA33", "")
	try:
		DecData = json.loads(ReqRcv)
		infoType = DecData['frame']['header']['infoType']
		if Parameters["Mode6"] != "0":
			Domoticz.Debug("infoType : " + infoType)
		##############################################################################################################
		#####################################Frame infoType 0					ON/OFF
		##############################################################################################################
		if infoType == "0":
			DecodeInfoType0(DecData, infoType)
		##############################################################################################################
		#####################################Frame infoType 1					ON/OFF   error in API receive id instead of id_lsb and id_msb
		##############################################################################################################
		if infoType == "1":
			DecodeInfoType1(DecData, infoType)
		##############################################################################################################
		#####################################Frame infoType 2					Visonic###############################
		#############http://www.el-sys.com.ua/wp-content/uploads/MCR-300_UART_DE3140U0.pdf ###########################
		###########http://cpansearch.perl.org/src/BEANZ/Device-RFXCOM-1.142010/lib/Device/RFXCOM/Decoder/Visonic.pm ##
		#############https://forum.arduino.cc/index.php?topic=289554.0 ###############################################
		##############################################################################################################
		if infoType == "2":
			DecodeInfoType2(DecData, infoType)
		##############################################################################################################
		#####################################Frame infoType 3				RTS	 ##################################
		##############################################################################################################
		if infoType == "3":
			DecodeInfoType3(DecData, infoType)
		##############################################################################################################
		#####################################Frame infoType 4		Oregon thermo/hygro sensors  #####################
		#############http://www.connectingstuff.net/blog/encodage-protocoles-oregon-scientific-sur-arduino/###########
		##############################################################################################################
		if infoType == "4":
			DecodeInfoType4(DecData, infoType)
		##############################################################################################################
		#####################################Frame infoType 5		Oregon thermo/hygro/pressure sensors  ############
		##############################################################################################################
		if infoType == "5":
			DecodeInfoType5(DecData, infoType)
		##############################################################################################################
		#####################################Frame infoType 6		Oregon Wind sensors  #############################
		#############http://www.connectingstuff.net/blog/encodage-protocoles-oregon-scientific-sur-arduino/###########
		##############################################################################################################
		if infoType == "6":
			DecodeInfoType6(DecData, infoType)
		##############################################################################################################
		#####################################Frame infoType 7		Oregon UV sensors  ############
		##############################################################################################################
		if infoType == "7":
			DecodeInfoType7(DecData, infoType)
		##############################################################################################################
		#####################################Frame infoType 8		OWL Energy/power sensors  ############
		##############################################################################################################
		if infoType == "8":
			DecodeInfoType8(DecData, infoType)
		##############################################################################################################
		#####################################Frame infoType 9		Oregon Rain sensors  ############
		##############################################################################################################
		if infoType == "9":
			DecodeInfoType9(DecData, infoType)
		##############################################################################################################
		#####################################Frame infoType 10		Thermostats  X2D protocol ########################
		##############################################################################################################
		if infoType == "10":
			DecodeInfoType10(DecData, infoType)
		##############################################################################################################
		#####################################Frame infoType 11		 Alarm X2D protocol / Shutter ####################
		##############################################################################################################
		if infoType == "11":
			DecodeInfoType11(DecData, infoType)
	except:
		Domoticz.Log("Error while reading JSON Infotype")
		Domoticz.Debug("Debug : Error Decoding/Reading  " + ReqRcv)
		if Parameters["Mode6"] == "Debug":
			with open(Parameters["HomeFolder"]+"Debug.txt", "at") as text_file:
				print(ReqRcv, file=text_file)
		ReqRcv=""
		return
		
def ReadTrace(ReqRcv):
	##############################################################################################################
	# decoding trace from RfPlayer 
	##############################################################################################################
	#Domoticz.Log("Trace - " + ReqRcv)
	ReqRcv=ReqRcv.replace("ZIA55 ", "")
	
	ListeSamples=[]
	ListeTimes0=[]
	ListeTimes1=[]
	ListePulses=[]
	Frequency=0
	Level=0
	Noise=0
	SamplesCount=0
	
	for line in ReqRcv.splitlines():
		if line.startswith("RFLINK REC"):
			# RFLINK REC frame F=433920Khz level=-54dBm noise=-85dBm Samples number=317 list below= level:time(us)
			ParamList=line.split(" ")
			Frequency=ParamList[3].split("=")[1]		
			Level=ParamList[4].split("=")[1]			
			Noise=ParamList[5].split("=")[1]			
			SamplesCount=ParamList[7].split("=")[1]			
		else:
			#RFLINK line 0= 0:0, 1:360, 0:640, 1:360, 0:1920, 1:520, 0:3920, 1:480, 0:1920, 1:520, 0:3880, 1:520, 0:3920, 1:440, 0:2000, 1:480,
			#RFLINK line 33= 0:2000, 1:560, 0:7720, 1:560, 0:0.
			if line.startswith("RFLINK line"):
				#Domoticz.Log("Ligne : " + line)
				for SampleItem in line.split("=")[1].split(","):
					if SampleItem.strip(" ") != "":
						ListeSamples.append(SampleItem.strip(" ").replace(".",""))
						Item=SampleItem.strip(" ").replace(".","").split(":")
						ListePulses.append(int(Item[1]))
						if (int(Item[1]) > 0):
							if (int(Item[0]) == 0) :
								try:
									ListeTimes0.index(int(Item[1]))
								except Exception:
									ListeTimes0.append(int(Item[1]))
							if (int(Item[0]) == 1) :
								try:
									ListeTimes1.index(int(Item[1]))
								except Exception:
									ListeTimes1.append(int(Item[1]))
			else:
				if line != "" :
					if Parameters["Mode6"] != "0":
						Domoticz.Log(line)
	
	#if ((len(ListeSamples)-2) == int(SamplesCount)):
	ListeTimes0.sort()
	ListeTimes1.sort()
	#Domoticz.Log("Samples identified:"+str(len(ListeSamples)))
	if Parameters["Mode6"] != "0":
		Domoticz.Log("-------------Trace-------------")
		Domoticz.Log("Frequency="+str(Frequency))
		Domoticz.Log("Level="+str(Level))
		Domoticz.Log("Noise="+str(Noise))
		Domoticz.Log("Samples="+str(SamplesCount))
	DebugListeListTimes="";
	for Time in ListeTimes0:
		if(DebugListeListTimes != ""):
			DebugListeListTimes = DebugListeListTimes + ","
		DebugListeListTimes = DebugListeListTimes + str(Time)
	if Parameters["Mode6"] != "0":
		Domoticz.Log("Times(0)"+DebugListeListTimes)
	DebugListeListTimes="";
	for Time in ListeTimes1:
		if(DebugListeListTimes != ""):
			DebugListeListTimes = DebugListeListTimes + ","
		DebugListeListTimes = DebugListeListTimes + str(Time)
	if Parameters["Mode6"] != "0":
		Domoticz.Log("Times(1)"+DebugListeListTimes)
	#FileName="Trace_"+Frequency+"_"+Level+"_"+Noise+"_"+SamplesCount+".csv"
	
	Prefixe=""
	
	if ((int(SamplesCount) >= 74) & (int(SamplesCount) <= 78) ) :
		Prefixe="Alecto V4-"
		try :
			Plugin_032(int(SamplesCount),ListePulses)
		except :
			Prefixe=""
	FileName=Prefixe+"Trace_"+str(Frequency)+"_"+str(Level)+"-Bits.csv"
	TraceFile = open(FileName,"w")
	for IndexSample in range(len(ListeSamples)):
		Value=ListeSamples[IndexSample].split(":")[0]
		Time=ListeSamples[IndexSample].split(":")[1]
		#TraceFile.write(ListeSamples[IndexSample].replace(":",";")+"\r\n")
		for x in range(0,(int(Time) // 10)):
			TraceFile.write(Value+"\r\n")
	TraceFile.close()
	os.chmod(FileName, 0o777)
	FileName=Prefixe+"Trace_"+str(Frequency)+"_"+str(Level)+"-Signal.csv"
	TraceFile = open(FileName,"w")
	for IndexSample in range(len(ListeSamples)):
		TraceFile.write(ListeSamples[IndexSample].replace(":",";")+"\r\n")
	TraceFile.close()
	os.chmod(FileName, 0o777)
	
	#else:
	#	Domoticz.Log("Trace not good : RFPlayer says:" + str(SamplesCount) + " samples ,we found:"+str(len(ListeSamples)-2)+" samples !")
	#for IndexSample in range(len(ListeSamples)):
	#	Domoticz.Log(ListeSamples[IndexSample])
	
def ReadZIA00(ReqRcv):
	##############################################################################################################
	# decoding trace from RfPlayer 
	##############################################################################################################
	Domoticz.Log("Trace - " + ReqRcv)
	ReqRcv=ReqRcv.replace("ZIA00 ", "")

def ReadZIA11(ReqRcv):
	##############################################################################################################
	# decoding trace from RfPlayer 
	##############################################################################################################
	Domoticz.Log("Trace - " + ReqRcv)
	ReqRcv=ReqRcv.replace("ZIA11 ", "")

def ReadZIA22(ReqRcv):
	##############################################################################################################
	# decoding trace from RfPlayer 
	##############################################################################################################
	Domoticz.Log("Trace - " + ReqRcv)
	ReqRcv=ReqRcv.replace("ZIA22 ", "")

def ReadZIA44(ReqRcv):
	##############################################################################################################
	# decoding trace from RfPlayer 
	##############################################################################################################
	Domoticz.Log("Trace - " + ReqRcv)
	ReqRcv=ReqRcv.replace("ZIA44 ", "")

def ReadZIA66(ReqRcv):
	##############################################################################################################
	# decoding trace from RfPlayer 
	##############################################################################################################
	Domoticz.Log("Trace - " + ReqRcv)
	ReqRcv=ReqRcv.replace("ZIA66 ", "")

def SendtoRfplayer(Unit, Command, Level, Hue):
	bErreur = False
	Options=Devices[Unit].Options
	if Parameters["Mode6"] != "0":
		Domoticz.Debug("SendtoRfplayer - Call: Unit=" + str(Unit) + " , Command=" + str(Command) + " , Level=" + str(Level) + " , Hue=" + str(Hue))
		Domoticz.Debug("SendtoRfplayer - Options found in DB: " + str(Devices[Unit].Options) + " for devices unit " + str(Unit))
		Domoticz.Debug("SendtoRfplayer - Description found in DB: " + str(Devices[Unit].Description) + " for devices unit " + str(Unit))
		Domoticz.Debug("SendtoRfplayer - Switchtype found in DB: " + str(Devices[Unit].SwitchType) + " for devices unit " + str(Unit))
	
	if Unit==255 :
		Domoticz.Debug("Controle")
		if Level==10:
			lineinput='ZIA++STATUS JSON'
			SerialConn.Send(bytes(lineinput + '\n\r','utf-8'))
	else:
		DOptions=Devices[Unit].Options
		
		protocol=""
		infoType=""
		id=""
		assocMode=""
		
		#if hasattr(Devices[Unit].Options, 'infoType'):
		infoType = DOptions['infoType']
		#if hasattr(Devices[Unit].Options, 'protocol'):
		protocol=Devices[Unit].Options['protocol']
		#if hasattr(Devices[Unit].Options, 'id'):
		id=Devices[Unit].Options['id']
			
		
		for line in Devices[Unit].Description.splitlines():
			if line.find("Options") != -1:
				line=line.split(":")[1]
				for Option in line.split(";"):
					if Parameters["Mode6"] != "0":
						Domoticz.Log("SendtoRfplayer - Option: " + Option)
					NameVar=Option.split("=")[0]
					ValVar=Option.split("=")[1]
					if NameVar=="id":
						id=ValVar
					elif NameVar=="infoType":
						infoType=ValVar
					elif NameVar=="protocol":
						protocol=ValVar
					elif NameVar=="assocMode":
						assocMode=ValVar
		
		if Parameters["Mode6"] != "0":				
			Domoticz.Log("SendtoRfplayer - " + id + " | " + infoType + " | " + protocol) 
		
		lineinput=""
		if bErreur == False :
			if protocol =="1": protocol="X10"
			if protocol =="2": 
				frequency=Options['frequency']
				if frequency == "433920":
					protocol="VISONIC433"
				if frequency == "868950":
					protocol="VISONIC868"
			if protocol =="3": protocol="BLYSS"
			if protocol =="4": protocol="CHACON"
			if protocol =="6": protocol="DOMIA"
			if protocol =="8" and infoType == "10":
				frequency=Options['frequency']
				if frequency == "433920":
					protocol="X2D433"
				if frequency == "868950":
					protocol="X2D868"
			if protocol =="8" and infoType == "11":
				protocol="X2DSHUTTER"
			if protocol =="9": protocol="RTS"
			if protocol =="10": protocol="KD101"
			if protocol =="11": protocol="PARROT"

			if infoType == "0" and  protocol == "PARROT":
				#id=Options['id']
				lineinput='ZIA++' + str(Command.upper()) + " " + protocol + " " + id
				SerialConn.Send(bytes(lineinput + '\n\r','utf-8'))
				if Command == "On":
					Devices[Unit].Update(nValue =1,sValue = "on")
				if Command == "Off":
					Devices[Unit].Update(nValue =0,sValue = "off")
					
			if infoType == "0" and protocol != "PARROT":
				#id=Options['id']
				lineinput='ZIA++' + str(Command.upper()) + " " + protocol + " ID " + id
				SerialConn.Send(bytes(lineinput + '\n\r','utf-8'))
				if Command == "On":
					Devices[Unit].Update(nValue =1,sValue = "on")
				if Command == "Off":
					Devices[Unit].Update(nValue =0,sValue = "off")
					
			if infoType == "1" or infoType == "2":
				id=Options['id']
				lineinput='ZIA++' + str(Command.upper()) + " " + protocol + " ID " + id
				SerialConn.Send(bytes(lineinput + '\n\r','utf-8'))
				if Command == "On":
					Devices[Unit].Update(nValue =1,sValue = "on")
				if Command == "Off":
					Devices[Unit].Update(nValue =0,sValue = "off")
						#Devices[Unit].Update(nValue =0,sValue = "off")
				
			if infoType == "3" :
				#id=Options['id']			
				#qualifier=""
				#DeviceTypeSwitch: 0,
				#DeviceTypeDoorbell: 1,
				#DeviceTypeContact: 2,
				#DeviceTypeBlinds: 3,
				#DeviceTypeSmoke: 5,
				#DeviceTypeBlindsInverted: 6,
				#DeviceTypeDimmer: 7,
				#DeviceTypeMotion: 8,
				#DeviceTypePushOn: 9,
				#DeviceTypeDoorContact: 11,
				#DeviceTypeBlindsPercentage: 13,
				#DeviceTypeBlindsVenetianUS: 14,
				#DeviceTypeBlindsVenetianEU: 15,
				#DeviceTypeBlindsPercentageInverted: 16,
				#DeviceTypeMedia: 17, // Only supported as on/off switch at the moment.
				#DeviceTypeSelector: 18,
				#DeviceTypeDoorLock: 19,
				#DeviceTypeDoorLockInverted: 20,
				lineinput=""
				if Devices[Unit].SwitchType == 15 :
					#Venitian blinds EU
					if assocMode == "1" :
						lineinput='ZIA++' + str("ASSOC " + protocol + " " + id)
						Devices[Unit].Update(nValue = 17, sValue="50");
					else :
						if Command == "Off":
							lineinput='ZIA++' + str("ON " + protocol + " " + id )
							Devices[Unit].Update(nValue =0,sValue="100");
						elif Command == "On":
							lineinput='ZIA++' + str("OFF " + protocol + " " + id )
							Devices[Unit].Update(nValue =1,sValue="0");
						else :
							lineinput='ZIA++' + str("DIM " + protocol + " " + id + " %50" )
							Devices[Unit].Update(nValue = 17, sValue="50");
				if Devices[Unit].SwitchType == 13 :
					#Blinds percentage
					if assocMode == "1" :
						lineinput='ZIA++' + str("ASSOC " + protocol + " " + id)
						Devices[Unit].Update(nValue = 17, sValue="50");
					else :
						if Command == "Off":
							lineinput='ZIA++' + str("ON " + protocol + " " + id )
							Devices[Unit].Update(nValue =0,sValue="100");
						elif Command == "On":
							lineinput='ZIA++' + str("OFF " + protocol + " " + id )
							Devices[Unit].Update(nValue =1,sValue="0");
						elif Command== "Set Level" :
							if Level <= 1 :
								lineinput='ZIA++' + str("ON " + protocol + " " + id )
								Devices[Unit].Update(nValue = 0, sValue="100");
							elif Level >= 99 :
								lineinput='ZIA++' + str("OFF " + protocol + " " + id )
								Devices[Unit].Update(nValue = 1, sValue="0");
							else :
								lineinput='ZIA++' + str("DIM " + protocol + " " + id + " %" + str(Level) )
								Devices[Unit].Update(nValue = 17, sValue=str(Level));
							
				if Devices[Unit].SwitchType == 16 :
					if assocMode == "1" :
						lineinput='ZIA++' + str("ASSOC " + protocol + " " + id)
						Devices[Unit].Update(nValue = 17, sValue="50");
					else :
						if Command == "Off":
							lineinput='ZIA++' + str("ON " + protocol + " " + id )
							Devices[Unit].Update(nValue =0,sValue="off");
						elif Command == "On":
							lineinput='ZIA++' + str("OFF " + protocol + " " + id )
							Devices[Unit].Update(nValue =1,sValue="on");
						else :
							lineinput='ZIA++' + str("DIM " + protocol + " " + id + " %50" )
							Devices[Unit].Update(nValue = 17, sValue="50");
				elif Devices[Unit].SwitchType == 18 :
					qualifier=Devices[Unit].Options['subType']
					if qualifier=="0":
					###start MAj from Deennoo
						if Level == 0 and Command != "On" :
							lineinput='ZIA++' + str("OFF " + protocol + " ID " + id + " QUALIFIER " + qualifier)
						if Level == 10 :
							lineinput='ZIA++' + str("DIM " + protocol + " ID " + id + " %50" + " QUALIFIER " + qualifier)
						if Level == 20 or Command == "Off" :
							lineinput='ZIA++' + str("ON " + protocol + " ID " + id + " QUALIFIER " + qualifier)
						if Level == 30 :
							lineinput='ZIA++' + str("ASSOC " + protocol + " ID " + id + " QUALIFIER " + qualifier)
					###End MAj from Deennoo
					if qualifier=="1":
						if Level == 10 :
							lineinput='ZIA++' + str("ON " + protocol + " ID " + id + " QUALIFIER " + qualifier)
						if Level == 20 :
							lineinput='ZIA++' + str("OFF " + protocol + " ID " + id + " QUALIFIER " + qualifier)
						if Level == 30 :
							lineinput='ZIA++' + str("ASSOC " + protocol + " ID " + id + " QUALIFIER " + qualifier)
				if lineinput != "" :
					if Parameters["Mode6"] != "0":
						Domoticz.Log(lineinput)
					SerialConn.Send(bytes(lineinput + '\n\r','utf-8'))
					#Devices[Unit].Update(nValue =0,sValue = str(Level))
				
			if infoType == "10" :
				Area=Options['area']
				if Level == 0 : # Off
					lineinput="ZIA++ OFF X2DELEC A"+Area + " %4"
				if Level == 10 : # HG
					lineinput="ZIA++ OFF X2DELEC A"+Area + " %5"
				if Level == 20 : # Eco
					lineinput="ZIA++ OFF X2DELEC A"+Area + " %0"
				if Level == 30 : # confort-2
					lineinput="ZIA++ OFF X2DELEC A"+Area + " %1"
				if Level == 40 : # confort-1
					lineinput="ZIA++ OFF X2DELEC A"+Area + " %2"
				if Level == 50 : # confort
					lineinput="ZIA++ ON X2DELEC A"+Area + " %3"
				if Level == 60 : # assoc
					lineinput="ZIA++ ASSOC X2DELEC A"+Area
				SerialConn.Send(bytes(lineinput + '\n\r','utf-8'))
				Devices[Unit].Update(nValue =0,sValue = str(Level))

			if infoType == "11" :
				subType=Options['subType']
				if subType == "1" :
					id=Options['id']
					if Level == 10 :
						lineinput='ZIA++' + str("ON " + protocol + " ID " + id )#+ " QUALIFIER " + qualifier)
					if Level == 20 :
						lineinput='ZIA++' + str("OFF " + protocol + " ID " + id ) #+ " QUALIFIER " + qualifier)
					if Level == 30 :
						lineinput='ZIA++' + str("ASSOC " + protocol + " ID " + id ) #+ " QUALIFIER " + qualifier)
					SerialConn.Send(bytes(lineinput + '\n\r','utf-8'))
					Devices[Unit].Update(nValue =0,sValue = str(Level))
		else :
			Domoticz.Log("Erreur RFPlayer !");
				
def FreeUnit() :
	FreeUnit=""
	for x in range(1,256):
		Domoticz.Debug("FreeUnit - is device " + str(x) + " exist ?")
		if x not in Devices :
			Domoticz.Debug("FreeUnit - device " + str(x) + " not exist")
			FreeUnit=x
			return FreeUnit			
	if FreeUnit =="" :
		FreeUnit=len(Devices)+1
	Domoticz.Debug("FreeUnit - Free Device Unit find : " + str(x))
	return FreeUnit
	
	

def CheckRFPControl():
	#########check if devices exist ####################
	id=255

	########### create device if not find ###############
	if id not in Devices :
		Options = {"LevelNames": "OFF|STATUS|PAIR"}
		Domoticz.Device(Name="RFPlayer - Control", Unit=id, Type=16, Switchtype=18, Options=Options).Create()



def DecodeInfoType0(DecData, infoType):
	try :
		IsCreated=False
		x=0
		# New device will start at 1 or at last + 1
		nbrdevices=0
		protocol = DecData['frame']['header']['protocol']
		SubType = DecData['frame']['infos']['subType']
		id = DecData['frame']['infos']['id']
		Domoticz.Debug("id : " + str(id))
		
		Options = {"infoType":infoType, "id": str(id), "protocol": str(protocol)}
		Domoticz.Debug("Options to find or set : " + str(Options))
		#########check if devices exist ####################
		for x in Devices:
			#JJE - start
			DOptions = Devices[x].Options
	#				if Devices[x].Options == Options :
			if  DOptions["protocol"] == Options["protocol"] :
				if DOptions["infoType"] == Options["infoType"] :
					if DOptions["id"] == Options["id"] :
					#JJE - end
						IsCreated = True
						nbrdevices=x
						#Domoticz.Log("Devices already exist. Unit=" + str(x))
						Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
						break
		########### create device if not find ###############
		if IsCreated == False and Parameters["Mode4"] == "True" :
			nbrdevices=FreeUnit()
			Domoticz.Device(Name=protocol + " - " + id, Unit=nbrdevices, Type=16, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue =int(SubType),sValue = str(SubType),Options = Options)
		elif IsCreated == True :
		############ update device if found###################
			Devices[nbrdevices].Update(nValue =int(SubType),sValue = str(SubType))
	except:
		Domoticz.Log("Error while decoding Infotype0 frame")
		return

def DecodeInfoType1(DecData, infoType):
	try :
		IsCreated=False
		x=0
		# New device will start at 1 or at last + 1
		nbrdevices=0
		protocol = DecData['frame']['header']['protocol']
		SubType = DecData['frame']['infos']['subType']
		id = DecData['frame']['infos']['id']
		Domoticz.Debug("id : " + id)
		#########################################################################################
		######################### calcul id_lsb and id_msb from id ##############################
		#########################################################################################
		idb= bin(int(id))[2:]
		Domoticz.Debug("id binary : " + str(idb))
		Unit=idb[-6:]
		idd=idb[:-6]
		Domoticz.Debug("Unit b: " + str(Unit))
		Domoticz.Debug("id decode b: " + str(idd))
		Domoticz.Debug("Unit i: " + str(int(Unit,2)+1))
		Domoticz.Debug("id decode i: " + str(int(idd,2)))
		Domoticz.Debug("id decode h: " + str(hex(int(idd,2)))[2:])
		#########################################################################################
		#########################################################################################
		Options = {"infoType":infoType, "id": str(id), "id_lsb": str(hex(int(idd,2)))[2:], "id_msb": str(int(Unit,2)+1), "protocol": str(protocol)}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			#JJE - start
			DOptions = Devices[x].Options
			Domoticz.Debug("DOptions : " + str(DOptions))
	#				if Devices[x].Options == Options :
			if  DOptions["protocol"] == Options["protocol"] :
				if DOptions["infoType"] == Options["infoType"] :
					if DOptions["id"] == Options["id"] :
					#JJE - end
						IsCreated = True
						nbrdevices=x
						#Domoticz.Log("Devices already exist. Unit=" + str(x))
						Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
						#No need to walk on the other devices
						break
		if IsCreated == False and Parameters["Mode4"] == "True" :
			nbrdevices=FreeUnit()
			Domoticz.Device(Name=protocol + " - " + id, Unit=nbrdevices, Type=16, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue =int(SubType),sValue = str(SubType),Options = Options)
		elif IsCreated == True :
			Domoticz.Debug("update devices : " + str(x))
			Devices[nbrdevices].Update(nValue =int(SubType),sValue = str(SubType))
	except:
		Domoticz.Log("Error while decoding Infotype1 frame")
		return

def DecodeInfoType2(DecData, infoType):
	#try :
	IsCreated=False
	x=0
	nbrdevices=0
	protocol = DecData['frame']['header']['protocol']
	frequency = DecData['frame']['header']['frequency']
	SubType = DecData['frame']['infos']['subType']
	Domoticz.Debug("Protocol : " + str(protocol))
	if protocol == "2":
		id= DecData['frame']['infos']['id']
		qualifier = DecData['frame']['infos']['qualifier']
		Domoticz.Debug("id : " + str(id) + " qualifier :" + str(qualifier))
	if protocol == "3" :
		id = DecData['frame']['infos']['id']
		Domoticz.Debug("id : " + str(id) + " subType :" + str(SubType))
	##############################################################################################################
	if SubType == "0" and protocol == "2": # Detector/sensor visonic
		#Qualifier Meaning for MCT-320
		#"qualifier": "6", "qualifierMeaning": { "flags": ["Alarm","LowBatt"]}}}}
		#"qualifier": "4", "qualifierMeaning": { "flags": ["LowBatt"]}}}}
		#"qualifier": "2", "qualifierMeaning": { "flags": ["Alarm"]}}}}
		#"qualifier": "0", "qualifierMeaning": { "flags": []}}}}
		#"qualifier": "8", "qualifierMeaning": { "flags": ["Supervisor/Alive"]}}}}
		#"qualifier": "12", "qualifierMeaning": { "flags": ["LowBatt","Supervisor/Alive"]}}}}
		if qualifier =="8" or qualifier=="4" or qualifier=="12" or qualifier=="0":#Close
			status=0
		if qualifier == "1" :
			status=10
		if qualifier =="7" or qualifier=="2" or qualifier=="6":#Open
			status=20
		if qualifier == "3" :
			status=30
		Battery=99			#Default Value
		if qualifier == "4" or qualifier =="6" or qualifier =="12":
			Battery=10	
		Options = {"infoType":infoType, "id": str(id), "protocol": str(protocol), "subType": str(SubType), "LevelActions": "||||", "LevelNames": "Off|Tamper|Alarm|Tamper+Alarm", "LevelOffHidden": "False", "SelectorStyle": "0"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			#JJE - start
			DOptions = Devices[x].Options
#				if Devices[x].Options == Options :
			if  DOptions["protocol"] == Options["protocol"] :
				if DOptions["infoType"] == Options["infoType"] :
					if DOptions["id"] == Options["id"] :
					#JJE - end
						IsCreated = True
						nbrdevices=x
						#Domoticz.Log("Devices already exist. Unit=" + str(x))
						Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
						#No need to walk on the other devices
						break
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=FreeUnit()
			#Options = {"LevelActions": "||||", "LevelNames": "Off|Tamper|Alarm|Tamper+Alarm", "LevelOffHidden": "False", "SelectorStyle": "0"}
			Domoticz.Device(Name=protocol + " - " + id,  Unit=nbrdevices, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
			Devices[nbrdevices].Update(nValue =0,sValue = str(status), BatteryLevel = Battery, Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue =0,sValue = str(status), BatteryLevel = Battery)
	##############################################################################################################
	##############################################################################################################
	if SubType == "0" and protocol == "3" : # blyss 
		Options = {"infoType":infoType, "id": str(id), "protocol": str(protocol), "subType": str(SubType) }
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			#JJE - start
			DOptions = Devices[x].Options
#				if Devices[x].Options == Options :
			if  DOptions["protocol"] == Options["protocol"] :
				if DOptions["infoType"] == Options["infoType"] :
					if DOptions["id"] == Options["id"] :
					#JJE - end
						IsCreated = True
						nbrdevices=x
						#Domoticz.Log("Devices already exist. Unit=" + str(x))
						Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
						#No need to walk on the other devices
						break
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=FreeUnit()
			Domoticz.Device(Name=protocol + " - " + id,  Unit=nbrdevices, Type=16, Switchtype=0, Options=Options).Create()
			Devices[nbrdevices].Update(nValue =0, sValue = "on", Options = Options)
		elif IsCreated == True :
			svalue = Devices[nbrdevices].nValue
			if svalue =="on": svalue="off"
			if svalue =="off": svalue="on"
			Devices[nbrdevices].Update(nValue =0, sValue = str(svalue))
	##############################################################################################################
	elif SubType == "1":  # remote
		Options = {"infoType":infoType, "id": str(id), "protocol": str(protocol), "subType": str(SubType), "frequency": str(frequency)}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			#JJE - start
			DOptions = Devices[x].Options
#				if Devices[x].Options == Options :
			if  DOptions["protocol"] == Options["protocol"] :
				if DOptions["infoType"] == Options["infoType"] :
					if DOptions["id"] == Options["id"] :
					#JJE - end
						IsCreated = True
						nbrdevices=x
						#Domoticz.Log("Devices already exist. Unit=" + str(x))
						Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
						#No need to walk on the other devices
						break
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=FreeUnit()
			Domoticz.Device(Name="Button 1 - " + id, Unit=nbrdevices, Type=16, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue =0,sValue = "0", BatteryLevel = Battery, Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue =0,sValue = "0", BatteryLevel = Battery)
#	except:
#		Domoticz.Log("Error while decoding Infotype2 frame")
#		return

def DecodeInfoType3(DecData, infoType):
	try :
		Domoticz.Debug("Decoding infotype RTS frame")
		IsCreated=False
		x=0
		# New device will start at 1 or at last + 1
		nbrdevices=0
		protocol = DecData['frame']['header']['protocol']
		SubType = DecData['frame']['infos']['subType']
		id = DecData['frame']['infos']['id']
		Domoticz.Debug("id : " + id)
		qualifier = DecData['frame']['infos']['qualifier']
		Domoticz.Debug("protocol : " + str(protocol) + " - SubType : " + str(SubType) +" - id : " + str(id) + " - Qualifier : " + str(qualifier))
#		if len(str(id))== 8 :
#			Domoticz.Debug("len id = 8")
#			idb= bin(int(id))[2:]
#			id= int(idb[1:],2)
		if SubType == "0" :
			Domoticz.Debug("subtype = 0")
			if qualifier == "1" :
				Domoticz.Debug("qualifier == 1")
				level = 0 #Off/Down
				Action = 1
				sAction = "On"
			elif qualifier == "4" :
				Domoticz.Debug("qualifier == 4")
				level = 10 #My
				Action = 17
				sAction = "50"
			elif qualifier == "7" :
				Domoticz.Debug("qualifier == 7")
				level = 20 #On/Up
				Action = 0
				sAction = "Off"
			elif qualifier == "13" :
				Domoticz.Debug("qualifier == 13")
				level = 30 #Assoc
				Action = 18
			else :
				Domoticz.Log("Unknow qualifier - please send log to dev team")
			#################################################################################################################
			Domoticz.Debug("id : " + str(id))
			Options = {"infoType": infoType, "id": str(id), "protocol": str(protocol), "subType": str(SubType), "LevelActions": "|||||", "LevelNames": "Off/Down|My|On/Up|Assoc", "LevelOffHidden": "False", "SelectorStyle": "0"}
			Domoticz.Debug("Options to find or set : " + str(Options))
			for x in Devices:
				#JJE - start
				DOptions = Devices[x].Options
				Domoticz.Debug(str(x) + " -- DOptions : " + str(DOptions))
				try :
					if  DOptions["protocol"] == Options["protocol"] :
						OtherId = ""
						try :
							for line in Devices[x].Description.splitlines():
								if line.find("Options") != -1:
									line=line.split(":")[1]
									for Option in line.split(";"):
										NameVar=Option.split("=")[0]
										ValVar=Option.split("=")[1]
										if NameVar=="OtherId":
											OtherId=ValVar
						except :
							Domoticz.Debug("Error while locating OtherId")
						Domoticz.Debug("Recherche ID " + Options["id"] + " ou " + OtherId)
						
						if OtherId.find(Options["id"]) != -1 :
							#JJE - end
							#IsCreated = True
							#nbrdevices=x
							#Domoticz.Log("Devices already exist. Unit=" + str(x))
							Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
							Devices[x].Update(nValue = Action,sValue = str(level))
							#No need to walk on the other devices
							#break
						if DOptions["infoType"] == Options["infoType"] :
							if DOptions["id"] == Options["id"] :
								#JJE - end
								IsCreated = True
								nbrdevices=x
								Domoticz.Log("Devices already exist. Unit=" + str(x))
								Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
								Devices[nbrdevices].Update(nValue = 1,sValue = str(level))
								#No need to walk on the other devices
								#break
				except :
					Domoticz.Debug("Error while matching")
			if IsCreated == False and Parameters["Mode4"] == "True":
				Domoticz.Debug("Create devices : " + str(x))
				nbrdevices=FreeUnit()
				#Options = {"LevelActions": "|||||", "LevelNames": "Off/Down|My|On/Up|Assoc", "LevelOffHidden": "False", "SelectorStyle": "0", "protocol": str(Options["protocol"]),"id": str(id),"infoType":str(Options["infoType"])}
				Domoticz.Device(Name=" RTS Telec - " + str(id),  Unit=nbrdevices, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
				Devices[nbrdevices].Update(nValue = 1,sValue = str(level),Options = Options)
			elif IsCreated == True :
				Domoticz.Debug("isCreated = True")
				#Devices[nbrdevices].Update(nValue = 1,sValue = str(level))
				#Devices[nbrdevices].Update(nValue = 1,sValue = "0")
			###############################################################################################################
		elif SubType == "1" :
			if qualifier == "5" :
				level = 10
			elif qualifier == "6" :
				level = 20
			else :
				Domoticz.Log("Unknow qualifier - please send log to dev team")
			Domoticz.Debug("id : " + str(id))
			#####################################################################################################################
			Options = {"infoType": infoType, "id": str(id), "protocol": str(protocol), "subType": str(SubType), "LevelActions": "||||", "LevelNames": "Off|Left button|Right button", "LevelOffHidden": "False", "SelectorStyle": "0"}
			Domoticz.Debug("Options to find or set : " + str(Options))
			for x in Devices:
				#JJE - start
				DOptions = Devices[x].Options
	#				if Devices[x].Options == Options :
				if  DOptions["protocol"] == Options["protocol"] :
					if DOptions["infoType"] == Options["infoType"] :
						if DOptions["id"] == Options["id"] :
						#JJE - end
							IsCreated = True
							nbrdevices=x
							#Domoticz.Log("Devices already exist. Unit=" + str(x))
							Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
							#No need to walk on the other devices
							break
			if IsCreated == False and Parameters["Mode4"] == "True":
				nbrdevices=FreeUnit()
				#Options = {"LevelActions": "||||", "LevelNames": "Off|Left button|Right button", "LevelOffHidden": "False", "SelectorStyle": "0"}
				Domoticz.Device(Name=" RTS - " + str(id),  Unit=nbrdevices, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
				Devices[nbrdevices].Update(nValue = 0,sValue = "0",Options = Options)
			elif IsCreated == True :
				Devices[nbrdevices].Update(nValue = 0,sValue = str(level))
				#Devices[nbrdevices].Update(nValue = 1,sValue = "0")
		else :
			Domoticz.Log("Unknow SubType - please send log to dev team")
	except:
		Domoticz.Log("Error while decoding Infotype3 frame")
		return

def DecodeInfoType4(DecData, infoType):
	try :
		protocol = DecData['frame']['header']['protocol']
		id_PHY = DecData['frame']['infos']['id_PHY']
		adr_channel = DecData['frame']['infos']['adr_channel']
		channel = DecData['frame']['infos']['channel']
		qualifier = DecData['frame']['infos']['qualifier']
		
		try:
			lowBatt = DecData['frame']['infos']['lowBatt']
		except IndexError:
			lowbatt="0"
		try:
			temp = DecData['frame']['infos']['measures'][0]['value']
		except IndexError:
			temp = "0"
		try :
			hygro = DecData['frame']['infos']['measures'][1]['value']
		except IndexError:
			hygro = "0"
		battery_level = 100 if DecData['frame']['infos']['lowBatt'] == "0" else 0
		signal_level = int(DecData['frame']['header']['rfQuality'])
		temphygro = temp + ';' + hygro + ';1'
		Domoticz.Debug("id : " + id_PHY + " adr_channel : " + adr_channel)
		IsCreated=False
		x=0
		# New device will start at 1 or at last + 1
		nbrdevices=0
		sensorType = 80
		Options = {"infoType":infoType, "id": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "Temp" : "1", "sensorType" : str(sensorType) }
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			#JJE - start
			DOptions = Devices[x].Options
#				if Devices[x].Options == Options :
			if  DOptions["protocol"] == Options["protocol"] :
				if DOptions["infoType"] == Options["infoType"] and DOptions["sensorType"] == Options["sensorType"]:
					if DOptions["id"] == Options["id"] and DOptions["adr_channel"] == Options["adr_channel"] :
					#JJE - end
						IsCreated = True
						nbrdevices=x
						#Domoticz.Log("Devices already exist. Unit=" + str(x))
						Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
						#No need to walk on the other devices
						break;
		subType = 0
		if id_PHY in InfoType4SubTypes:
			subType = InfoType4SubTypes[id_PHY][1]
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=FreeUnit()
			Domoticz.Device(Name="Temp - " + adr_channel + ' (channel ' + channel + ')', Unit=nbrdevices, Type=80, Subtype=subType, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 1,sValue = str(temp), SignalLevel=signal_level , BatteryLevel=battery_level, Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 1,sValue = str(temp), SignalLevel=signal_level , BatteryLevel=battery_level)
		#####################################################################################################################
		IsCreated=False
		x=0
		nbrdevices=0
		sensorType = 81
		Options = {"infoType":infoType, "id": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "Hygro" : "1", "sensorType" : str(sensorType) }
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			#JJE - start
			DOptions = Devices[x].Options
#				if Devices[x].Options == Options :
			if  DOptions["protocol"] == Options["protocol"] :
				if DOptions["infoType"] == Options["infoType"] and DOptions["sensorType"] == Options["sensorType"]:
					if DOptions["id"] == Options["id"] and DOptions["adr_channel"] == Options["adr_channel"] :
					#JJE - end
						IsCreated = True
						nbrdevices=x
						#Domoticz.Log("Devices already exist. Unit=" + str(x))
						Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
						#No need to walk on the other devices
						break;
		subType = 0
		if id_PHY in InfoType4SubTypes:
			subType = InfoType4SubTypes[id_PHY][2]
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=FreeUnit()
			Domoticz.Device(Name="Hygro - " + adr_channel + ' (channel ' + channel + ')', Unit=nbrdevices, Type=81, Subtype=subType, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = int(hygro),sValue = "1", SignalLevel=signal_level , BatteryLevel=battery_level, Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = int(hygro),sValue = "1", SignalLevel=signal_level , BatteryLevel=battery_level)
		#####################################################################################################################	
		IsCreated=False
		x=0
		# New device will start at 1 or at last + 1
		nbrdevices=0
		sensorType = 82
		Options = {"infoType":infoType, "id": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "TempHygro" : "1", "sensorType" : str(sensorType) }
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			#JJE - start
			DOptions = Devices[x].Options
#				if Devices[x].Options == Options :
			if  DOptions["protocol"] == Options["protocol"] :
				if DOptions["infoType"] == Options["infoType"] and DOptions["sensorType"] == Options["sensorType"]:
					if DOptions["id"] == Options["id"] and DOptions["adr_channel"] == Options["adr_channel"] :
					#JJE - end
						IsCreated = True
						nbrdevices=x
						#Domoticz.Log("Devices already exist. Unit=" + str(x))
						Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
						# No need to walk on the other devices
						break
		subType = 0
		if id_PHY in InfoType4SubTypes:
			subType = InfoType4SubTypes[id_PHY][0]
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=FreeUnit()
			Domoticz.Device(Name="Temp/Hygro - " + adr_channel + ' (channel ' + channel + ')', Unit=nbrdevices, Type=82, Subtype=subType, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 1,sValue = str(temphygro), SignalLevel=signal_level , BatteryLevel=battery_level, Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 1,sValue = str(temphygro), SignalLevel=signal_level , BatteryLevel=battery_level)
	except Exception as e:
		Domoticz.Log("Error while decoding Infotype4 frame" + repr(e))
		return

def DecodeInfoType5(DecData, infoType):
	try :
		IsCreated=False
		x=0
		# New device will start at 1 or at last + 1
		nbrdevices=0
		protocol = DecData['frame']['header']['protocol']
		id_PHY = DecData['frame']['infos']['id_PHY']
		adr_channel = DecData['frame']['infos']['adr_channel']
		qualifier = DecData['frame']['infos']['qualifier']
		try:
			lowBatt = DecData['frame']['infos']['lowBatt']
		except IndexError:
			lowbatt="0"
		try:
			temp = DecData['frame']['infos']['measures'][0]['value']
		except IndexError:
			temp = "0"
		try :
			hygro = DecData['frame']['infos']['measures'][1]['value']
		except IndexError:
			hygro = "0"
		try :
			pressure = DecData['frame']['infos']['measures'][2]['value']
		except IndexError:
			pressure = "0"
		temphygro = temp + ';' + hygro + ';1'
		temphygropress = temphygro + ';' + pressure + ';1'

		Domoticz.Debug("id : " + id_PHY + " adr_channel : " + adr_channel)
		
		Options = {"infoType":infoType, "id": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "Temp" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			#JJE - start
			DOptions = Devices[x].Options
#				if Devices[x].Options == Options :
			if  DOptions["protocol"] == Options["protocol"] :
				if DOptions["infoType"] == Options["infoType"] :
					if DOptions["id"] == Options["id"] :
					#JJE - end
						IsCreated = True
						nbrdevices=x
						#Domoticz.Log("Devices already exist. Unit=" + str(x))
						Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
						break;
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=FreeUnit()
			Domoticz.Device(Name="Temp - " + adr_channel, Unit=nbrdevices, Type=80, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 0,sValue = str(temp),Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 0,sValue = str(temp))
		#####################################################################################################################
		IsCreated=False
		x=0
		# New device will start at 1 or at last + 1
		nbrdevices=0
		Options = {"infoType":infoType, "id": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "Hygro" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			#JJE - start
			DOptions = Devices[x].Options
#				if Devices[x].Options == Options :
			if  DOptions["protocol"] == Options["protocol"] :
				if DOptions["infoType"] == Options["infoType"] :
					if DOptions["id"] == Options["id"] :
					#JJE - end
						IsCreated = True
						nbrdevices=x
						#Domoticz.Log("Devices already exist. Unit=" + str(x))
						Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
						break
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=FreeUnit()
			Domoticz.Device(Name="Hygro - " + adr_channel, Unit=nbrdevices, Type=81, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = int(hygro),sValue = "1",Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = int(hygro),sValue = "1")
		#####################################################################################################################
		IsCreated=False
		x=0
		# New device will start at 1 or at last + 1
		nbrdevices=0
		Options = {"infoType":infoType, "id": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "Pressure" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			#JJE - start
			DOptions = Devices[x].Options
#				if Devices[x].Options == Options :
			if  DOptions["protocol"] == Options["protocol"] :
				if DOptions["infoType"] == Options["infoType"] :
					if DOptions["id"] == Options["id"] :
					#JJE - end
						IsCreated = True
						nbrdevices=x
						#Domoticz.Log("Devices already exist. Unit=" + str(x))
						Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
						break
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=FreeUnit()
			Domoticz.Device(Name="Pressure - " + adr_channel, Unit=nbrdevices, Type=243, Subtype=26, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 0,sValue = str(pressure),Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 0,sValue = str(pressure)+";0")
		#####################################################################################################################	
		IsCreated=False
		x=0
		# New device will start at 1 or at last + 1
		nbrdevices=0
		Options = {"infoType":infoType, "id": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "TempHygro" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			#JJE - start
			DOptions = Devices[x].Options
#				if Devices[x].Options == Options :
			if  DOptions["protocol"] == Options["protocol"] :
				if DOptions["infoType"] == Options["infoType"] :
					if DOptions["id"] == Options["id"] :
					#JJE - end
						IsCreated = True
						nbrdevices=x
						#Domoticz.Log("Devices already exist. Unit=" + str(x))
						Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
						break
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=FreeUnit()
			Domoticz.Device(Name="Temp/Hygro - " + adr_channel, Unit=nbrdevices, Type=82, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 0,sValue = str(temphygro),Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 0,sValue = str(temphygro))
		#####################################################################################################################	
		IsCreated=False
		x=0
		# New device will start at 1 or at last + 1
		nbrdevices=0
		Options = {"infoType":infoType, "id": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "TempHygropressure" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			#JJE - start
			DOptions = Devices[x].Options
#				if Devices[x].Options == Options :
			if  DOptions["protocol"] == Options["protocol"] :
				if DOptions["infoType"] == Options["infoType"] :
					if DOptions["id"] == Options["id"] :
					#JJE - end
						IsCreated = True
						nbrdevices=x
						#Domoticz.Log("Devices already exist. Unit=" + str(x))
						Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
						break
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=FreeUnit()
			Domoticz.Device(Name="Temp/Hygro - " + adr_channel, Unit=nbrdevices, Type=84, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 0,sValue = str(temphygropress),Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 0,sValue = str(temphygropress))
	except:
		Domoticz.Log("Error while decoding Infotype5 frame")
		return

def DecodeInfoType6(DecData, infoType):
	try :
		IsCreated=False
		x=0
		# New device will start at 1 or at last + 1
		nbrdevices=0
		protocol = DecData['frame']['header']['protocol']
		id_PHY = DecData['frame']['infos']['id_PHY']
		adr_channel = DecData['frame']['infos']['adr_channel']
		qualifier = DecData['frame']['infos']['qualifier']
		try:
			lowBatt = DecData['frame']['infos']['lowBatt']
		except IndexError:
			lowbatt="0"
		try:
			speed = DecData['frame']['infos']['measures'][0]['value']
		except IndexError:
			speed = "0"
		try:
			direction = DecData['frame']['infos']['measures'][1]['value']
		except IndexError:
			direction = "0"
		if 22 <= int(direction) << 68 : 
			sens = 'NE'
		if 68 <= int(direction) << 112 : 
			sens = 'E'
		if 112 <= int(direction) << 157 : 
			sens = 'SE'
		if 157 <= int(direction) <= 202 : 
			sens = 'S'
		if 202 <= int(direction) <= 247 : 
			sens = 'SO'
		if 247 <= int(direction) <= 292 : 
			sens = 'O'
		if 292 <= int(direction) <= 337 : 
			sens = 'NO'
		if 337 <= int(direction) or int(direction) <= 22 : 
			sens = 'N'
		
		Wind = direction + ';' + sens + ';' + speed + ';0;0;0' #form need : 0;N;0;0;0;0

		Domoticz.Debug("id : " + id_PHY + " adr_channel : " + adr_channel)
		Options = {"infoType":infoType, "id": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "Wind" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			#JJE - start
			DOptions = Devices[x].Options
#				if Devices[x].Options == Options :
			if  DOptions["protocol"] == Options["protocol"] :
				if DOptions["infoType"] == Options["infoType"] :
					if DOptions["id"] == Options["id"] :
					#JJE - end
						IsCreated = True
						nbrdevices=x
						#Domoticz.Log("Devices already exist. Unit=" + str(x))
						Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
						break
		if IsCreated == False and Parameters["Mode4"] == "True" :
			nbrdevices=FreeUnit()
			Domoticz.Device(Name="Wind - " + adr_channel, Unit=nbrdevices, Type=86, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 0,sValue = str(Wind),Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 0,sValue = str(Wind))
	except:
		Domoticz.Log("Error while decoding Infotype6 frame")
		return

def DecodeInfoType7(DecData, infoType):
	try :
		IsCreated=False
		x=0
		# New device will start at 1 or at last + 1
		nbrdevices=0
		protocol = DecData['frame']['header']['protocol']
		id_PHY = DecData['frame']['infos']['id_PHY']
		adr_channel = DecData['frame']['infos']['adr_channel']
		qualifier = DecData['frame']['infos']['qualifier']
		UV = DecData['frame']['infos']['measures'][0]['value']
		try:
			lowBatt = DecData['frame']['infos']['lowBatt']
		except IndexError:
			lowbatt="0"
		Domoticz.Debug("id : " + id_PHY + " adr_channel : " + adr_channel)
		
		Options = {"infoType":infoType, "id": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "UV" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			#JJE - start
			DOptions = Devices[x].Options
#				if Devices[x].Options == Options :
			if  DOptions["protocol"] == Options["protocol"] :
				if DOptions["infoType"] == Options["infoType"] :
					if DOptions["id"] == Options["id"] :
					#JJE - end
						IsCreated = True
						nbrdevices=x
						#Domoticz.Log("Devices already exist. Unit=" + str(x))
						Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
						break
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=FreeUnit()
			Domoticz.Device(Name="UV - " + adr_channel, Unit=nbrdevices, Type=80, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 0,sValue = str(int(UV)/10) + ';0',Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 0,sValue = str(int(UV)/10) + ';0')
	except:
		Domoticz.Log("Error while decoding Infotype7 frame")
		return

def DecodeInfoType8(DecData, infoType):
	try :
		IsCreated=False
		x=0
		# New device will start at 1 or at last + 1
		nbrdevices=0
		protocol = DecData['frame']['header']['protocol']
		id_PHY = DecData['frame']['infos']['id_PHY']
		adr_channel = DecData['frame']['infos']['adr_channel']
		qualifier = DecData['frame']['infos']['qualifier']
		
		Energy = DecData['frame']['infos']['measures'][0]['value']   #♣ watt/hour
		Power = DecData['frame']['infos']['measures'][1]['value']  #♣ total watt with u=230v
		try:
			P1 = DecData['frame']['infos']['measures'][2]['value']   #♣ watt with u=230v
			P2 = DecData['frame']['infos']['measures'][3]['value']   #♣ watt with u=230v
			P3 = DecData['frame']['infos']['measures'][4]['value']   #♣ watt with u=230v
		except:
			P1 = ""
			P2 = ""
			P3 = ""
		Domoticz.Debug("id : " + id_PHY + " adr_channel : " + adr_channel)
		##################################################################################################################################
		Options = {"infoType":infoType, "id": str(id_PHY), "id": str(adr_channel), "protocol": str(protocol), "Power&Energie" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			#JJE - start
			DOptions = Devices[x].Options
#				if Devices[x].Options == Options :
			if  DOptions["protocol"] == Options["protocol"] :
				if DOptions["infoType"] == Options["infoType"] :
					if DOptions["id"] == Options["id"] :
					#JJE - end
						IsCreated = True
						nbrdevices=x
						#Domoticz.Log("Devices already exist. Unit=" + str(x))
						Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
						break
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=FreeUnit()
			Domoticz.Device(Name="Power & Energie - " + adr_channel, Unit=nbrdevices, Type=243, Subtype =29, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 0,sValue = str(Power + ';' + Energy),Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 0,sValue = str(Power + ';' + Energy))		
		##################################################################################################################################
		if P1 != "" : 
			IsCreated=False
			x=0
			# New device will start at 1 or at last + 1
			nbrdevices=0
			Options = {"infoType":infoType, "id": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "P1" : "1"}
			Domoticz.Debug("Options to find or set : " + str(Options))
			for x in Devices:
				#JJE - start
				DOptions = Devices[x].Options
	#				if Devices[x].Options == Options :
				if  DOptions["protocol"] == Options["protocol"] :
					if DOptions["infoType"] == Options["infoType"] :
						if DOptions["id"] == Options["id"] :
						#JJE - end
							IsCreated = True
							nbrdevices=x
							#Domoticz.Log("Devices already exist. Unit=" + str(x))
							Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
							break
			if IsCreated == False and Parameters["Mode4"] == "True":
				nbrdevices=FreeUnit()
				Domoticz.Device(Name="P1 - " + adr_channel, Unit=nbrdevices, Type=248, Switchtype=0).Create()
				Devices[nbrdevices].Update(nValue = 0,sValue = str(P1),Options = Options)
			elif IsCreated == True :
				Devices[nbrdevices].Update(nValue = 0,sValue = str(P1))
		##################################################################################################################################
		if P2 != "" :
			IsCreated=False
			x=0
			# New device will start at 1 or at last + 1
			nbrdevices=0
			Options = {"infoType":infoType, "id": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "P2" : "1"}
			Domoticz.Debug("Options to find or set : " + str(Options))
			for x in Devices:
				#JJE - start
				DOptions = Devices[x].Options
	#				if Devices[x].Options == Options :
				if  DOptions["protocol"] == Options["protocol"] :
					if DOptions["infoType"] == Options["infoType"] :
						if DOptions["id"] == Options["id"] :
						#JJE - end
							IsCreated = True
							nbrdevices=x
							#Domoticz.Log("Devices already exist. Unit=" + str(x))
							Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
							break
			if IsCreated == False and Parameters["Mode4"] == "True":
				nbrdevices=FreeUnit()
				Domoticz.Device(Name="P2 - " + adr_channel, Unit=nbrdevices, Type=248, Switchtype=0).Create()
				Devices[nbrdevices].Update(nValue = 0,sValue = str(P2),Options = Options)
			elif IsCreated == True :
				Devices[nbrdevices].Update(nValue = 0,sValue = str(P2))	
		##################################################################################################################################
		if P3 != "" :
			IsCreated=False
			x=0
			# New device will start at 1 or at last + 1
			nbrdevices=0
			Options = {"infoType":infoType, "id": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "P3" : "1"}
			Domoticz.Debug("Options to find or set : " + str(Options))
			for x in Devices:
				#JJE - start
				DOptions = Devices[x].Options
	#				if Devices[x].Options == Options :
				if  DOptions["protocol"] == Options["protocol"] :
					if DOptions["infoType"] == Options["infoType"] :
						if DOptions["id"] == Options["id"] :
						#JJE - end
							IsCreated = True
							nbrdevices=x
							#Domoticz.Log("Devices already exist. Unit=" + str(x))
							Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
							break
			if IsCreated == False and Parameters["Mode4"] == "True":
					nbrdevices=FreeUnit()
					Domoticz.Device(Name="P3 - " + adr_channel, Unit=nbrdevices, Type=248, Switchtype=0).Create()
					Devices[nbrdevices].Update(nValue = 0,sValue = str(P3),Options = Options)
			elif IsCreated == True :
				Devices[nbrdevices].Update(nValue = 0,sValue = str(P3))
	except:
		Domoticz.Log("Error while decoding Infotype8 frame")
		return

def DecodeInfoType9(DecData, infoType):
	try :
		IsCreated=False
		x=0
		# New device will start at 1 or at last + 1
		nbrdevices=0
		protocol = DecData['frame']['header']['protocol']
		id_PHY = DecData['frame']['infos']['id_PHY']
		adr_channel = DecData['frame']['infos']['adr_channel']
		qualifier = DecData['frame']['infos']['qualifier']
		try:
			lowBatt = DecData['frame']['infos']['lowBatt']
		except IndexError:
			lowbatt="0"
		try:
			TotalRain = DecData['frame']['infos']['measures'][0]['value']
		except IndexError:
			TotalRain = "0"
		try :
			CurrentRain = DecData['frame']['infos']['measures'][1]['value']
		except IndexError:
			CurrentRain = "0"
		Domoticz.Debug("id : " + id_PHY + " adr_channel : " + adr_channel)
		
		Options = {"infoType":infoType, "id": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "Temp" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			#JJE - start
			DOptions = Devices[x].Options
#				if Devices[x].Options == Options :
			if  DOptions["protocol"] == Options["protocol"] :
				if DOptions["infoType"] == Options["infoType"] :
					if DOptions["id"] == Options["id"] :
					#JJE - end
						IsCreated = True
						nbrdevices=x
						#Domoticz.Log("Devices already exist. Unit=" + str(x))
						Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
						break
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=FreeUnit()
			Domoticz.Device(Name="Rain - " + adr_channel, Unit=nbrdevices, Type=85, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 0,sValue = str(CurrentRain),Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 0,sValue = str(CurrentRain))
	except:
		Domoticz.Log("Error while decoding Infotype9 frame")
		return

def DecodeInfoType10(DecData, infoType):
	try :
		IsCreated=False
		x=0
		# New device will start at 1 or at last + 1
		nbrdevices=0
		protocol = DecData['frame']['header']['protocol']
		frequency = DecData['frame']['header']['frequency']
		SubType = DecData['frame']['infos']['subType']
		id = DecData['frame']['infos']['id']
		area = DecData['frame']['infos']['area']
		function = DecData['frame']['infos']['function']
		state = DecData['frame']['infos']['state']
		
		#########################################################################################
		######################### calcul id_lsb and id_msb from id ##############################
		#########################################################################################
		idb= bin(int(id))[2:]
		Domoticz.Debug("id binary : " + str(idb))
		Unit=idb[-6:]
		idd=idb[:-6]
		Domoticz.Debug("area b: " + str(Unit))
		Domoticz.Debug("id decode b: " + str(idd))
		Domoticz.Debug("area i: " + str(int(Unit,2)+1))
		Domoticz.Debug("id decode i: " + str(int(idd,2)))
		Domoticz.Debug("id decode h: " + str(hex(int(idd,2)))[2:])
		#########################################################################################
		#########################################################################################
		
		if function == "2" :
			if state == "0": #ECO 
				status = 20
			if state == "1": #MODERAT 
				status = 30
			if state == "2": #MEDIO
				status = 40
			if state == "3": #COMFORT 
				status = 50
			if state == "4": #STOP 
				status = 0
			if state == "5": #OUT OF FROST 
				status = 10
			if state == "6": #SPECIAL 
				status = 60
			if state == "7": #AUTO 
				status = 70
			if state == "8": #CENTRALISED
				status = 80
			Options = {"infoType":infoType, "id": str(idd), "area": str(area), "function": str(function), "protocol": str(protocol), "subType": str(SubType), "frequency": str(frequency), "LevelActions": "|||||||||", "LevelNames": "Off|HG|Eco|Moderat|Medio|Comfort|Assoc", "LevelOffHidden": "False", "SelectorStyle": "0"}
			Domoticz.Debug("Options to find or set : " + str(Options))
			for x in Devices:
				DOptions = Devices[x].Options
				Domoticz.Debug("scanning devices: "+repr(x) + repr(DOptions))
				if {k: DOptions.get(k, None) for k in ('id', 'protocol', 'infoType')} == {k: Options.get(k, None) for k in ('id', 'protocol', 'infoType')}:
					IsCreated = True
					nbrdevices=x
					#Domoticz.Log("Devices already exist. Unit=" + str(x))
					Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
					break
			if IsCreated == False and Parameters["Mode4"] == "True":
				nbrdevices=FreeUnit()
				Domoticz.Device(Name=protocol + " - " + id,  Unit=nbrdevices, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
				Devices[nbrdevices].Update(nValue =0,sValue = str(status), Options = Options)
			elif IsCreated == True :
				Devices[nbrdevices].Update(nValue =0,sValue = str(status))
	##############################################################################################################
		else :
			Options = {"infoType":infoType, "id": str(id), "area": str(area), "function": str(function), "protocol": str(protocol), "subType": str(SubType), "frequency": str(frequency)}
			Domoticz.Debug("Options to find or set : " + str(Options))
			for x in Devices:
				Domoticz.Debug("scanning devices: "+repr(x))
				DOptions = Devices[x].Options
	#				if Devices[x].Options == Options :
				if {k: DOptions.get(k, None) for k in ('id', 'protocol', 'infoType', 'area')} == {k: Options.get(k, None) for k in ('id', 'protocol', 'infoType', 'area')}:
					IsCreated = True
					nbrdevices=x
					#Domoticz.Log("Devices already exist. Unit=" + str(x))
					Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
					break
			if IsCreated == False and Parameters["Mode4"] == "True":
				nbrdevices=FreeUnit()
				Domoticz.Device(Name=protocol + " - " + id, Unit=nbrdevices, Type=16, Switchtype=0).Create()
				Devices[nbrdevices].Update(nValue =0,sValue = str(state), Options = Options)
			elif IsCreated == True :
				Devices[nbrdevices].Update(nValue =0,sValue = str(state))
	except Exception as e:
		Domoticz.Log("Error while decoding Infotype10 frame: " + repr(e))
		return

def DecodeInfoType11(DecData, infoType):
	try :
		IsCreated=False
		x=0
		# New device will start at 1 or at last + 1
		nbrdevices=0
		protocol = DecData['frame']['header']['protocol']
		SubType = DecData['frame']['infos']['subType']
		frequency=DecData['frame']['header']['frequency']
		##############################################################################################################
		if SubType == "0" : # Detector/sensor
			id = DecData['frame']['infos']['id']
			qualifier = DecData['frame']['infos']['qualifier']
			if qualifier=="0":
				status=0
			if qualifier=="2":
				status=10
			if qualifier=="1":
				status=20
			if qualifier == "10":
				status=0
			Options = {"infoType":infoType, "id": str(id), "protocol": str(protocol), "frequency": str(frequency), "subType": str(SubType), "LevelActions": "||||", "LevelNames": "Off|Tamper|Alarm|Tamper+Alarm", "LevelOffHidden": "False", "SelectorStyle": "0"}
			Domoticz.Debug("Options to find or set : " + str(Options))
			for x in Devices:
				#JJE - start
				DOptions = Devices[x].Options
	#				if Devices[x].Options == Options :
				if  DOptions["protocol"] == Options["protocol"] :
					if DOptions["infoType"] == Options["infoType"] :
						if DOptions["id"] == Options["id"] :
						#JJE - end
							IsCreated = True
							nbrdevices=x
							#Domoticz.Log("Devices already exist. Unit=" + str(x))
							Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
							break
			if IsCreated == False and Parameters["Mode4"] == "True":
				nbrdevices=FreeUnit()
				#Options = {"LevelActions": "||||", "LevelNames": "Off|Alarm|Tamper", "LevelOffHidden": "False", "SelectorStyle": "0"}
				Domoticz.Device(Name=protocol + " - " + id,  Unit=nbrdevices, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
				Devices[nbrdevices].Update(nValue =0,sValue = str(status), Options = Options)
			elif IsCreated == True :
				Devices[nbrdevices].Update(nValue =0,sValue = str(status))
		##############################################################################################################
		elif SubType == "1":  # remote
			id = DecData['frame']['infos']['id']
			qualifier = DecData['frame']['infos']['qualifier']
			if qualifier=="1" :
				status=10
			if qualifier=="2" :
				status=0
			if qualifier=="3" :
				status=20
			Options = {"infoType":infoType, "id": str(id), "protocol": str(protocol), "frequency": str(frequency), "subType": str(SubType), "LevelActions": "|||", "LevelNames": "Off|On|Stop", "LevelOffHidden": "False", "SelectorStyle": "0"}
			Domoticz.Debug("Options to find or set : " + str(Options))
			for x in Devices:
				#JJE - start
				DOptions = Devices[x].Options
	#				if Devices[x].Options == Options :
				if  DOptions["protocol"] == Options["protocol"] :
					if DOptions["infoType"] == Options["infoType"] :
						if DOptions["id"] == Options["id"] :
						#JJE - end
							IsCreated = True
							nbrdevices=x
							#Domoticz.Log("Devices already exist. Unit=" + str(x))
							Domoticz.Debug("Options found in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
							break;
			if IsCreated == False and Parameters["Mode4"] == "True":
				nbrdevices=FreeUnit()
				Domoticz.Device(Name=protocol + " - " + id,  Unit=nbrdevices, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
				Devices[nbrdevices].Update(nValue =0,sValue = str(status), Options = Options)
			elif IsCreated == True :
				Devices[nbrdevices].Update(nValue =0,sValue = str(status))
	except:
		Domoticz.Log("Error while decoding Infotype11 frame")
		return

def Plugin_032(RawSignal_Number,RawSignal_Pulses) :
	if (RawSignal_Number < 74 | RawSignal_Number > 78 ) :
		return False
	bitstream=0
	temperature=0
	humidity=0
	rc=0
	rc2=0
	
	MaxOneLen=560 #550 à l'origine
	MaxUpZeroLen=3000
	MinZeroLen=1480 #1500 à l'origine
	MaxZeroLen=2100
      
	#==================================================================================
	start=0
	if (RawSignal_Number == 78) :
		start=4
	if (RawSignal_Number == 76) :
		start=2
	x=2+start
	while(x<=56+start) :                     # Get first 28 bits
		if (RawSignal_Pulses[x+1] > MaxOneLen) :
			Domoticz.Log("Phase 1 - Bad 1 Length")
			return False
		if (RawSignal_Pulses[x] > MaxUpZeroLen) :
		   bitstream = (bitstream << 1) | 0x01;
		else :
			if (RawSignal_Pulses[x] > MinZeroLen) :
				if (RawSignal_Pulses[x] > MaxZeroLen) :
					Domoticz.Log("Phase 1 - Bad 0 Length - Too Long")
					return False;
				bitstream = (bitstream << 1)
			else :
				Domoticz.Log("Phase 1 - Bad 0 Length - Too Short")
				return False
		x=x+2
	
	x=58+start
	while(x<=72+start) :                          # Get remaining 8 bits
		if (RawSignal_Pulses[x+1] > MaxOneLen) :
			Domoticz.Log("Phase 2 - Bad 1 Length")
			return False
		if(RawSignal_Pulses[x] > MaxUpZeroLen) :
			humidity = (humidity << 1) | 0x01
		else :
			humidity = (humidity << 1)
		x=x+2
	
	#==================================================================================
	# Prevent repeating signals from showing up
	#==================================================================================
	#if( (SignalHash!=SignalHashPrevious) || ((RepeatingTimer+3000) < millis()) ) { # 1000
	 # not seen the RF packet recently
	# if (bitstream == 0) return false;   // Sanity check
	# if (humidity==0) return false;      // Sanity check
	#} else {
	# already seen the RF packet recently
	# return true;
	#} 
	#==================================================================================
	# Sort data
	rc = (bitstream >> 20) & 0xff
	rc2= (bitstream >> 12) & 0xfb        
	if ( ((rc2)&0x08) != 0x08) :
		Domoticz.Log("Phase 3 - Bad rc2")
		return False;         # needs to be 1
	temperature = (bitstream) & 0xfff
	#fix 12 bit signed number conversion
	if ((temperature & 0x800) == 0x800) :
		temperature=4096-temperature                 # fix for minus temperatures
		if (temperature > 0x258) :
			Domoticz.Log("Phase 3 - Bad temperature")
			return False        # temperature out of range ( > 60.0 degrees) 
		temperature=temperature | 0x8000             # turn highest bit on for minus values
	else :
		if (temperature > 0x258) :
			Domoticz.Log("Phase 4 - Bad temperature")
			return False        # temperature out of range ( > 60.0 degrees)
	if (humidity > 99) :
		Domoticz.Log("Phase 5 - Bad humidity")
		return False;                 # Humidity out of range
	#==================================================================================
	# Output
	# ----------------------------------
	#sprintf(pbuffer, "20;%02X;", PKSequenceNumber++);# Node and packet number 
	#Serial.print( pbuffer );
	# ----------------------------------
	if Parameters["Mode6"] != "0":
		Domoticz.Log("Alecto V4;")                   # Label
		Domoticz.Log("ID=%dx%dx;" % (rc, rc2))       # ID 
		Domoticz.Log("TEMP=%f;" % (temperature))     
		if (humidity < 99) :                             # Only report valid humidty values
			Domoticz.Log("HUM=%d;" % (humidity))      # decimal value..
	#==================================================================================
	#RawSignal.Repeats=true                          # suppress repeats of the same RF packet
	#RawSignal.Number=0;
	return True
