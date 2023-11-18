#!/usr/bin/python -u

import requests
import re
import hashlib
import os

import snmp_passpersist as snmp
import lxml.etree as etree

username='vodafone'
password='ADMIN_PASSWORD'
router_ip='192.168.1.1'
soap_login='<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><soapenv:Header><DMCookie>{dm_cookie}</DMCookie></soapenv:Header><soapenv:Body><cwmp:Login xmlns=""><ParameterList><Username>{username}</Username><Password>{password}</Password><AllowRelogin>0</AllowRelogin></ParameterList></cwmp:Login></soapenv:Body></soapenv:Envelope>'
soap_names='<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><soapenv:Header><DMCookie>{dm_cookie}</DMCookie><SessionNotRefresh>1</SessionNotRefresh></soapenv:Header><soapenv:Body><cwmp:GetParameterNames xmlns=""><ParameterPath>InternetGatewayDevice.X_JUNGO_COM_TR_181.Device.Hosts.Host.79.IPv6Address.</ParameterPath><NextLevel>1</NextLevel></cwmp:GetParameterNames></soapenv:Body></soapenv:Envelope>'
soap_params='<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><soapenv:Header><DMCookie>{dm_cookie}</DMCookie></soapenv:Header><soapenv:Body><cwmp:GetParameterValues xmlns=""><ParameterNames><string>InternetGatewayDevice.WANDevice.65.WANDSLInterfaceConfig.X_JUNGO_COM_DownstreamETRCurrRate</string><string>InternetGatewayDevice.WANDevice.65.WANDSLInterfaceConfig.DownstreamNoiseMargin</string><string>InternetGatewayDevice.WANDevice.65.WANDSLInterfaceConfig.DownstreamAttenuation</string><string>InternetGatewayDevice.WANDevice.65.WANDSLInterfaceConfig.Stats.Showtime.FECErrors</string><string>InternetGatewayDevice.WANDevice.65.WANDSLInterfaceConfig.Stats.Showtime.CRCErrors</string><string>InternetGatewayDevice.WANDevice.65.WANDSLInterfaceConfig.X_JUNGO_COM_UpstreamETRCurrRate</string><string>InternetGatewayDevice.WANDevice.65.WANDSLInterfaceConfig.UpstreamNoiseMargin</string><string>InternetGatewayDevice.WANDevice.65.WANDSLInterfaceConfig.UpstreamAttenuation</string><string>InternetGatewayDevice.WANDevice.65.WANDSLInterfaceConfig.Stats.Showtime.ATUCFECErrors</string><string>InternetGatewayDevice.WANDevice.65.WANDSLInterfaceConfig.Stats.Showtime.ATUCCRCErrors</string><string>InternetGatewayDevice.WANDevice.65.WANConnectionDevice.70.WANPPPConnection.72.ConnectionStatus</string></ParameterNames></cwmp:GetParameterValues></soapenv:Body></soapenv:Envelope>'

def update():
    page = requests.get("http://{router_ip}/main.cgi?page=login.html".format(router_ip=router_ip))
    wbm_cookie = page.cookies['wbm_cookie_session_id']
    dm_cookie_search = re.search(r"var dm_cookie='([A-Z0-9]+)'", page.text)
    if dm_cookie_search == None or dm_cookie_search.group(1) == None:
        print("ERROR: Invalid dm_cookie")
        exit
    dm_cookie = dm_cookie_search.group(1)

    page = requests.get("http://{router_ip}/main.cgi?js=rg_config.js".format(router_ip=router_ip), cookies={'wbm_cookie_session_id': wbm_cookie})
    auth_key_search = re.search(r"var auth_key = '([0-9]+)'", page.text)
    if auth_key_search == None:
        print("ERROR: Invalid auth_key")
        exit
    auth_key = auth_key_search.group(1)

    passwd_hash = hashlib.md5((password + auth_key).encode('utf-8')).hexdigest()
    login_headers = {'SOAPAction': 'cwmp:Login', 'Accept': 'application/xml, text/xml, */*; q=0.01', 'Content-Type': 'text/xml; charset=utf-8'}
    page = requests.post("http://{router_ip}/data_model.cgi".format(router_ip=router_ip), data=soap_login.format(dm_cookie=dm_cookie, username=username, password=passwd_hash), headers=login_headers, cookies={'wbm_cookie_session_id': wbm_cookie})

    page = requests.get("http://{router_ip}/main.cgi?page=app.html".format(router_ip=router_ip))
    wbm_cookie = page.cookies['wbm_cookie_session_id']
    dm_cookie_search = re.search(r"var dm_cookie='([A-Z0-9]+)'", page.text)
    if dm_cookie_search == None or dm_cookie_search.group(1) == None:
        print("ERROR: Invalid dm_cookie")
        exit
    dm_cookie = dm_cookie_search.group(1)

    params_headers = {'SOAPAction': 'cwmp:GetParameterValues', 'Accept': 'application/xml, text/xml, */*; q=0.01', 'Content-Type': 'text/xml; charset=utf-8'}
    page = requests.post("http://{router_ip}/data_model.cgi".format(router_ip=router_ip), data=soap_params.format(dm_cookie=dm_cookie), headers=params_headers, cookies={'wbm_cookie_session_id': wbm_cookie})

    soap_text = page.text
    soap_text = re.sub(r'<\?xml.*\?>', '', soap_text)

    parser = etree.XMLParser(recover=True)
    xmltree = etree.fromstring(soap_text, parser)

    pp.add_gau("1.1", xmltree.xpath("//Name[contains(text(), 'UpstreamETRCurrRate')]/following-sibling::Value/text()")[0])
    pp.add_gau("1.2", xmltree.xpath("//Name[contains(text(), 'DownstreamETRCurrRate')]/following-sibling::Value/text()")[0])
    pp.add_gau("1.3", 0)
    pp.add_gau("1.4", 0)
    pp.add_gau("1.5", xmltree.xpath("//Name[contains(text(), 'UpstreamNoiseMargin')]/following-sibling::Value/text()")[0])
    pp.add_gau("1.6", xmltree.xpath("//Name[contains(text(), 'DownstreamNoiseMargin')]/following-sibling::Value/text()")[0])
    pp.add_gau("1.7", 0)
    pp.add_gau("1.8", 0)
    pp.add_gau("1.9",  xmltree.xpath("//Name[contains(text(), 'UpstreamAttenuation')]/following-sibling::Value/text()")[0])
    pp.add_gau("1.10", xmltree.xpath("//Name[contains(text(), 'DownstreamAttenuation')]/following-sibling::Value/text()")[0])

pp = snmp.PassPersist('.1.3.9950.1.1')
pp.start(update, 300)
