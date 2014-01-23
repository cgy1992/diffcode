<?php

require "common.php";

#print_r(parse_ini_file(CONFIG_PATH."/component.ini",true));

print_r(json_decode('{\"leftType\":\"svn\",\"rightType\":\"ssh\",\"sessionName\":\"trade\",\"leftURI\":\"http://tc-svn.tencent.com/isd/isd_opencloud_rep/trade_proj/trunk/ars_dir\"}',true));



?>