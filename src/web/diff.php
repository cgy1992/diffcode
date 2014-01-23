<?php


require_once("common.php");
define("PARAM_ROOT" , dirname(ROOT_PATH));



$content = $_POST;//file_get_contents("php://input" ,'r');

//print_r($_POST); //输出name=tom&amp;age=22

//$content = json_decode($content['paramjsonstring'],true);
$sessionName = $content['sessionName'];


$componentarr = parse_ini_file(CONFIG_PATH."/component.ini",true);

$component = $componentarr[$sessionName];

$svn = array(
	"uri" => "",
	"username" => $component['svn.username'],
	"password" => $component['svn.password'],
	);
$ssh = array(
	"uri" => $component['ssh.uri'],
	"username" => $component['ssh.username'],
	"password" => $component['ssh.password'],
	"host" => $component['ssh.host'],
	);


$leftType  = $content['leftType'];
$rightType = $content['rightType'];


$param = array();
$param["sessionName"] = $sessionName;
$param["leftType"] = $leftType;
$param["rightType"] = $rightType;
$param['ignore'] = $component['ignore'];

if($leftType == 'svn'){
	$param["left"] = 	array(
						"uri" => $content['leftURI'],
						"username" => $component['svn.username'],
						"password" => $component['svn.password'],
						);
}elseif($leftType == 'ssh'){
	$param['left'] = $ssh = array(
							"uri" => $component['ssh.uri'],
							"username" => $component['ssh.username'],
							"password" => $component['ssh.password'],
							"host" => $component['ssh.host'],
							"exclude" => $component['ssh.exclude'],
							);  
}


if($rightType == 'svn'){
	$param["right"] = 	array(
						"uri" => $content['rightURI'],
						"username" => $component['svn.username'],
						"password" => $component['svn.password'],
						);
}elseif($rightType == 'ssh'){
	$param['right'] = $ssh = array(
							"uri" => $component['ssh.uri'],
							"username" => $component['ssh.username'],
							"password" => $component['ssh.password'],
							"host" => $component['ssh.host'],
							"exclude" => $component['ssh.exclude'],
							);  
}

$sparam = json_encode($param);
//print $sparam;
$foldercmp = "cd .. ;./foldercmp.py '{$sparam}'";
#print $foldercmp;
$ret = array("date" => date("Y-m-d H:i:s",time()),
	//"cmd" =>$foldercmp
	);
exec($foldercmp, $res, $rc);
try {
	if (isset($res[0]) && $res[0] ) {
		//var_dump($res[0]);
		$a = json_decode($res[0],true);	
		//var_dump($a);
		if($a['retcode'] == 0){
			$ret['retcode'] = 0;
			$ret['cmdresult'] = $a;
		}else{
			$ret['retcode'] = 0 ;
			$ret['cmdresult'] = $a;
		}
		
	}else{
		$ret['retcode'] = -1;
		$ret['cmdresult'] = array();
		$ret['message'] = "没有获取到python对比脚本的返回值";
	}
	
} catch (Exception $e) {
	$ret['retcode'] = -1;
	$ret['cmdresult'] = array();
	$ret['message'] = "程序异常...".$e.getMessage() ;
}

#$a = system("cd .. ;./foldercmp1.py '{$sparam}'");
echo json_encode($ret);
#print 1
#exec($foldercmp, $res, $rc);
#print_r($res[0]);

?>

