<?php

require_once("common.php");

$file = $_GET['filepath'];



readfile(APP_PATH."/cmpfolder/".$file);



?>