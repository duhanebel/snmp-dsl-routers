#!/usr/bin/python -u
import requests
import re
import hashlib
import os

import snmp_passpersist as snmp
import lxml.etree as etree

username='Administrator'
password='ROUTER_PASSWORD'
router_ip='192.168.1.1'

def update():
    session = requests.Session()
    page = session.get("http://{router_ip}/login.lp".format(router_ip=router_ip))
    page = session.get("http://{router_ip}/login.lp?get_preauth=true".format(router_ip=router_ip))
    pre_auth=page.text.split("|")
    rn=pre_auth[0]
    realm=pre_auth[1]
    nonce=pre_auth[2]
    qop=pre_auth[3]

    ha="{user}:{realm}:{password}".format(user=username, realm=realm, password=password)
    ha2="GET:/login.lp"
    ha_sum=hashlib.md5(ha.encode('utf-8')).hexdigest()
    ha2_sum=hashlib.md5(ha2.encode('utf-8')).hexdigest()
    hidepw="{ha}:{nonce}:00000001:xyz:{qop}:{ha2}".format(ha=ha_sum, nonce=nonce, qop=qop, ha2=ha2_sum)
    hidepw_sum=hashlib.md5(hidepw.encode('utf-8')).hexdigest()

    login_data="rn={rn}&hidepw={hidepw}&user={user}".format(rn=rn, hidepw=hidepw_sum, user=username)

    page = session.post("http://{router_ip}/login.lp".format(router_ip=router_ip), data=login_data, headers={"Content-Type": "application/x-www-form-urlencoded"}, allow_redirects=False)

    page = session.get("http://{router_ip}/network-expert-dsl.lp".format(router_ip=router_ip), allow_redirects=False)

    html = page.text
    parser = etree.HTMLParser()
    xmltree = etree.fromstring(html, parser)

    pp.add_gau("1.1", xmltree.xpath("//dd[@id='cbr']/text()")[0].split()[0])
    pp.add_gau("1.2", xmltree.xpath("//dd[@id='cbr']/text()")[0].split()[3])
    pp.add_gau("1.3", xmltree.xpath("//dd[@id='mabr']/text()")[0].split()[0])
    pp.add_gau("1.4", xmltree.xpath("//dd[@id='mabr']/text()")[0].split()[3])
    pp.add_gau("1.5", xmltree.xpath("//dd[@id='nm']/text()")[0].split()[0])
    pp.add_gau("1.6", xmltree.xpath("//dd[@id='nm']/text()")[0].split()[3])
    pp.add_gau("1.7", xmltree.xpath("//dd[@id='ptl']/text()")[0].split()[0])
    pp.add_gau("1.8", xmltree.xpath("//dd[@id='ptl']/text()")[0].split()[3])
    pp.add_gau("1.9", xmltree.xpath("//dd[@id='la']/text()")[0].split()[0])
    pp.add_gau("1.10", xmltree.xpath("//dd[@id='la']/text()")[0].split()[3])

pp = snmp.PassPersist('.1.3.9950.1.1')
pp.start(update, 300)
