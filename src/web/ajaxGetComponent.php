<?php



include "./common.php";

header('cache-control: private');
header('Content-Type: application/json; charset=' . DEFAULT_CHARSET);

$component = parse_ini_file(CONFIG_PATH."/component.ini",true);
//print_r(parse_ini_file(CONFIG_PATH."/component.ini",true));


foreach ($component as $key => &$value) {
	# code...
	unset($value['ssh.password']);
	unset($value['ssh.username']);
	unset($value['svn.password']);
	unset($value['svn.username']);
}



echo json_encode($component);



?>