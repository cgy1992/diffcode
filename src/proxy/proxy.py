#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
VERSION = '1.2.1'

目前还存在的bug
    * 偶现。代理机器scp 服务器到本地来，然后网络http返回，打开文件会有No such file or directory。是否可以使用ssh 公钥、私钥？yolang说弄一个flag文件
    * 偶现。broken pipe

20140107
    * 使用expect登录SSH的时候，增加exit命令，速度提升。取消timeout有些慢，ssh间歇性抽风
    

'''

import BaseHTTPServer
import subprocess
import urlparse,json,urllib


PROXY_PORT = 8899
PROXY_DOWNLOAD = "proxydownload"

class WebRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_POST(self):
        print "-------------------------------------start----------------------------------------"
        #print self.headers
        #print self.rfile.read(10)
        length = int(self.headers.getheader('content-length'))
        s = self.rfile.read(length)
        
        postvars =  dict(urlparse.parse_qsl(s))
        #print  urllib.unquote(s[len("paramjsonstring="):])
        #postvars = json.loads(urllib.unquote(s[len("paramjsonstring="):]))
        print "request" , s
        #postvars = json.loads(self.rfile.read(length))
        self.readyFile(**postvars)

        filename = postvars['filename']
        
        
        self.send_response(200)
        self.send_header("Content-Disposition", "attachment; filename=%s" % filename)
        self.end_headers()
        self.wfile.write(open("./proxydownload/%s" % filename ).read())
        self.wfile.close()
        
        ##clear local file
        #p =subprocess.Popen("rm ./download/%s" % filename , stdout=subprocess.PIPE, shell=True)
        #(output, err) = p.communicate()

        

    def do_GET(self):
        if self.path == '/download':      # 匹配 url ：/foo 的请求
            self.send_response(200)
            self.end_headers()
            self.wfile.write("please use get method")
            self.wfile.close()

        else:
            self.send_error(404) # 对于错误的请求，返回 404 错误

    def readyFile(self,filename,username,host,password,filepath,exclude):
        host,port = host.split(":")
      
        CMD_BASE = r"""
            expect -c "
            set timeout 1;
            spawn ssh {username}@{host} -p {port}  ;
            expect yes/no {{{{ send yes\r ; exp_continue }}}}   ;
            expect *assword* {{{{ send {password}\r }}}}  ;
            expect {username}@*   {{{{send \"{{cmd}}\r\" }}}}  ;
            expect {username}@*  {{{{ send exit\r }}}} ;
            expect eof
            "
        """.format(username=username,password=password,host=host,port=port)
        
        
        
        excludepath = ""
        for excludep in exclude.split(","):
            excludepath += " --exclude="+excludep
        
        tar = r""" cd {filepath};tar {excludepath} -cf /tmp/{filename} * """.format(excludepath=excludepath, filepath=filepath , filename= filename)
        cmd = CMD_BASE.format(cmd = tar)
        print "cmd = ",cmd
        p =subprocess.Popen(cmd , stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        #------------------------------------------------------------------------------
        
        SCP_CMD_BASE = r"""
            expect -c "
            set timeout 1;
            spawn scp -P {port} {username}@{host}:/tmp/{{filename}} ./proxydownload/  ;
            expect *assword* {{{{ send {password}\r }}}}  ;
            expect *\r
            expect \r
            expect eof
            "
        """.format(username=username,password=password,host=host,port=port)

        cmd = SCP_CMD_BASE.format(filename = filename)
        print "cmd=", cmd
        p  = subprocess.Popen( cmd , stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        #self.wfile.write(output)
        
        
        #### rm ssh  the tmp file
        CMD_BASE = r"""
            expect -c "
            set timeout 1;
            spawn ssh {username}@{host} -p {port}  ;
            expect *assword* {{{{ send {password}\r }}}}  ;
            expect {username}@*   {{{{ send \"{{cmd}}\r\" }}}}  ;
            expect {username}@*  {{{{ send exit\r }}}} ;
            expect eof
            "
        """.format(username=username,password=password,host=host,port=port)
        
        
        tar = r""" rm /tmp/{filename} """.format(filename= filename)
        cmd = CMD_BASE.format(cmd = tar)
        print "cmd = ",cmd
        p =subprocess.Popen(cmd , stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        print "clear ssh file /tmp/%s" % filename
        pass

try:
    server = BaseHTTPServer.HTTPServer(('0.0.0.0',PROXY_PORT), WebRequestHandler)    # 创建 HTTPSever 服务器，绑定地址：http://127.0.0.1:8080
    print('start server ')
    server.serve_forever()   # 启动 HTTPServer 服务器
except KeyboardInterrupt:
    print('^C received, shutting down server')
    server.socket.close()



