
# $Id$

use Apache::DBI;
use CGI; CGI->compile(':all');
use Socket;

$configfile = "/etc/soepkiptng.conf";
open F, $configfile or die "$configfile: $!\n";
while(<F>) {
	/^#/ and next;
	s/\s+$//;
	/./ or next;
	if(/^(\w+)\s*=\s*(.*?)\s*$/) {
		$f = $1;
		${$f} = $2;
	} elsif(/^\s+(.*?)\s*$/) {
		# continuation line
		${$f} .= "\n$1";
	} else {
		die "$configfile line $.: invalid format\n";
	}
}
close F;

Apache::DBI->connect_on_init("DBI:$db_type:$db_name:$db_host", $db_user, $db_pass);

